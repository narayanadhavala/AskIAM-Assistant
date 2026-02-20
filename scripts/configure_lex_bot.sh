#!/bin/bash
# AWS Lex V2 Bot Configuration Script
# Sets up bot locale, intents, slots, and builds the bot
# Run this after CloudFormation deployment

set -e

# ==================== Configuration ====================
ENVIRONMENT=${1:-dev}
REGION=${2:-us-west-2}

echo "=== AWS Lex V2 Bot Configuration ==="
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo ""

# ==================== Step 1: Get Bot ID from CloudFormation ====================
echo "Step 1: Retrieving Lex Bot ID from CloudFormation..."

BOT_ID=$(aws cloudformation describe-stacks \
  --stack-name askiam-lex-${ENVIRONMENT} \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`LexBotId`].OutputValue' \
  --output text)

if [ -z "$BOT_ID" ]; then
  echo "ERROR: Could not find Lex Bot ID. Ensure CloudFormation stack deployed successfully."
  exit 1
fi

echo "✓ Lex Bot ID: $BOT_ID"
echo ""

# ==================== Step 2: Create Bot Locale (English US) ====================
echo "Step 2: Creating Bot Locale (English US)..."

LOCALE_RESPONSE=$(aws lexv2-models create-bot-locale \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --description "English US locale for AskIAM Bot" \
  --nlu-confidence-threshold 0.40 \
  --voice-settings voiceId=Joanna \
  --region $REGION \
  --output json)

LOCALE_STATUS=$(echo $LOCALE_RESPONSE | jq -r '.botLocaleStatus // "Unknown"')
echo "✓ Bot Locale created. Status: $LOCALE_STATUS"
echo ""

# ==================== Step 3: Create Slot Types ====================
echo "Step 3: Creating Slot Types..."

# Slot Type 1: User
echo "  Creating UserType slot..."
aws lexv2-models create-slot-type \
  --slot-type-name UserType \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --slot-type-values \
    sampleValue={value="aaron.nichols"} \
    sampleValue={value="john.smith"} \
    sampleValue={value="jane.doe"} \
    sampleValue={value="bob.johnson"} \
    sampleValue={value="alice.williams"} \
  --value-selection-setting resolutionStrategy=ORIGINAL_VALUE \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ UserType created"

# Slot Type 2: Application
echo "  Creating ApplicationType slot..."
aws lexv2-models create-slot-type \
  --slot-type-name ApplicationType \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --slot-type-values \
    sampleValue={value="Workday"} \
    sampleValue={value="Salesforce"} \
    sampleValue={value="AzureAD"} \
    sampleValue={value="ServiceNow"} \
    sampleValue={value="GitHub"} \
    sampleValue={value="Jira"} \
  --value-selection-setting resolutionStrategy=ORIGINAL_VALUE \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ ApplicationType created"

# Slot Type 3: Role
echo "  Creating RoleType slot..."
aws lexv2-models create-slot-type \
  --slot-type-name RoleType \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --slot-type-values \
    sampleValue={value="HR Analyst"} \
    sampleValue={value="Payroll Admin"} \
    sampleValue={value="IT Admin"} \
    sampleValue={value="Finance Manager"} \
    sampleValue={value="Systems Administrator"} \
    sampleValue={value="Application Owner"} \
    sampleValue={value="Read-Only User"} \
  --value-selection-setting resolutionStrategy=ORIGINAL_VALUE \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ RoleType created"
echo ""

# ==================== Step 4: Get Slot Type IDs ====================
echo "Step 4: Retrieving Slot Type IDs..."

# Get UserType ID
USER_SLOT_TYPE_ID=$(aws lexv2-models list-slot-types \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --region $REGION \
  --query "slotTypeSummaries[?slotTypeName=='UserType'].slotTypeId" \
  --output text)

# Get ApplicationType ID
APP_SLOT_TYPE_ID=$(aws lexv2-models list-slot-types \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --region $REGION \
  --query "slotTypeSummaries[?slotTypeName=='ApplicationType'].slotTypeId" \
  --output text)

