"""
AuditLogger Lambda Function
Logs validation events for compliance and auditing.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS clients
secrets_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')


class AuditLogger:
    """Logs validation events for audit and compliance."""
    
    def __init__(self):
        self.db_endpoint = os.getenv('DB_ENDPOINT')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'iamdb')
        self.db_user = os.getenv('DB_USER', 'iamadmin')
        self.db_password = self._get_db_password()
        self.conn = None
        self.audit_enabled = self._is_audit_enabled()
        self.s3_bucket = os.getenv('AUDIT_BUCKET', '')
    
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
    
    def _is_audit_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        try:
            import boto3
            ssm_client = boto3.client('ssm')
            response = ssm_client.get_parameter(
                Name=f"/askiam/{os.getenv('ENVIRONMENT')}/app/audit-enabled"
            )
            return response['Parameter']['Value'].lower() == 'true'
        except Exception as e:
            logger.warning(f"Failed to check audit enabled: {e}, defaulting to true")
            return True
    
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
            logger.info("Connected to RDS Aurora for audit logging")
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise
    
    def close_db(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def log_to_database(self, audit_record: Dict[str, Any]) -> None:
        """
        Log audit record to RDS.
        
        Args:
            audit_record: Audit event details
        """
        if not self.audit_enabled:
            logger.info("Audit logging disabled, skipping database write")
            return
        
        self.connect_to_db()
        
        try:
            cursor = self.conn.cursor()
            
            # Insert into audit_log table
            cursor.execute("""
                INSERT INTO audit_log (
                    request_id, user_id, action, validation_status,
                    validation_method, reason, context_ip, context_session,
                    timestamp, details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                audit_record['request_id'],
                audit_record['user_id'],
                'ACCESS_REQUEST_VALIDATION',
                audit_record['validation_result'],
                audit_record['validation_method'],
                audit_record['reason'],
                audit_record['context'].get('ip_address'),
                audit_record['context'].get('session_id'),
                audit_record['timestamp'],
                json.dumps(audit_record.get('details', {}))
            ))
            
            self.conn.commit()
            logger.info(f"Audit record logged: request_id={audit_record['request_id']}")
        
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
            self.conn.rollback()
            raise
        
        finally:
            cursor.close()
            self.close_db()
    
    def log_to_cloudwatch(self, audit_record: Dict[str, Any]) -> None:
        """
        Log audit record to CloudWatch in structured JSON format.
        
        Args:
            audit_record: Audit event details
        """
        structured_log = {
            'timestamp': audit_record['timestamp'],
            'request_id': audit_record['request_id'],
            'user_id': audit_record['user_id'],
            'action': 'ACCESS_REQUEST_VALIDATION',
            'status': audit_record['validation_result'],
            'method': audit_record['validation_method'],
            'reason': audit_record['reason'],
            'context': audit_record['context'],
            'details': audit_record.get('details', {}),
            'level': 'AUDIT'
        }
        
        logger.info(json.dumps(structured_log))
    
    def archive_to_s3(self, audit_record: Dict[str, Any]) -> None:
        """
        Archive audit record to S3 for long-term retention.
        
        Args:
            audit_record: Audit event details
        """
        if not self.s3_bucket:
            logger.warning("S3 bucket not configured, skipping archive")
            return
        
        try:
            # Create S3 path: s3://bucket/audit/yyyy/mm/dd/request_id.json
            date = datetime.fromisoformat(audit_record['timestamp']).date()
            s3_key = f"audit/{date.year:04d}/{date.month:02d}/{date.day:02d}/{audit_record['request_id']}.json"
            
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(audit_record, default=str),
                ServerSideEncryption='AES256',
                ContentType='application/json'
            )
            
            logger.info(f"Audit record archived to S3: {s3_key}")
        
        except Exception as e:
            logger.error(f"Failed to archive to S3: {e}")
            # Don't raise - archival failure shouldn't block audit logging


def lambda_handler(event, context):
    """
    Lambda handler for audit logging.
    
    Args:
        event: {
            'request_id': str,
            'user_id': str,
            'validation_result': bool,
            'validation_method': str,
            'reason': str,
            'context': {...},
            'timestamp': str,
            'details': {...}
        }
        
    Returns:
        Success status
    """
    logger_instance = AuditLogger()
    
    try:
        request_id = event.get('request_id')
        user_id = event.get('user_id')
        validation_result = 'VALID' if event.get('validation_result') else 'INVALID'
        
        audit_record = {
            'request_id': request_id,
            'user_id': user_id,
            'validation_result': validation_result,
            'validation_method': event.get('validation_method', 'unknown'),
            'reason': event.get('reason', ''),
            'context': event.get('context', {}),
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
            'details': event.get('details', {})
        }
        
        # Log to all destinations
        logger_instance.log_to_cloudwatch(audit_record)
        logger_instance.log_to_database(audit_record)
        logger_instance.archive_to_s3(audit_record)
        
        return {
            'statusCode': 200,
            'request_id': request_id,
            'message': 'Audit logging completed successfully'
        }
    
    except Exception as e:
        logger.error(f"Audit logging failed: {e}", exc_info=True)
        # Still try to log to CloudWatch
        try:
            logger.error(json.dumps({
                'level': 'ERROR',
                'message': 'Audit logging error',
                'error': str(e),
                'request_id': event.get('request_id')
            }))
        except:
            pass
        
        return {
            'statusCode': 500,
            'request_id': event.get('request_id'),
            'error': str(e)
        }
