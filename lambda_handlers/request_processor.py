"""
Request Processor Lambda Function Handler
Handles incoming IAM access requests and coordinates processing
"""

import json
import boto3
import os
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
CHAT_LOGS_TABLE = os.environ.get('CHAT_LOGS_TABLE')
OPENSEARCH_COLLECTION = os.environ.get('OPENSEARCH_COLLECTION')

# AWS clients
secrets_manager = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
aoss = boto3.client('opensearchserverless')

def get_db_connection():
    """Get PostgreSQL database connection from Secrets Manager"""
    try:
        secret = secrets_manager.get_secret_value(SecretId=DB_SECRET_ARN)
        creds = json.loads(secret['SecretString'])
        
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['username'],
            password=creds['password'],
            database=creds['dbname']
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        raise

def log_to_dynamodb(request_id, timestamp, message, response=None, status='PROCESSING'):
    """Log chat interactions to DynamoDB"""
    try:
        table = dynamodb.Table(CHAT_LOGS_TABLE)
        table.put_item(
            Item={
                'request_id': request_id,
                'timestamp': timestamp,
                'message': message,
                'response': response or '',
                'status': status,
                'created_at': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")

def extract_entities(message, db_conn):
    """Extract user, role, and application from request message"""
    try:
        cursor = db_conn.cursor()
        
        # Simple extraction logic - enhance based on your NLP model
        entities = {
            'user': None,
            'role': None,
            'application': None
        }
        
        # Query users
        cursor.execute("SELECT user_id, user_name FROM users LIMIT 100")
        users = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        # Query roles
        cursor.execute("SELECT role_id, role_name FROM roles LIMIT 100")
        roles = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        # Query applications
        cursor.execute("SELECT app_id, app_name FROM applications LIMIT 100")
        apps = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        # Simple matching logic
        message_lower = message.lower()
        
        for user_name, user_id in users.items():
            if user_name in message_lower:
                entities['user'] = {'id': user_id, 'name': user_name}
                break
        
        for role_name, role_id in roles.items():
            if role_name in message_lower:
                entities['role'] = {'id': role_id, 'name': role_name}
                break
        
        for app_name, app_id in apps.items():
            if app_name in message_lower:
                entities['application'] = {'id': app_id, 'name': app_name}
                break
        
        cursor.close()
        return entities
        
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")
        return None

def validate_request(entities, db_conn):
    """Validate the access request based on extracted entities"""
    try:
        if not entities or not all([entities.get('user'), entities.get('role')]):
            return {
                'valid': False,
                'reason': 'Missing required entities (user, role)',
                'details': {}
            }
        
        cursor = db_conn.cursor()
        
        # Check if user exists
        cursor.execute(
            "SELECT * FROM users WHERE user_id = %s",
            (entities['user']['id'],)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            return {
                'valid': False,
                'reason': 'User not found',
                'details': {'user': entities['user']}
            }
        
        # Check if role exists
        cursor.execute(
            "SELECT * FROM roles WHERE role_id = %s",
            (entities['role']['id'],)
        )
        role = cursor.fetchone()
        
        if not role:
            cursor.close()
            return {
                'valid': False,
                'reason': 'Role not found',
                'details': {'role': entities['role']}
            }
        
        # Check if user already has role
        if entities.get('application'):
            cursor.execute(
                """
                SELECT * FROM user_roles 
                WHERE user_id = %s AND role_id = %s AND app_id = %s
                """,
                (entities['user']['id'], entities['role']['id'], 
                 entities['application']['id'])
            )
        else:
            cursor.execute(
                """
                SELECT * FROM user_roles 
                WHERE user_id = %s AND role_id = %s
                """,
                (entities['user']['id'], entities['role']['id'])
            )
        
        existing = cursor.fetchone()
        cursor.close()
        
        if existing:
            return {
                'valid': False,
                'reason': 'User already has this role',
                'details': {'user': entities['user'], 'role': entities['role']}
            }
        
        return {
            'valid': True,
            'reason': 'Request is valid and can be approved',
            'details': {
                'user': user,
                'role': role,
                'application': entities.get('application')
            }
        }
        
    except Exception as e:
        print(f"Error validating request: {str(e)}")
        return {
            'valid': False,
            'reason': f'Validation error: {str(e)}',
            'details': {}
        }

def handler(event, context):
    """
    Main Lambda handler for request processing
    
    Expected event structure:
    {
        "message": "I need access to HR Analyst role in Workday",
        "sessionId": "session-123",
        "userId": "user-456"
    }
    """
    
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        message = body.get('message', '')
        session_id = body.get('sessionId', 'unknown')
        request_id = context.request_id
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        
        print(f"Processing request {request_id}: {message}")
        
        # Log initial request
        log_to_dynamodb(request_id, timestamp, message, status='RECEIVED')
        
        # Get database connection
        db_conn = get_db_connection()
        
        # Extract entities from message
        entities = extract_entities(message, db_conn)
        print(f"Extracted entities: {entities}")
        
        # Validate request
        validation_result = validate_request(entities, db_conn)
        print(f"Validation result: {validation_result}")
        
        # Log result
        response_text = json.dumps(validation_result)
        log_to_dynamodb(
            request_id, 
            timestamp, 
            message, 
            response_text,
            status='VALIDATION_COMPLETE'
        )
        
        # Close connection
        db_conn.close()
        
        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'requestId': request_id,
                'sessionId': session_id,
                'message': message,
                'entities': entities,
                'validation': validation_result,
                'timestamp': timestamp
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        error_response = {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Request processing failed',
                'message': str(e),
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
        # Log error
        log_to_dynamodb(
            context.request_id,
            int(datetime.utcnow().timestamp() * 1000),
            body.get('message', ''),
            str(e),
            status='ERROR'
        )
        
        return error_response