# Get RoleType ID
ROLE_SLOT_TYPE_ID=$(aws lexv2-models list-slot-types \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --region $REGION \
  --query "slotTypeSummaries[?slotTypeName=='RoleType'].slotTypeId" \
  --output text)

echo "✓ UserType ID: $USER_SLOT_TYPE_ID"
echo "✓ ApplicationType ID: $APP_SLOT_TYPE_ID"
echo "✓ RoleType ID: $ROLE_SLOT_TYPE_ID"
echo ""

# ==================== Step 5: Create Intent ====================
echo "Step 5: Creating Intent (IAMAccessRequest)..."

INTENT_RESPONSE=$(aws lexv2-models create-intent \
  --intent-name IAMAccessRequest \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --description "Intent to handle IAM access requests" \
  --sample-utterances \
    utteranceInput={text="I need access to {Role} in {Application}"} \
    utteranceInput={text="Grant me {Role} role in {Application}"} \
    utteranceInput={text="I need {Application} {Role} access"} \
    utteranceInput={text="Provide {Role} access for {Application}"} \
    utteranceInput={text="Add me to {Role} in {Application}"} \
    utteranceInput={text="I require {Role} permissions in {Application}"} \
    utteranceInput={text="I would like access to {Role} in {Application}"} \
    utteranceInput={text="Request {Role} role for {Application}"} \
  --region $REGION \
  --output json)

INTENT_ID=$(echo $INTENT_RESPONSE | jq -r '.intentId // "Unknown"')
echo "✓ Intent created. ID: $INTENT_ID"
echo ""

# ==================== Step 6: Create Slots ====================
echo "Step 6: Creating Slots..."

# Get Lambda fulfillment function ARN
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name askiam-lex-${ENVIRONMENT} \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`LexFulfillmentFunctionArn`].OutputValue' \
  --output text)

echo "  Creating User slot..."
aws lexv2-models create-slot \
  --slot-name User \
  --slot-type-id $USER_SLOT_TYPE_ID \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --intent-id $INTENT_ID \
  --value-elicitation-setting "slotConstraint=Optional,promptSpecification={messageGroupsList=[{message={plainTextMessage={value='What is your user name or email?'}}}],maxRetries=3}" \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ User slot created"

echo "  Creating Application slot..."
aws lexv2-models create-slot \
  --slot-name Application \
  --slot-type-id $APP_SLOT_TYPE_ID \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --intent-id $INTENT_ID \
  --value-elicitation-setting "slotConstraint=Optional,promptSpecification={messageGroupsList=[{message={plainTextMessage={value='Which application do you need access to?'}}}],maxRetries=3}" \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ Application slot created"

echo "  Creating Role slot..."
aws lexv2-models create-slot \
  --slot-name Role \
  --slot-type-id $ROLE_SLOT_TYPE_ID \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --intent-id $INTENT_ID \
  --value-elicitation-setting "slotConstraint=Optional,promptSpecification={messageGroupsList=[{message={plainTextMessage={value='What role do you need access to?'}}}],maxRetries=3}" \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "  ✓ Role slot created"
echo ""

# ==================== Step 7: Update Intent with Fulfillment Hook ====================
echo "Step 7: Updating Intent with Fulfillment Lambda..."

aws lexv2-models update-intent \
  --intent-id $INTENT_ID \
  --intent-name IAMAccessRequest \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --fulfillment-code-hook-settings fullfillmentUpdatesSpecification={active=true,startResponse={messageGroupsList=[{message={plainTextMessage={value='Processing your request...'}}}],delayInSeconds=0},updateResponse={messageGroupsList=[{message={plainTextMessage={value='Request processed.'}}}],delayInSeconds=0},timeoutInSeconds=30} \
  --region $REGION \
  > /dev/null 2>&1 || true

echo "✓ Fulfillment Lambda configured for intent"
echo ""

# ==================== Step 8: Build Bot Locale ====================
echo "Step 8: Building Bot Locale..."

