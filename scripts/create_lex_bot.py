#!/usr/bin/env python3
"""
AWS Lex V2 Bot Creation Script for AskIAM Assistant

This script programmatically creates an AWS Lex V2 bot with intents and slots
as an alternative to manual console configuration.

Prerequisites:
- AWS credentials configured (aws configure)
- boto3 installed (pip install boto3)
- Python 3.7+
- CloudFormation stack created with Lex role

Usage:
    python create_lex_bot.py --region us-east-1 --role-arn arn:aws:iam::ACCOUNT:role/LexBotRole
"""

import argparse
import json
import time
import boto3
import sys
from typing import Dict, List, Optional

# Initialize Lex client
lex_client = None
iam_client = None

def initialize_clients(region: str):
    """Initialize AWS clients"""
    global lex_client, iam_client
    lex_client = boto3.client('lexv2-models', region_name=region)
    iam_client = boto3.client('iam', region_name=region)
    print(f"✓ Initialized AWS clients for region: {region}")

def create_slot_type(bot_name: str, slot_type_name: str, slot_values: List[str]) -> str:
    """Create a custom slot type"""
    print(f"  Creating slot type: {slot_type_name}")
    
    try:
        response = lex_client.create_slot_type(
            slotTypeName=slot_type_name,
            description=f"{slot_type_name} slot for AskIAM Assistant",
            slotTypeValues=[
                {
                    'sampleValue': {
                        'value': value
                    }
                }
                for value in slot_values
            ],
            valueSelectionSetting={
                'resolutionStrategy': 'TopResolution'
            }
        )
        slot_type_id = response['slotTypeId']
        print(f"  ✓ Created slot type: {slot_type_id}")
        return slot_type_id
    except Exception as e:
        print(f"  ✗ Error creating slot type: {e}")
        raise

def create_bot(
    bot_name: str,
    bot_description: str,
    role_arn: str,
    idle_session_ttl_seconds: int = 900
) -> str:
    """Create the Lex V2 bot"""
    print(f"Creating bot: {bot_name}")
    
    try:
        response = lex_client.create_bot(
            botName=bot_name,
            description=bot_description,
            roleArn=role_arn,
            dataPrivacy={
                'childDirected': False
            },
            idleSessionTTLInSeconds=idle_session_ttl_seconds
        )
        bot_id = response['botId']
        print(f"✓ Created bot: {bot_id}")
        return bot_id
    except Exception as e:
        print(f"✗ Error creating bot: {e}")
        raise

def create_locale(bot_id: str, locale_id: str = 'en_US') -> str:
    """Create bot locale"""
    print(f"Creating locale: {locale_id}")
    
    try:
        response = lex_client.create_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId=locale_id,
            description=f'{locale_id} locale for AskIAM Assistant',
            nluIntentConfidenceThreshold=0.10
        )
        print(f"✓ Created locale: {locale_id}")
        return locale_id
    except Exception as e:
        print(f"✗ Error creating locale: {e}")
        raise

def create_intent(
    bot_id: str,
    locale_id: str,
    intent_name: str,
    description: str,
    sample_utterances: List[str],
    fulfillment_lambda_arn: str
) -> str:
    """Create a Lex intent"""
    print(f"  Creating intent: {intent_name}")
    
    try:
        response = lex_client.create_intent(
            botId=bot_id,
            botVersion='DRAFT',
            intentsLocaleId=locale_id,
            intentName=intent_name,
            description=description,
            sampleUtterances=[
                {
                    'utterance': {
                        'utteranceText': utterance
                    }
                }
                for utterance in sample_utterances
            ],
            fulfillmentCodeHook={
                'enabled': True
            }
        )
        intent_id = response['intentId']
        print(f"  ✓ Created intent: {intent_id}")
        return intent_id
    except Exception as e:
        print(f"  ✗ Error creating intent: {e}")
        raise

