#!/usr/bin/env python3
"""
Lex Slot Synchronization Script
Syncs user, application, and role values from IAM database to AWS Lex slot types
This should be run periodically (e.g., every 6 hours via CloudWatch Events)
"""

import json
import boto3
import psycopg2
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Clients
lexv2_client = boto3.client('lexv2-models')
secrets_client = boto3.client('secretsmanager')

# Configuration
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
LEX_BOT_ID = os.environ.get('LEX_BOT_ID')
LEX_BOT_LOCALE = 'en_US'


class LexSlotSynchronizer:
    """Synchronizes database entities to AWS Lex slot types"""

    def __init__(self):
        self.db_creds = self._get_db_credentials()
        self.bot_id = LEX_BOT_ID

    def _get_db_credentials(self) -> Dict[str, str]:
        """Retrieve database credentials from Secrets Manager"""
        try:
            response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
            creds = json.loads(response['SecretString'])
            logger.info("Database credentials retrieved successfully")
            return creds
        except Exception as e:
            logger.error(f"Error retrieving DB credentials: {str(e)}")
            raise

    def _get_db_connection(self):
        """Create connection to PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host=self.db_creds['host'],
                port=self.db_creds.get('port', 5432),
                database=self.db_creds['dbname'],
                user=self.db_creds['username'],
                password=self.db_creds['password']
            )
            logger.info("Database connection established")
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def get_users(self) -> List[Dict[str, str]]:
        """Retrieve all users from database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Query all users (adjust table name as needed)
            cursor.execute("""
                SELECT DISTINCT username, email 
                FROM users 
                WHERE is_active = true 
                ORDER BY username
            """)
            
            users = []
            for row in cursor.fetchall():
                username, email = row
                # Use email if available, otherwise username
                value = email or username
                users.append({
                    'username': username,
                    'email': email,
                    'display_value': value
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(users)} users from database")
            return users
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            return []

    def get_applications(self) -> List[Dict[str, str]]:
        """Retrieve all applications from database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Query all applications
            cursor.execute("""
                SELECT DISTINCT application_name, display_name
                FROM applications
                WHERE is_active = true
                ORDER BY application_name
            """)
            
            applications = []
            for row in cursor.fetchall():
                app_name, display_name = row
                applications.append({
                    'name': app_name,
                    'display_value': display_name or app_name
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(applications)} applications from database")
            return applications
        except Exception as e:
            logger.error(f"Error retrieving applications: {str(e)}")
            return []

    def get_roles(self) -> List[Dict[str, str]]:
        """Retrieve all roles from database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Query all roles
            cursor.execute("""
                SELECT DISTINCT role_name, role_description
                FROM roles
                WHERE is_active = true
                ORDER BY role_name
            """)
            
            roles = []
            for row in cursor.fetchall():
                role_name, description = row
                roles.append({
                    'name': role_name,
                    'display_value': description or role_name
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(roles)} roles from database")
            return roles
        except Exception as e:
            logger.error(f"Error retrieving roles: {str(e)}")
            return []

    def update_lex_slot_type(self, slot_type_name: str, values: List[Dict[str, str]]) -> bool:
        """
        Update AWS Lex slot type with new values
        
        Args:
            slot_type_name: Name of the Lex slot type (e.g., 'UserType')
            values: List of dicts with 'display_value' and/or 'name' keys
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format slot values for Lex
            slot_values = [
                {
                    'sampleValue': {
                        'value': v.get('display_value') or v.get('value', '')
                    },
                    'description': v.get('description', '')
                }
                for v in values
                if v.get('display_value') or v.get('value')
            ]

            if not slot_values:
                logger.warning(f"No values to update for slot type {slot_type_name}")
                return False

            # Update Lex slot type
            response = lexv2_client.put_slot_type(
                slotTypeName=slot_type_name,
                botId=self.bot_id,
                botVersion='DRAFT',
                localeId=LEX_BOT_LOCALE,
                slotTypeValues=slot_values,
                valueSelectionSetting={
                    'resolutionStrategy': 'ORIGINAL_VALUE'
                }
            )

            logger.info(
                f"Updated Lex slot type '{slot_type_name}' with {len(slot_values)} values. "
                f"SlotTypeId: {response.get('slotTypeId')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating Lex slot type {slot_type_name}: {str(e)}")
            return False

    def build_bot_locale(self) -> bool:
        """Build/train the Lex bot locale after updating slot types"""
        try:
            response = lexv2_client.build_bot_locale(
                botId=self.bot_id,
                botVersion='DRAFT',
                localeId=LEX_BOT_LOCALE
            )

            build_status = response.get('botLocaleStatus', 'Unknown')
            logger.info(f"Bot locale build initiated. Status: {build_status}")
            return True

        except Exception as e:
            logger.error(f"Error building bot locale: {str(e)}")
            return False

    def synchronize(self) -> Dict[str, Any]:
        """
        Main synchronization method
        Updates all slot types and rebuilds the bot
        """
        logger.info("=== Starting Lex Slot Synchronization ===")
        start_time = datetime.now()

        results = {
            'timestamp': start_time.isoformat(),
            'users_synced': 0,
            'applications_synced': 0,
            'roles_synced': 0,
            'errors': []
        }

        try:
            # Sync users
            logger.info("Syncing users...")
            users = self.get_users()
            if users:
                success = self.update_lex_slot_type('UserType', users)
                results['users_synced'] = len(users) if success else 0
            else:
                results['errors'].append("No users found in database")

            # Sync applications
            logger.info("Syncing applications...")
            applications = self.get_applications()
            if applications:
                success = self.update_lex_slot_type('ApplicationType', applications)
                results['applications_synced'] = len(applications) if success else 0
            else:
                results['errors'].append("No applications found in database")

            # Sync roles
            logger.info("Syncing roles...")
            roles = self.get_roles()
            if roles:
                success = self.update_lex_slot_type('RoleType', roles)
                results['roles_synced'] = len(roles) if success else 0
            else:
                results['errors'].append("No roles found in database")

            # Build bot to apply changes
            logger.info("Building Lex bot locale...")
            build_success = self.build_bot_locale()
            results['bot_built'] = build_success

            elapsed_time = (datetime.now() - start_time).total_seconds()
            results['elapsed_seconds'] = elapsed_time

            logger.info(f"=== Synchronization complete in {elapsed_time:.2f} seconds ===")
            logger.info(f"Summary: {results['users_synced']} users, {results['applications_synced']} apps, {results['roles_synced']} roles")

            return results

        except Exception as e:
            logger.error(f"Synchronization failed: {str(e)}")
            results['errors'].append(str(e))
            return results


def lambda_handler(event, context):
    """
    AWS Lambda handler for automated slot synchronization
    Can be triggered by CloudWatch Events (e.g., every 6 hours)
    """
    try:
        synchronizer = LexSlotSynchronizer()
        results = synchronizer.synchronize()

        return {
            'statusCode': 200,
            'body': json.dumps(results),
            'message': 'Lex slot synchronization completed successfully'
        }

    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'message': 'Lex slot synchronization failed'
        }


def main():
    """Local execution for testing/manual run"""
    import sys
    
    # Set environment variables (from CloudFormation outputs)
    if not os.environ.get('DB_SECRET_ARN') or not os.environ.get('LEX_BOT_ID'):
        print("Error: Missing required environment variables:")
        print("  DB_SECRET_ARN: ARN of the database secret in Secrets Manager")
        print("  LEX_BOT_ID: ID of the Lex bot (from CloudFormation output)")
        sys.exit(1)

    synchronizer = LexSlotSynchronizer()
    results = synchronizer.synchronize()

    print("\n=== Synchronization Results ===")
    print(json.dumps(results, indent=2))

    # Exit with error code if there were errors
    if results.get('errors'):
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
