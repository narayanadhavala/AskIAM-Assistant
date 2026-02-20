"""
Lex Fulfillment Lambda Function Handler
Processes Lex intent fulfillment and routes to appropriate Lambda functions
"""

import json
import boto3
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

# Environment variables
REQUEST_PROCESSOR_ARN = os.environ.get('REQUEST_PROCESSOR_ARN')
ENTITY_VALIDATOR_ARN = os.environ.get('ENTITY_VALIDATOR_ARN')
RAG_QUERY_ARN = os.environ.get('RAG_QUERY_ARN')
CHAT_LOGS_TABLE = os.environ.get('CHAT_LOGS_TABLE')

def log_to_dynamodb(session_id, message, response=None, intent_name=None):
    """Log interaction to DynamoDB"""
    try:
        table = dynamodb.Table(CHAT_LOGS_TABLE)
        table.put_item(
            Item={
                'request_id': session_id,
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                'message': message,
                'response': response or '',
                'intent': intent_name or '',
                'created_at': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error logging to DynamoDB: {str(e)}")

def invoke_lambda(function_arn, payload):
    """Invoke another Lambda function and return result"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        logger.info(f"Lambda invocation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error invoking Lambda: {str(e)}")
        return {'error': f'Failed to invoke function: {str(e)}'}

def handle_access_request_intent(intent_name, slots, session_id):
    """Handle AccessRequestIntent - process IAM access requests"""
    try:
        logger.info(f"Handling AccessRequestIntent with slots: {slots}")
        
        # Extract slot values
        role = slots.get('Role', {}).get('value', {}).get('interpretedValue', '')
        application = slots.get('Application', {}).get('value', {}).get('interpretedValue', '')
        
        message = f"I need access to {role} role"
        if application:
            message += f" in {application}"
        
        # Invoke request processor
        payload = {
            'body': json.dumps({
                'message': message,
                'sessionId': session_id
            })
        }
        
        result = invoke_lambda(REQUEST_PROCESSOR_ARN, payload)
        
        # Extract response
        if 'body' in result:
            body = json.loads(result['body'])
            response_text = str(body.get('validation', {}).get('reason', 'Request processed'))
        else:
            response_text = 'Request processed successfully'
        
        log_to_dynamodb(session_id, message, response_text, intent_name)
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error handling AccessRequestIntent: {str(e)}")
        return f"Error processing your request: {str(e)}"

def handle_validate_entity_intent(intent_name, slots, session_id):
    """Handle ValidateEntityIntent - validate entities"""
    try:
        logger.info(f"Handling ValidateEntityIntent with slots: {slots}")
        
        # Extract slot values
        entity_name = slots.get('EntityName', {}).get('value', {}).get('interpretedValue', '')
        
        if not entity_name:
            return "Please provide an entity name to validate (user, role, or application)"
        
        # Invoke entity validator
        payload = {
            'body': json.dumps({
                'entity_type': 'user',  # Default, could be enhanced to detect type
                'entity_id': entity_name
            })
        }
        
        result = invoke_lambda(ENTITY_VALIDATOR_ARN, payload)
        
        # Extract response
        if 'body' in result:
            body = json.loads(result['body'])
            validation = body.get('validation', {})
            if validation.get('valid'):
                response_text = f"✓ {entity_name} is valid. Details: {validation.get('name', 'N/A')}"
            else:
                response_text = f"✗ {entity_name} is not valid. {validation.get('error', '')}"
        else:
            response_text = 'Entity validation could not be completed'
        
        log_to_dynamodb(session_id, f"Validate {entity_name}", response_text, intent_name)
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error handling ValidateEntityIntent: {str(e)}")
        return f"Error validating entity: {str(e)}"

def build_lex_response(response_text, session_attributes=None):
    """Build standard Lex fulfillment response"""
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'state': 'Fulfilled'
            },
            'sessionAttributes': session_attributes or {}
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': response_text
            }
        ]
    }

def handler(event, context):
    """
    Lex V2 Fulfillment Handler
    
    Event structure from Lex:
    {
        'currentIntent': {
            'name': 'AccessRequestIntent',
            'state': 'Fulfilled'
        },
        'inputTranscript': 'I need access to HR Analyst role',
        'sessionState': {
            'sessionAttributes': {}
        },
        'slots': {...}
    }
    """
    
    try:
        logger.info(f"Received Lex event: {json.dumps(event)}")
        
        # Extract Lex information
        intent_name = event.get('sessionState', {}).get('intent', {}).get('name', '')
        slots = event.get('sessionState', {}).get('intent', {}).get('slots', {})
        session_id = event.get('sessionId', 'unknown')
        input_transcript = event.get('inputTranscript', '')
        session_attributes = event.get('sessionState', {}).get('sessionAttributes', {})
        
        logger.info(f"Processing intent: {intent_name}, Session: {session_id}")
        
        # Route to appropriate handler based on intent
        if intent_name == 'AccessRequestIntent':
            response_text = handle_access_request_intent(intent_name, slots, session_id)
        elif intent_name == 'ValidateEntityIntent':
            response_text = handle_validate_entity_intent(intent_name, slots, session_id)
        elif intent_name == 'AMAZON.HelpIntent':
            response_text = (
                "I can help you with IAM access requests. You can:\n"
                "1. Request access to a role: 'I need access to HR Analyst role'\n"
                "2. Validate an entity: 'Validate John Smith'\n"
                "3. Check if you have access: 'Do I have access to Salesforce?'"
            )
        else:
            response_text = f"I didn't understand your request. Please try again or ask for help."
        
        logger.info(f"Generated response: {response_text}")
        
        # Return Lex response
        lex_response = build_lex_response(response_text, session_attributes)
        logger.info(f"Returning Lex response: {json.dumps(lex_response)}")
        
        return lex_response
        
    except Exception as e:
        logger.error(f"Error in Lex fulfillment handler: {str(e)}", exc_info=True)
        return build_lex_response(f"An error occurred: {str(e)}")