def create_slot(
    bot_id: str,
    locale_id: str,
    intent_id: str,
    slot_name: str,
    slot_type_id: str,
    is_required: bool = False,
    prompt: Optional[str] = None
) -> str:
    """Create a slot in an intent"""
    print(f"    Creating slot: {slot_name}")
    
    try:
        slot_config = {
            'botId': bot_id,
            'botVersion': 'DRAFT',
            'intentsLocaleId': locale_id,
            'intentId': intent_id,
            'slotName': slot_name,
            'slotTypeId': slot_type_id,
            'valueElicitationSetting': {
                'slotConstraint': 'Required' if is_required else 'Optional',
                'promptSpecification': {
                    'messageGroupsList': [
                        {
                            'message': {
                                'plainTextMessage': {
                                    'value': prompt or f'What is the {slot_name}?'
                                }
                            }
                        }
                    ],
                    'maxRetries': 2
                }
            }
        }
        
        response = lex_client.create_slot(
            **slot_config
        )
        slot_id = response['slotId']
        print(f"    ✓ Created slot: {slot_id}")
        return slot_id
    except Exception as e:
        print(f"    ✗ Error creating slot: {e}")
        # Continue on slot creation failure
        return None

def create_bot_alias(bot_id: str, alias_name: str = 'PROD') -> str:
    """Create a bot alias"""
    print(f"Creating bot alias: {alias_name}")
    
    try:
        # Build bot first
        print("  Building bot...")
        lex_client.build_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId='en_US'
        )
        
        # Wait for build to complete
        time.sleep(5)
        
        response = lex_client.create_bot_alias(
            botAliasName=alias_name,
            description=f'{alias_name} alias for AskIAM Assistant',
            botId=bot_id,
            botVersion='DRAFT'
        )
        alias_id = response['botAliasId']
        print(f"✓ Created bot alias: {alias_id}")
        return alias_id
    except Exception as e:
        print(f"✗ Error creating alias: {e}")
        raise

def enable_lex_cloudwatch_logs(bot_id: str, log_group_name: str):
    """Enable CloudWatch logging for Lex bot"""
    print(f"Enabling CloudWatch logs: {log_group_name}")
    
    try:
        logs_client = boto3.client('logs')
        
        # Create log group if doesn't exist
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
            print(f"  ✓ Created log group")
        except logs_client.exceptions.ResourceAlreadyExistsException:
            print(f"  ✓ Log group exists")
        
        # Set retention
        logs_client.put_retention_policy(
            logGroupName=log_group_name,
            retentionInDays=14
        )
        print(f"  ✓ Set retention: 14 days")
    except Exception as e:
        print(f"  ✗ Warning: Could not enable CloudWatch logs: {e}")

def setup_access_request_intent(
    bot_id: str,
    locale_id: str,
    role_slot_type_id: str,
    app_slot_type_id: str,
    user_slot_type_id: str
):
    """Setup AccessRequestIntent"""
    print("\n=== Setting up AccessRequestIntent ===")
    
    sample_utterances = [
        "I need access to {Role}",
        "Please grant me {Role} role",
        "I want to request {Application} access for {User}",
        "I need {Role} permissions",
        "Can I get access to {Application}",
        "Grant {User} access to {Role}",
        "Request {Role} for the {Application} team"
    ]
    
    intent_id = create_intent(
        bot_id=bot_id,
        locale_id=locale_id,
        intent_name='AccessRequestIntent',
        description='Handle IAM access requests',
        sample_utterances=sample_utterances,
        fulfillment_lambda_arn='FULFILLED_BY_LEX_FUNCTION'
    )
    
    # Create slots
    create_slot(
        bot_id, locale_id, intent_id, 'User',
        user_slot_type_id, False,
        'Which user is requesting access? (optional)'
    )
    
    create_slot(
        bot_id, locale_id, intent_id, 'Role',
        role_slot_type_id, True,
        'Which role do you need access to?'
    )
    
    create_slot(
        bot_id, locale_id, intent_id, 'Application',
        app_slot_type_id, False,
        'Which application do you need access to? (optional)'
    )

def setup_validate_intent(
    bot_id: str,
    locale_id: str,
    entity_type_slot_id: str
):
    """Setup ValidateEntityIntent"""
    print("\n=== Setting up ValidateEntityIntent ===")
    
    sample_utterances = [
        "Validate {EntityName}",
        "Does {EntityName} exist?",
        "Check {EntityName}",
        "Is {EntityName} a valid user?",
        "Verify {EntityName}",
        "Look up {EntityName}",
        "Who is {EntityName}?"
    ]
    
    intent_id = create_intent(
        bot_id=bot_id,
        locale_id=locale_id,
        intent_name='ValidateEntityIntent',
        description='Validate IAM entities',
        sample_utterances=sample_utterances,
        fulfillment_lambda_arn='FULFILLED_BY_LEX_FUNCTION'
    )
    
    # Create EntityName slot
    create_slot(
        bot_id, locale_id, intent_id, 'EntityName',
        entity_type_slot_id, True,
        'What entity would you like me to validate?'
    )