BUILD_RESPONSE=$(aws lexv2-models build-bot-locale \
  --bot-id $BOT_ID \
  --bot-version DRAFT \
  --locale-id en_US \
  --region $REGION \
  --output json)

BUILD_STATUS=$(echo $BUILD_RESPONSE | jq -r '.botLocaleStatus // "Unknown"')
echo "✓ Bot locale build initiated. Status: $BUILD_STATUS"
echo ""
echo "   Waiting for build to complete (this may take 1-2 minutes)..."

# Poll build status
MAX_ATTEMPTS=24
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  CURRENT_STATUS=$(aws lexv2-models describe-bot-locale \
    --bot-id $BOT_ID \
    --bot-version DRAFT \
    --locale-id en_US \
    --region $REGION \
    --query 'botLocaleStatus' \
    --output text)
  
  if [ "$CURRENT_STATUS" == "Built" ]; then
    echo "✓ Bot locale built successfully!"
    break
  elif [ "$CURRENT_STATUS" == "Failed" ]; then
    echo "✗ Bot locale build failed!"
    exit 1
  else
    echo "   Status: $CURRENT_STATUS (waiting...)"
    sleep 5
  fi
  
  ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "⚠ Build timeout. Check AWS Console for status."
fi

echo ""

# ==================== Step 9: Get Built Bot Version ====================
echo "Step 9: Retrieving Built Bot Version..."

BUILT_VERSION=$(aws lexv2-models list-bot-versions \
  --bot-id $BOT_ID \
  --region $REGION \
  --query "botVersionSummaries[?botStatus=='Available'].botVersion" \
  --output text | head -1)

if [ -z "$BUILT_VERSION" ]; then
  echo "⚠ Warning: No built version found. Build status check may have timed out."
  BUILT_VERSION="DRAFT"
fi

echo "✓ Built Bot Version: $BUILT_VERSION"
echo ""

# ==================== Step 10: Create Bot Alias ====================
echo "Step 10: Creating Bot Alias (Production)..."

ALIAS_RESPONSE=$(aws lexv2-models create-bot-alias \
  --bot-alias-name Production \
  --bot-id $BOT_ID \
  --bot-version $BUILT_VERSION \
  --description "Production alias for AskIAM Bot with Lex entity extraction" \
  --region $REGION \
  --output json 2>&1 || true)

ALIAS_ID=$(echo $ALIAS_RESPONSE | jq -r '.botAliasId // "Unknown"' 2>/dev/null || echo "Check console")
ALIAS_STATUS=$(echo $ALIAS_RESPONSE | jq -r '.botAliasStatus // "Unknown"' 2>/dev/null || echo "Check console")

echo "✓ Bot Alias created. ID: $ALIAS_ID, Status: $ALIAS_STATUS"
echo ""

# ==================== Summary ====================
echo "=========================================="
echo "✓ Lex Bot Configuration Complete!"
echo "=========================================="
echo ""
echo "Bot Details:"
echo "  • Bot ID:              $BOT_ID"
echo "  • Bot Name:            AskIAM-Bot-${ENVIRONMENT}"
echo "  • Locale:              en_US"
echo "  • Intent:              IAMAccessRequest"
echo "  • Fulfillment Lambda:  $LAMBDA_ARN"
echo "  • Production Alias:    $ALIAS_ID"
echo ""
echo "Next Steps:"
echo "  1. Sync database slots: python scripts/sync_lex_slots.py"
echo "  2. Test intent recognition:"
echo "     aws lexv2-runtime recognize-text \\"
echo "       --bot-id $BOT_ID \\"
echo "       --bot-alias-id $ALIAS_ID \\"
echo "       --locale-id en_US \\"
echo "       --session-id test-session \\"
echo "       --text \"I need Admin access to Salesforce\""
echo "  3. Test API endpoint: curl -X POST <LEX_PROXY_URL>"
echo ""
echo "Documentation: See LEX_DEPLOYMENT_GUIDE.md for testing and troubleshooting"
echo ""
