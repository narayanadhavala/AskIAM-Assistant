"""
Lex Fulfillment Handler Lambda Function for AskIAM Assistant
Receives slot values extracted by Lex and executes business logic
(entity validation, RAG query, access determination)
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')

# Environment Variables
CHAT_LOGS_TABLE = os.environ.get('CHAT_LOGS_TABLE', 'askiam-chat-logs')
REQUEST_STATE_TABLE = os.environ.get('REQUEST_STATE_TABLE', 'askiam-request-state')
OPENSEARCH_COLLECTION = os.environ.get('OPENSEARCH_COLLECTION', 'iam-collection')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
ENTITY_VALIDATOR_ARN = os.environ.get('ENTITY_VALIDATOR_ARN')
RAG_QUERY_ARN = os.environ.get('RAG_QUERY_ARN')


class LexFulfillmentHandler:
    """Handles Lex bot fulfillment for IAM access requests"""

    def __init__(self):
        self.chat_logs_table = dynamodb.Table(CHAT_LOGS_TABLE)
        self.request_state_table = dynamodb.Table(REQUEST_STATE_TABLE)
        self.db_credentials = self._get_db_credentials()

    def _get_db_credentials(self) -> Dict[str, str]:
        """Retrieve database credentials from Secrets Manager"""
        try:
            response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Error retrieving DB credentials: {str(e)}")
            return {}

    def handle_fulfillment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main handler for Lex fulfillment
        Event structure from Lex:
        {
            "sessionId": "...",
            "currentIntent": {
                "name": "IAMAccessRequest",
                "slots": {
                    "User": "john.smith",
                    "Application": "Salesforce",
                    "Role": "Admin"
                },
                "nluConfidence": {...}
            },
            "inputTranscript": "I need Admin access to Salesforce"
        }
        """
        try:
            session_id = event.get('sessionId')
            intent = event.get('currentIntent', {})
            slots = intent.get('slots', {})
            input_transcript = event.get('inputTranscript', '')

            logger.info(f"Lex Fulfillment Request - Session: {session_id}, Slots: {slots}")

            # Extract slot values with defaults
            user_name = slots.get('User')
            application_name = slots.get('Application')
            role_name = slots.get('Role')

            # Create request ID
            request_id = f"lex-{session_id}-{int(datetime.now().timestamp())}"

            # Log to DynamoDB
            self._log_request(
                request_id=request_id,
                user_name=user_name,
                application_name=application_name,
                role_name=role_name,
                input_transcript=input_transcript,
                session_id=session_id
            )

            # Validate extracted entities
            validation_result = self._validate_entities(
                user_name=user_name,
                application_name=application_name,
                role_name=role_name
            )

            if not validation_result.get('success'):
                return self._lex_close_response(
                    session_id=session_id,
                    dialog_state='Failed',
                    message=validation_result.get('message', 'Invalid request. Please try again.'),
                    request_id=request_id
                )

            # For valid requests, invoke Lex intent fulfillment
            # Get RAG-based answer about access policies
            rag_response = self._query_rag(
                user_name=user_name,
                application_name=application_name,
                role_name=role_name
            )

            # Determine if request is fulfillable
            access_decision = self._determine_access(
                user_name=user_name,
                application_name=application_name,
                role_name=role_name,
                validation_result=validation_result,
                rag_response=rag_response
            )

            # Save request state for future reference
            self._save_request_state(
                request_id=request_id,
                user_name=user_name,
                application_name=application_name,
                role_name=role_name,
                validation_result=validation_result,
                rag_response=rag_response,
                access_decision=access_decision
            )

            # Generate fulfillment message
            fulfillment_message = self._generate_fulfillment_message(
                user_name=user_name,
                application_name=application_name,
                role_name=role_name,
                access_decision=access_decision,
                request_id=request_id
            )

            return self._lex_close_response(
                session_id=session_id,
                dialog_state='Fulfilled',
                message=fulfillment_message,
                request_id=request_id
            )

        except Exception as e:
            logger.error(f"Error in fulfillment handler: {str(e)}", exc_info=True)
            return self._lex_close_response(
                session_id=event.get('sessionId'),
                dialog_state='Failed',
                message=f"An error occurred processing your request. Please try again.",
                request_id=None
            )

    def _validate_entities(self, user_name: Optional[str], 
                          application_name: Optional[str], 
                          role_name: Optional[str]) -> Dict[str, Any]:
        """
        Validate that extracted entities exist in the system
        Calls EntityValidator Lambda
        """
        try:
            # Check if all required entities are present
            if not all([user_name, application_name, role_name]):
                missing = []
                if not user_name:
                    missing.append("user")
                if not application_name:
                    missing.append("application")
                if not role_name:
                    missing.append("role")
                
                return {
                    'success': False,
                    'message': f"I couldn't identify all required information. Please provide: {', '.join(missing)}",
                    'missing_fields': missing
                }

            # Invoke EntityValidator Lambda
            payload = {
                'user_name': user_name,
                'application_name': application_name,
                'role_name': role_name
            }

            try:
                response = lambda_client.invoke(
                    FunctionName=ENTITY_VALIDATOR_ARN,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read().decode())
                return result
            except Exception as e:
                logger.error(f"Error validating entities: {str(e)}")
                return {
                    'success': False,
                    'message': "Could not validate your request. Please check the application, role, and user details."
                }

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                'success': False,
                'message': "An error occurred validating your request."
            }

    def _query_rag(self, user_name: str, application_name: str, role_name: str) -> Dict[str, Any]:
        """
        Query RAG system for access policies and compliance information
        Uses Bedrock for embeddings and OpenSearch for retrieval
        """
        try:
            query = f"What are the access policies and requirements for {role_name} role in {application_name} application?"
            
            # Invoke RAG Query Lambda
            payload = {
                'query': query,
                'user_name': user_name,
                'application_name': application_name,
                'role_name': role_name
            }

            try:
                response = lambda_client.invoke(
                    FunctionName=RAG_QUERY_ARN,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read().decode())
                return result
            except Exception as e:
                logger.error(f"Error querying RAG: {str(e)}")
                return {
                    'success': False,
                    'error': 'RAG query failed',
                    'documents': [],
                    'answer': 'Could not retrieve policy information.'
                }

        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _determine_access(self, user_name: str, application_name: str, role_name: str,
                         validation_result: Dict[str, Any], 
                         rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if access should be granted based on validation and policies
        """
        # Check if entities are valid
        if not validation_result.get('is_valid_user'):
            return {
                'decision': 'DENIED',
                'reason': f"User '{user_name}' not found in the system"
            }
        
        if not validation_result.get('is_valid_application'):
            return {
                'decision': 'DENIED',
                'reason': f"Application '{application_name}' not found in the system"
            }
        
        if not validation_result.get('is_valid_role'):
            return {
                'decision': 'DENIED',
                'reason': f"Role '{role_name}' not found in the system"
            }

        # Check if user already has role
        if validation_result.get('user_has_role'):
            return {
                'decision': 'ALREADY_HAS',
                'reason': f"User '{user_name}' already has '{role_name}' role in '{application_name}'"
            }

        # If all validations pass, check if request should be auto-approved
        # (based on policy/hierarchy/rules from RAG)
        if rag_response.get('success'):
            answer = rag_response.get('answer', '')
            # Simple heuristic: if policy mentions "auto-approve" or "standard role"
            if 'auto-approve' in answer.lower() or 'standard' in answer.lower():
                return {
                    'decision': 'APPROVED',
                    'reason': 'Request meets auto-approval criteria',
                    'requires_approval': False
                }

        # Default: request requires manual approval
        return {
            'decision': 'PENDING',
            'reason': 'Request requires manager approval',
            'requires_approval': True
        }

    def _generate_fulfillment_message(self, user_name: str, application_name: str,
                                      role_name: str, access_decision: Dict[str, Any],
                                      request_id: str) -> str:
        """Generate human-readable fulfillment message from bot"""
        decision = access_decision.get('decision', 'UNKNOWN')
        reason = access_decision.get('reason', '')

        messages = {
            'APPROVED': f"Great! I've processed your request for {role_name} access in {application_name}. Your access has been approved. (Request ID: {request_id})",
            'DENIED': f"I couldn't process your request: {reason}. (Request ID: {request_id})",
            'ALREADY_HAS': f"You already have {role_name} access in {application_name}. No additional access needed.",
            'PENDING': f"Your request for {role_name} access in {application_name} has been submitted for approval. You'll be notified once it's processed. (Request ID: {request_id})"
        }

        return messages.get(decision, f"Your request is being processed. (Request ID: {request_id})")

    def _log_request(self, request_id: str, user_name: Optional[str],
                    application_name: Optional[str], role_name: Optional[str],
                    input_transcript: str, session_id: str) -> None:
        """Log request to DynamoDB"""
        try:
            timestamp = int(datetime.now().timestamp())
            ttl = timestamp + (90 * 24 * 60 * 60)  # 90 days TTL

            self.chat_logs_table.put_item(
                Item={
                    'request_id': request_id,
                    'timestamp': timestamp,
                    'session_id': session_id,
                    'user_name': user_name or 'unknown',
                    'application_name': application_name or 'unknown',
                    'role_name': role_name or 'unknown',
                    'input_transcript': input_transcript,
                    'source': 'lex',
                    'expiration_time': ttl
                }
            )
            logger.info(f"Request logged: {request_id}")
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")

    def _save_request_state(self, request_id: str, user_name: str,
                           application_name: str, role_name: str,
                           validation_result: Dict[str, Any],
                           rag_response: Dict[str, Any],
                           access_decision: Dict[str, Any]) -> None:
        """Save request state to DynamoDB for future reference"""
        try:
            timestamp = int(datetime.now().timestamp())
            ttl = timestamp + (30 * 24 * 60 * 60)  # 30 days TTL

            self.request_state_table.put_item(
                Item={
                    'request_id': request_id,
                    'user_name': user_name,
                    'application_name': application_name,
                    'role_name': role_name,
                    'timestamp': timestamp,
                    'validation_result': json.dumps(validation_result),
                    'rag_response': json.dumps(rag_response),
                    'access_decision': json.dumps(access_decision),
                    'expiration_time': ttl
                }
            )
            logger.info(f"Request state saved: {request_id}")
        except Exception as e:
            logger.error(f"Error saving request state: {str(e)}")

    @staticmethod
    def _lex_close_response(session_id: str, dialog_state: str,
                           message: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Format response for Lex bot"""
        return {
            'sessionAttributes': {
                'request_id': request_id or 'unknown',
                'dialog_state': dialog_state
            },
            'dialogAction': {
                'type': 'Close',
                'fulfillmentState': 'Fulfilled' if dialog_state == 'Fulfilled' else 'Failed',
                'message': {
                    'contentType': 'PlainText',
                    'content': message
                }
            }
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Receives events from Lex and processes them
    """
    logger.info(f"Incoming event: {json.dumps(event)}")

    handler = LexFulfillmentHandler()
    response = handler.handle_fulfillment(event)

    logger.info(f"Response: {json.dumps(response)}")
    return response