def print_summary(bot_id: str, bot_name: str, region: str):
    """Print deployment summary"""
    print("\n" + "="*70)
    print("✓ Lex Bot Created Successfully!")
    print("="*70)
    print(f"\nBot Information:")
    print(f"  Name: {bot_name}")
    print(f"  ID: {bot_id}")
    print(f"  Region: {region}")
    print(f"\nNext Steps:")
    print(f"  1. Update CloudFormation outputs with bot ID and alias ID")
    print(f"  2. Configure Cognito Identity Pool")
    print(f"  3. Deploy frontend (HTML or React)")
    print(f"  4. Test bot in AWS Lex console")
    print(f"\nUseful AWS CLI Commands:")
    print(f"  # Get bot details")
    print(f"  aws lexv2-models describe-bot --bot-id {bot_id} --region {region}")
    print(f"\n  # List intents")
    print(f"  aws lexv2-models list-intents --bot-id {bot_id} --bot-version DRAFT --locale-id en_US --region {region}")
    print(f"\n  # Test bot with sample utterance")
    print(f"  aws lexv2-runtime recognize-text --bot-id {bot_id} --bot-alias-id <ALIAS_ID> --locale-id en_US --session-id test-session --text 'I need access to HR Analyst'")
    print("="*70)

def main():
    parser = argparse.ArgumentParser(description='Create AWS Lex V2 bot for AskIAM Assistant')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--role-arn', required=True, help='IAM role ARN for Lex bot')
    parser.add_argument('--fulfillment-lambda-arn', help='Lambda ARN for fulfillment')
    parser.add_argument('--bot-name', default='AskIAM-Assistant', help='Bot name')
    
    args = parser.parse_args()
    
    try:
        # Initialize clients
        initialize_clients(args.region)
        
        # Create slot types
        print("\n=== Creating Slot Types ===")
        
        role_values = [
            'HR Analyst', 'Finance Manager', 'IT Admin', 'Developer',
            'Data Analyst', 'Marketing Manager', 'Sales Representative',
            'Project Manager', 'Business Analyst', 'DevOps Engineer'
        ]
        role_slot_id = create_slot_type('AskIAM-Assistant', 'RoleSlot', role_values)
        
        app_values = [
            'Salesforce', 'SAP', 'Workday', 'Google Workspace', 'ServiceNow',
            'Jira', 'Slack', 'Azure AD', 'Okta', 'GitHub Enterprise'
        ]
        app_slot_id = create_slot_type('AskIAM-Assistant', 'ApplicationSlot', app_values)
        
        entity_values = ['user', 'role', 'application', 'group']
        entity_slot_id = create_slot_type('AskIAM-Assistant', 'EntityTypeSlot', entity_values)
        
        # Create bot
        print("\n=== Creating Bot ===")
        bot_id = create_bot(
            bot_name=args.bot_name,
            bot_description='AI-powered IAM access validation assistant',
            role_arn=args.role_arn
        )
        
        # Create locale
        locale_id = create_locale(bot_id)
        
        # Setup intents
        setup_access_request_intent(bot_id, locale_id, role_slot_id, app_slot_id, entity_slot_id)
        setup_validate_intent(bot_id, locale_id, entity_slot_id)
        
        # Wait for intents to be created
        print("\nWaiting for intents to be created...")
        time.sleep(3)
        
        # Create bot alias
        alias_id = create_bot_alias(bot_id)
        
        # Enable logging
        log_group = f'/aws/lex/{args.bot_name}'
        enable_lex_cloudwatch_logs(bot_id, log_group)
        
        # Print summary
        print_summary(bot_id, args.bot_name, args.region)
        
        print(f"\nBot Alias ID: {alias_id}")
        print("\nSave these values for frontend configuration!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
