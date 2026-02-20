"""
Entity Validator Lambda Function Handler
Validates specific entities (users, roles, applications) in the database
"""

import json
import boto3
import os
import psycopg2
from datetime import datetime

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')

# AWS clients
secrets_manager = boto3.client('secretsmanager')

def get_db_credentials():
    """Retrieve database credentials from Secrets Manager"""
    try:
        secret = secrets_manager.get_secret_value(SecretId=DB_SECRET_ARN)
        return json.loads(secret['SecretString'])
    except Exception as e:
        print(f"Error retrieving credentials: {str(e)}")
        raise

def get_db_connection(creds):
    """Create PostgreSQL database connection"""
    try:
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

def validate_user(user_id, db_conn):
    """Validate that a user exists"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT user_id, user_name, email, status 
            FROM users 
            WHERE user_id = %s
            """,
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'valid': True,
                'entity_type': 'user',
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'status': result[3]
            }
        else:
            return {
                'valid': False,
                'entity_type': 'user',
                'error': f'User {user_id} not found'
            }
    except Exception as e:
        return {
            'valid': False,
            'entity_type': 'user',
            'error': f'Database error: {str(e)}'
        }

def validate_role(role_id, db_conn):
    """Validate that a role exists"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT role_id, role_name, description, status 
            FROM roles 
            WHERE role_id = %s
            """,
            (role_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'valid': True,
                'entity_type': 'role',
                'id': result[0],
                'name': result[1],
                'description': result[2],
                'status': result[3]
            }
        else:
            return {
                'valid': False,
                'entity_type': 'role',
                'error': f'Role {role_id} not found'
            }
    except Exception as e:
        return {
            'valid': False,
            'entity_type': 'role',
            'error': f'Database error: {str(e)}'
        }

def validate_application(app_id, db_conn):
    """Validate that an application exists"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT app_id, app_name, description, status 
            FROM applications 
            WHERE app_id = %s
            """,
            (app_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'valid': True,
                'entity_type': 'application',
                'id': result[0],
                'name': result[1],
                'description': result[2],
                'status': result[3]
            }
        else:
            return {
                'valid': False,
                'entity_type': 'application',
                'error': f'Application {app_id} not found'
            }
    except Exception as e:
        return {
            'valid': False,
            'entity_type': 'application',
            'error': f'Database error: {str(e)}'
        }

def handler(event, context):
    """
    Entity validation handler
    
    Expected event structure:
    {
        "entity_type": "user|role|application",
        "entity_id": "identifier",
        "validate_access": true  # Optional: check user-role assignment
    }
    """
    
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        entity_type = body.get('entity_type', '').lower()
        entity_id = body.get('entity_id', '')
        validate_access = body.get('validate_access', False)
        
        if not entity_type or not entity_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: entity_type, entity_id'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Get database credentials and connection
        creds = get_db_credentials()
        db_conn = get_db_connection(creds)
        
        # Route to appropriate validation function
        if entity_type == 'user':
            result = validate_user(entity_id, db_conn)
        elif entity_type == 'role':
            result = validate_role(entity_id, db_conn)
        elif entity_type == 'application':
            result = validate_application(entity_id, db_conn)
        else:
            db_conn.close()
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Invalid entity_type: {entity_type}. Must be user, role, or application'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Additional validation: check if user has role (if applicable)
        if validate_access and entity_type == 'user' and result['valid']:
            user_id = result['id']
            cursor = db_conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM user_roles 
                WHERE user_id = %s
                """,
                (user_id,)
            )
            role_count = cursor.fetchone()[0]
            result['assigned_roles_count'] = role_count
            
            # Get a sample of assigned roles
            cursor.execute(
                """
                SELECT r.role_id, r.role_name, a.app_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.role_id
                LEFT JOIN applications a ON ur.app_id = a.app_id
                WHERE ur.user_id = %s
                LIMIT 5
                """,
                (user_id,)
            )
            roles = cursor.fetchall()
            result['sample_roles'] = [
                {'role_id': r[0], 'role_name': r[1], 'application': r[2]}
                for r in roles
            ]
            cursor.close()
        
        db_conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'validation': result,
                'timestamp': datetime.utcnow().isoformat(),
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(f"Error in validation handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Validation failed',
                'message': str(e),
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
