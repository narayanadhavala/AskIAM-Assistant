"""
RequestOrchestrator Lambda Function
Coordinates the IAM access validation workflow.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict
import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS clients
lambda_client = boto3.client('lambda')
ssm_client = boto3.client('ssm')
cloudwatch = boto3.client('cloudwatch')
xray_recorder = None

try:
    from aws_xray_sdk.core import xray_recorder
    from aws_xray_sdk.core import patch_all
    patch_all()
except ImportError:
    logger.warning("X-Ray SDK not available")


class RequestOrchestrator:
    """Orchestrates IAM validation workflow."""
    
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        self.rag_threshold = self._load_rag_threshold()
        
    def _load_rag_threshold(self) -> float:
        """Load RAG confidence threshold from Parameter Store."""
        try:
            response = ssm_client.get_parameter(
                Name=f"/askiam/{os.getenv('ENVIRONMENT')}/app/rag-threshold"
            )
            return float(response['Parameter']['Value'])
        except Exception as e:
            logger.warning(f"Failed to load RAG threshold: {e}, using default 0.95")
            return 0.95
    
    def parse_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming request from API Gateway or Lex.
        
        Args:
            event: Lambda event from API Gateway or Lex
            
        Returns:
            Standardized request object
        """
        # Handle API Gateway events
        if 'body' in event:
            body = json.loads(event.get('body', '{}'))
        else:
            body = event
        
        # Extract raw request
        raw_request = body.get('text') or body.get('message') or body.get('raw_request')
        if not raw_request:
            raise ValueError("Missing 'text', 'message', or 'raw_request' field")
        
        # Extract context
        request_context = {
            'ip_address': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('requestContext', {}).get('identity', {}).get('userAgent', 'unknown'),
            'session_id': body.get('session_id', self.request_id),
            'timestamp': self.start_time.isoformat()
        }
        
        return {
            'request_id': self.request_id,
            'raw_request': raw_request,
            'user_id': body.get('user_id'),
            'context': request_context,
            'source': 'api' if 'body' in event else 'lex'
        }
    
    def log_request(self, parsed_request: Dict[str, Any]) -> None:
        """Log request to CloudWatch."""
        logger.info(json.dumps({
            'level': 'INFO',
            'message': 'Access validation request received',
            'request_id': parsed_request['request_id'],
            'user_id': parsed_request.get('user_id'),
            'raw_request': parsed_request['raw_request'][:100],  # Truncate for logs
            'context': parsed_request['context']
        }))
    
    async def invoke_lambda_async(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Lambda function asynchronously."""
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            return json.loads(response['Payload'].read().decode())
        except Exception as e:
            logger.error(f"Failed to invoke {function_name}: {e}")
            return {'error': str(e), 'function': function_name}
    
    def invoke_entity_extractor(self, parsed_request: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke EntityExtractor Lambda."""
        payload = {
            'request_id': parsed_request['request_id'],
            'raw_request': parsed_request['raw_request'],
            'user_id': parsed_request.get('user_id')
        }
        
        try:
            response = lambda_client.invoke(
                FunctionName=f"ask-iam-entity-extractor-{os.getenv('ENVIRONMENT')}",
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            result = json.loads(response['Payload'].read().decode())
            logger.info(f"Entity extraction result: {result}")
            return result
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {'error': str(e), 'entities': {}}
    
    def decide_validation_path(self, entity_result: Dict[str, Any]) -> str:
        """
        Decide whether to use RAG-first or MCP-first validation.
        
        Returns:
            'parallel': Run both RAG and MCP in parallel
            'rag_only': Trust RAG if high confidence expected
            'mcp_only': Skip RAG, go straight to MCP
        """
        # For now, always run both in parallel for maximum accuracy
        return 'parallel'
    
    def invoke_validations_parallel(self, entity_result: Dict[str, Any], parsed_request: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke RAG and MCP validators in parallel."""
        validation_payloads = {
            'user_id': entity_result.get('user_id'),
            'app_id': entity_result.get('app_id'),
            'role_id': entity_result.get('role_id'),
            'request_id': parsed_request['request_id'],
            'raw_request': parsed_request['raw_request'],
            'context': parsed_request['context']
        }
        
        try:
            # Invoke both in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as executor:
                rag_future = executor.submit(
                    lambda_client.invoke,
                    FunctionName=f"ask-iam-rag-validator-{os.getenv('ENVIRONMENT')}",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(validation_payloads)
                )
                mcp_future = executor.submit(
                    lambda_client.invoke,
                    FunctionName=f"ask-iam-mcp-validator-{os.getenv('ENVIRONMENT')}",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(validation_payloads)
                )
                
                rag_response = json.loads(rag_future.result()['Payload'].read().decode())
                mcp_response = json.loads(mcp_future.result()['Payload'].read().decode())
                
                return {
                    'rag_result': rag_response,
                    'mcp_result': mcp_response
                }
        except Exception as e:
            logger.error(f"Parallel validation failed: {e}")
            return {'error': str(e), 'rag_result': {}, 'mcp_result': {}}
    
    def decide_final_result(self, entity_result: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide final validation result based on RAG and MCP outputs.
        
        Decision logic:
        1. If RAG confidence > threshold AND MCP passed: VALID
        2. If RAG confidence > threshold: VALID (trust RAG)
        3. If MCP passed: VALID
        4. Otherwise: INVALID
        """
        rag_result = validation_results.get('rag_result', {})
        mcp_result = validation_results.get('mcp_result', {})
        
        rag_confidence = rag_result.get('confidence', 0)
        rag_valid = rag_result.get('is_valid', False)
        mcp_valid = mcp_result.get('is_valid', False)
        
        if rag_confidence >= self.rag_threshold:
            return {
                'is_valid': True,
                'reason': f'RAG validation passed (confidence: {rag_confidence:.2f})',
                'method': 'rag',
                'details': {
                    'rag_confidence': rag_confidence,
                    'mcp_valid': mcp_valid,
                    'documents': rag_result.get('documents', [])
                }
            }
        elif mcp_valid:
            return {
                'is_valid': True,
                'reason': 'MCP database validation passed',
                'method': 'mcp',
                'details': {
                    'rag_confidence': rag_confidence,
                    'mcp_reason': mcp_result.get('reason', ''),
                    'queries': mcp_result.get('queries_executed', [])
                }
            }
        else:
            reason = mcp_result.get('reason') or rag_result.get('reason') or 'Validation failed'
            return {
                'is_valid': False,
                'reason': reason,
                'method': 'hybrid',
                'details': {
                    'rag_confidence': rag_confidence,
                    'mcp_valid': mcp_valid,
                    'error': validation_results.get('error')
                }
            }
    
    def invoke_audit_logger(self, parsed_request: Dict[str, Any], entity_result: Dict[str, Any], 
                           final_result: Dict[str, Any]) -> None:
        """Invoke audit logger asynchronously."""
        payload = {
            'request_id': parsed_request['request_id'],
            'user_id': entity_result.get('user_id') or parsed_request.get('user_id'),
            'validation_result': final_result['is_valid'],
            'validation_method': final_result.get('method'),
            'reason': final_result.get('reason'),
            'context': parsed_request['context'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            lambda_client.invoke(
                FunctionName=f"ask-iam-audit-logger-{os.getenv('ENVIRONMENT')}",
                InvocationType='Event',  # Async
                Payload=json.dumps(payload)
            )
        except Exception as e:
            logger.error(f"Failed to invoke audit logger: {e}")
    
    def emit_metrics(self, final_result: Dict[str, Any]) -> None:
        """Emit custom metrics to CloudWatch."""
        try:
            cloudwatch.put_metric_data(
                Namespace='AskIAM',
                MetricData=[
                    {
                        'MetricName': 'AccessRequestCount',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'Status', 'Value': 'VALID' if final_result['is_valid'] else 'INVALID'},
                            {'Name': 'Method', 'Value': final_result.get('method', 'unknown')}
                        ]
                    },
                    {
                        'MetricName': 'ValidationLatency',
                        'Value': (datetime.utcnow() - self.start_time).total_seconds() * 1000,
                        'Unit': 'Milliseconds'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to emit metrics: {e}")
    
    def build_response(self, parsed_request: Dict[str, Any], final_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build response for API Gateway or Lex."""
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        response = {
            'status': 'VALID' if final_result['is_valid'] else 'INVALID',
            'reason': final_result['reason'],
            'request_id': parsed_request['request_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': duration_ms,
            'details': final_result.get('details', {})
        }
        
        return response


def lambda_handler(event, context):
    """
    Main Lambda handler for RequestOrchestrator.
    
    Args:
        event: API Gateway or Lex event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    orchestrator = RequestOrchestrator()
    
    try:
        # 1. Parse request
        parsed_request = orchestrator.parse_request(event)
        orchestrator.log_request(parsed_request)
        
        # 2. Extract entities
        entity_result = orchestrator.invoke_entity_extractor(parsed_request)
        if entity_result.get('error'):
            raise ValueError(f"Entity extraction failed: {entity_result['error']}")
        
        # 3. Decide validation path
        validation_path = orchestrator.decide_validation_path(entity_result)
        
        # 4. Run validations (parallel)
        validation_results = orchestrator.invoke_validations_parallel(entity_result, parsed_request)
        
        # 5. Decide final result
        final_result = orchestrator.decide_final_result(entity_result, validation_results)
        
        # 6. Emit audit log (async)
        orchestrator.invoke_audit_logger(parsed_request, entity_result, final_result)
        
        # 7. Emit metrics
        orchestrator.emit_metrics(final_result)
        
        # 8. Build response
        response = orchestrator.build_response(parsed_request, final_result)
        
        # Format for API Gateway
        return {
            'statusCode': 200,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': parsed_request['request_id']
            }
        }
    
    except Exception as e:
        logger.error(f"Request orchestration failed: {e}", exc_info=True)
        error_response = {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'ERROR',
                'reason': str(e),
                'request_id': orchestrator.request_id
            }),
            'headers': {'Content-Type': 'application/json'}
        }
        return error_response
