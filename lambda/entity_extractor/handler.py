"""
EntityExtractor Lambda Function
Extracts user, application, and role entities from natural language requests.
"""

import json
import logging
import os
import re
from typing import Any, Dict, Tuple
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS clients
rds_client = boto3.client('rds')
ssm_client = boto3.client('ssm')
secrets_client = boto3.client('secretsmanager')


class EntityExtractor:
    """Extracts entities from IAM access requests."""
    
    def __init__(self):
        self.db_endpoint = os.getenv('DB_ENDPOINT')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'iamdb')
        self.db_user = os.getenv('DB_USER', 'iamadmin')
        self.db_password = self._get_db_password()
        self.conn = None
    
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
            logger.info("Connected to RDS Aurora")
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise
    
    def close_db(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def extract_entities(self, raw_request: str) -> Dict[str, str]:
        """
        Extract user, application, and role from natural language.
        
        Uses pattern matching and NLP-like parsing.
        
        Args:
            raw_request: User's natural language request
            
        Returns:
            Dictionary with extracted entities
        """
        # Normalize text
        normalized = raw_request.lower().strip()
        
        # Extract patterns:
        # "I need [role] in [app]"
        # "Grant me [role] role in [app]"
        # "[user] needs [role] for [app]"
        
        # Common patterns
        patterns = [
            r'(?:need|want|request|grant|assign)\s+(?:me\s+)?(?:the\s+)?(?:role\s+)?(?:of\s+)?(?:a\s+)?([a-z\s]+?)\s+(?:role\s+)?(?:in|for|on)\s+([a-z\s]+?)(?:\s|$|\.)',
            r'(?:for|in)\s+([a-z\s]+?)\s+(?:role|position)',
            r'([a-z\s]+?)\s+(?:role|access)\s+(?:in|for)\s+([a-z\s]+?)',
        ]
        
        extracted = {
            'user_name': None,
            'application_name': None,
            'role_name': None
        }
        
        for pattern in patterns:
            matches = re.findall(pattern, normalized)
            if matches:
                if len(matches[0]) >= 2:
                    extracted['role_name'] = matches[0][0].strip()
                    extracted['application_name'] = matches[0][1].strip()
                break
        
        # Standardize extracted values
        if extracted['role_name']:
            extracted['role_name'] = self._standardize_name(extracted['role_name'])
        if extracted['application_name']:
            extracted['application_name'] = self._standardize_name(extracted['application_name'])
        
        return extracted
    
    def _standardize_name(self, name: str) -> str:
        """Standardize entity name (title case, remove extra spaces)."""
        return ' '.join(word.capitalize() for word in name.split())
    
    def validate_entities_in_db(self, entities: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate that extracted entities exist in the database.
        
        Returns entity IDs if found, raises error if not found.
        """
        self.connect_to_db()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Query user
            if entities.get('user_name'):
                cursor.execute(
                    "SELECT user_id FROM users WHERE LOWER(name) = %s AND status = 'active'",
                    (entities['user_name'].lower(),)
                )
                user_row = cursor.fetchone()
                if not user_row:
                    raise ValueError(f"User '{entities['user_name']}' not found or inactive")
                entities['user_id'] = user_row['user_id']
            
            # Query application
            if entities.get('application_name'):
                cursor.execute(
                    "SELECT app_id FROM applications WHERE LOWER(name) = %s",
                    (entities['application_name'].lower(),)
                )
                app_row = cursor.fetchone()
                if not app_row:
                    raise ValueError(f"Application '{entities['application_name']}' not found")
                entities['app_id'] = app_row['app_id']
            
            # Query role
            if entities.get('role_name') and entities.get('app_id'):
                cursor.execute(
                    "SELECT role_id FROM roles WHERE LOWER(name) = %s AND app_id = %s",
                    (entities['role_name'].lower(), entities['app_id'])
                )
                role_row = cursor.fetchone()
                if not role_row:
                    raise ValueError(f"Role '{entities['role_name']}' not found in {entities['application_name']}")
                entities['role_id'] = role_row['role_id']
            
            cursor.close()
            return entities
        
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            raise
        
        finally:
            self.close_db()


def lambda_handler(event, context):
    """
    Lambda handler for entity extraction.
    
    Args:
        event: {
            'request_id': str,
            'raw_request': str,
            'user_id': str (optional)
        }
        
    Returns:
        {
            'user_id': int,
            'app_id': int,
            'role_id': int,
            'entities': {...}
        }
    """
    extractor = EntityExtractor()
    
    try:
        raw_request = event.get('raw_request')
        request_id = event.get('request_id')
        
        if not raw_request:
            raise ValueError("Missing 'raw_request'")
        
        logger.info(f"Extracting entities from: {raw_request}")
        
        # Extract entities from text
        entities = extractor.extract_entities(raw_request)
        
        # Validate entities exist in database
        entities = extractor.validate_entities_in_db(entities)
        
        result = {
            'request_id': request_id,
            'user_id': entities.get('user_id'),
            'app_id': entities.get('app_id'),
            'role_id': entities.get('role_id'),
            'entities': {k: v for k, v in entities.items() if k.endswith('_name') or k.endswith('_id')}
        }
        
        logger.info(f"Entity extraction successful: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}", exc_info=True)
        return {
            'error': str(e),
            'request_id': event.get('request_id'),
            'entities': {}
        }
