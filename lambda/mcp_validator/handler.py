"""
MCPValidator Lambda Function
Validates IAM access requests using direct database queries (MCP style).
"""

import json
import logging
import os
from typing import Any, Dict
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS clients
secrets_client = boto3.client('secretsmanager')


class MCPValidator:
    """Validates access using database queries."""
    
    def __init__(self):
        self.db_endpoint = os.getenv('DB_ENDPOINT')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'iamdb')
        self.db_user = os.getenv('DB_USER', 'iamadmin')
        self.db_password = self._get_db_password()
        self.conn = None
        self.queries_executed = []
    
    def _get_db_password(self) -> str:
        """Retrieve RDS password from Secrets Manager."""
        try:
            response = secrets_client.get_secret_value(
                SecretId=f"/askiam/{os.getenv('ENVIRONMENT')}/db/password"
            )
            secret = json.loads(response['SecretString'])
            return secret['password']
        except Exception as e:
            logger.error(f"Failed to retrieve DB password: {e}")
            raise
    
    def connect_to_db(self) -> None:
        """Connect to RDS Aurora."""
        try:
            self.conn = psycopg2.connect(
                host=self.db_endpoint,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=10,
                sslmode='prefer'
            )
            logger.info("Connected to RDS Aurora for validation")
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise
    
    def close_db(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def validate_access(self, user_id: int, app_id: int, role_id: int) -> Dict[str, Any]:
        """
        Validate IAM access using business logic queries.
        
        Checks:
        1. User exists and is active
        2. Application exists and is active
        3. Role exists and is active
        4. User doesn't already have the role
        5. User meets role prerequisites
        6. No conflicts or restrictions
        """
        self.connect_to_db()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # 1. Verify user is active
            cursor.execute(
                "SELECT user_id, status FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            if not user:
                return {
                    'is_valid': False,
                    'reason': f'User {user_id} not found',
                    'queries_executed': self.queries_executed
                }
            if user['status'] != 'active':
                return {
                    'is_valid': False,
                    'reason': f'User {user_id} is inactive',
                    'queries_executed': self.queries_executed
                }
            
            # 2. Verify application is active
            cursor.execute(
                "SELECT app_id, status FROM applications WHERE app_id = %s",
                (app_id,)
            )
            app = cursor.fetchone()
            if not app:
                return {
                    'is_valid': False,
                    'reason': f'Application {app_id} not found',
                    'queries_executed': self.queries_executed
                }
            if app['status'] != 'active':
                return {
                    'is_valid': False,
                    'reason': f'Application {app_id} is inactive',
                    'queries_executed': self.queries_executed
                }
            
            # 3. Verify role is active
            cursor.execute(
                "SELECT role_id, status FROM roles WHERE role_id = %s AND app_id = %s",
                (role_id, app_id)
            )
            role = cursor.fetchone()
            if not role:
                return {
                    'is_valid': False,
                    'reason': f'Role {role_id} not found in application {app_id}',
                    'queries_executed': self.queries_executed
                }
            if role['status'] != 'active':
                return {
                    'is_valid': False,
                    'reason': f'Role {role_id} is inactive',
                    'queries_executed': self.queries_executed
                }
            
            # 4. Check if user already has this role
            cursor.execute(
                "SELECT user_role_id FROM user_roles WHERE user_id = %s AND role_id = %s AND status = 'active'",
                (user_id, role_id)
            )
            existing_role = cursor.fetchone()
            if existing_role:
                return {
                    'is_valid': False,
                    'reason': f'User already has role {role_id}',
                    'queries_executed': self.queries_executed
                }
            
            # 5. Check prerequisites (if any)
            cursor.execute(
                "SELECT prerequisite_role_id FROM role_prerequisites WHERE role_id = %s",
                (role_id,)
            )
            prerequisites = cursor.fetchall()
            
            if prerequisites:
                for prereq in prerequisites:
                    cursor.execute(
                        "SELECT user_role_id FROM user_roles WHERE user_id = %s AND role_id = %s AND status = 'active'",
                        (user_id, prereq['prerequisite_role_id'])
                    )
                    if not cursor.fetchone():
                        return {
                            'is_valid': False,
                            'reason': f'User does not meet prerequisites for role {role_id}',
                            'queries_executed': self.queries_executed
                        }
            
            # 6. Check for any restrictions
            cursor.execute(
                "SELECT restriction_id FROM role_restrictions WHERE role_id = %s AND %s = ANY(restricted_user_ids)",
                (role_id, user_id)
            )
            restrictions = cursor.fetchone()
            if restrictions:
                return {
                    'is_valid': False,
                    'reason': f'User is restricted from accessing role {role_id}',
                    'queries_executed': self.queries_executed
                }
            
            cursor.close()
            return {
                'is_valid': True,
                'reason': f'User {user_id} can access role {role_id} in application {app_id}',
                'queries_executed': self.queries_executed
            }
        
        except Exception as e:
            logger.error(f"Validation query failed: {e}", exc_info=True)
            return {
                'is_valid': False,
                'reason': f'Database validation error: {str(e)}',
                'queries_executed': self.queries_executed
            }
        
        finally:
            self.close_db()


def lambda_handler(event, context):
    """
    Lambda handler for MCP-style validation.
    
    Args:
        event: {
            'user_id': int,
            'app_id': int,
            'role_id': int,
            'request_id': str,
            'context': {...}
        }
        
    Returns:
        {
            'is_valid': bool,
            'reason': str,
            'queries_executed': [...]
        }
    """
    validator = MCPValidator()
    
    try:
        user_id = event.get('user_id')
        app_id = event.get('app_id')
        role_id = event.get('role_id')
        
        if not all([user_id, app_id, role_id]):
            raise ValueError("Missing required parameters: user_id, app_id, role_id")
        
        logger.info(f"Validating access: user={user_id}, app={app_id}, role={role_id}")
        
        # Perform validation
        result = validator.validate_access(user_id, app_id, role_id)
        
        result['request_id'] = event.get('request_id')
        
        logger.info(f"MCP validation result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"MCP validation error: {e}", exc_info=True)
        return {
            'is_valid': False,
            'reason': f'Validation error: {str(e)}',
            'request_id': event.get('request_id'),
            'queries_executed': []
        }
