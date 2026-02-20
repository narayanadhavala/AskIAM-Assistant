#!/bin/bash

# AskIAM Assistant - Frontend Setup Script
# This script configures environment variables and deploys the frontend to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AskIAM Assistant - Frontend Setup${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Get CloudFormation Stack Information
echo -e "\n${YELLOW}Step 1: Retrieving CloudFormation Stack Information${NC}"

read -p "Enter CloudFormation stack name (default: askiam-assistant): " STACK_NAME
STACK_NAME=${STACK_NAME:-askiam-assistant}

read -p "Enter AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

echo -e "${YELLOW}Fetching stack outputs...${NC}"

# Get CloudFormation outputs
if ! STACK_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null); then
    echo -e "${RED}✗ Failed to retrieve CloudFormation stack${NC}"
    echo "  Make sure the stack exists and AWS credentials are configured"
    exit 1
fi

# Parse outputs
LEX_BOT_ID=$(echo "$STACK_OUTPUTS" | grep -o '"OutputKey": "LexBotId"' -A2 | grep OutputValue | cut -d'"' -f4 || echo "")
UI_BUCKET=$(echo "$STACK_OUTPUTS" | grep -o '"OutputKey": "UIBucket"' -A2 | grep OutputValue | cut -d'"' -f4 || echo "")
CLOUDFRONT_URL=$(echo "$STACK_OUTPUTS" | grep -o '"OutputKey": "CloudFrontURL"' -A2 | grep OutputValue | cut -d'"' -f4 || echo "")

echo -e "${GREEN}✓ Retrieved stack information${NC}"

# Step 2: Get Cognito Information
echo -e "\n${YELLOW}Step 2: Cognito Identity Pool Configuration${NC}"

read -p "Enter Cognito Identity Pool ID (format: region:xxxxx): " COGNITO_POOL_ID

if [ -z "$COGNITO_POOL_ID" ]; then
    echo -e "${YELLOW}ℹ Creating new Cognito Identity Pool...${NC}"
    
    read -p "Enter desired Identity Pool name (default: AskIAMAssistant-Identity-Pool): " POOL_NAME
    POOL_NAME=${POOL_NAME:-AskIAMAssistant-Identity-Pool}
    
    COGNITO_POOL_ID=$(aws cognito-identity create-identity-pool \
        --identity-pool-name "$POOL_NAME" \
        --allow-unauthenticated-identities \
        --region "$AWS_REGION" \
        --query 'IdentityPoolId' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$COGNITO_POOL_ID" ]; then
        echo -e "${RED}✗ Failed to create Cognito pool${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Created Cognito Identity Pool: $COGNITO_POOL_ID${NC}"
fi

# Step 3: Get Lex Bot Alias
echo -e "\n${YELLOW}Step 3: Lex Bot Alias Configuration${NC}"

if [ -z "$LEX_BOT_ID" ]; then
    read -p "Enter Lex Bot ID if already created: " LEX_BOT_ID
fi

if [ -n "$LEX_BOT_ID" ]; then
    # Get Lex aliases
    echo -e "${YELLOW}Fetching Lex bot aliases...${NC}"
    
    ALIASES=$(aws lexv2-models list-bot-aliases \
        --bot-id "$LEX_BOT_ID" \
        --region "$AWS_REGION" \
        --output json 2>/dev/null || echo "{}")
    
    ALIAS_ID=$(echo "$ALIASES" | grep -o '"botAliasId": "[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$ALIAS_ID" ]; then
        read -p "Enter Lex Bot Alias ID (e.g., PROD): " ALIAS_ID
    else
        echo -e "${GREEN}✓ Found Lex Alias: $ALIAS_ID${NC}"
    fi
else
    echo -e "${YELLOW}ℹ Run 'scripts/create_lex_bot.py' to create the bot first${NC}"
    read -p "Enter Lex Bot ID: " LEX_BOT_ID
    read -p "Enter Lex Bot Alias ID: " ALIAS_ID
fi

# Step 4: Create Environment File
echo -e "\n${YELLOW}Step 4: Creating Environment Configuration${NC}"

ENV_FILE="$PROJECT_ROOT/frontend/.env.production"

cat > "$ENV_FILE" << EOF
# AskIAM Assistant - Frontend Environment Variables
# Generated: $(date)

# AWS Configuration
REACT_APP_AWS_REGION=$AWS_REGION
REACT_APP_LEX_BOT_ID=$LEX_BOT_ID
REACT_APP_LEX_ALIAS_ID=$ALIAS_ID
REACT_APP_COGNITO_POOL_ID=$COGNITO_POOL_ID

# S3 and CloudFront
REACT_APP_S3_BUCKET=$UI_BUCKET
REACT_APP_CLOUDFRONT_URL=$CLOUDFRONT_URL

# Application Settings
REACT_APP_API_TIMEOUT=30000
REACT_APP_CHAT_SESSION_TIMEOUT=900
REACT_APP_DEBUG=false
EOF

echo -e "${GREEN}✓ Created environment file: $ENV_FILE${NC}"

# Step 5: Create HTML Version Configuration
echo -e "\n${YELLOW}Step 5: Configuring HTML Version${NC}"

HTML_FILE="$PROJECT_ROOT/frontend/lex_chat_interface.html"

if [ -f "$HTML_FILE" ]; then
    # Create a configuration script
    CONFIG_JS="$PROJECT_ROOT/frontend/config.js"
    
    cat > "$CONFIG_JS" << EOF
// AskIAM Assistant - Frontend Configuration
// Generated: $(date)

window.ASKIAM_CONFIG = {
    region: '$AWS_REGION',
    botId: '$LEX_BOT_ID',
    botAliasId: '$ALIAS_ID',
    localeId: 'en_US',
    cognitoPoolId: '$COGNITO_POOL_ID',
    apiTimeout: 30000,
    sessionTimeout: 900
};

// Override in HTML before initializing
function getLexConfig() {
    return window.ASKIAM_CONFIG;
}
EOF

    echo -e "${GREEN}✓ Created configuration file: $CONFIG_JS${NC}"
fi

# Step 6: React Setup (Optional)
echo -e "\n${YELLOW}Step 6: React Application Setup${NC}"

read -p "Do you want to set up React application? (y/n): " -n 1 -r SETUP_REACT
echo

if [[ $SETUP_REACT =~ ^[Yy]$ ]]; then
    REACT_DIR="$PROJECT_ROOT/frontend/react-app"
    
    if [ ! -d "$REACT_DIR" ]; then
        echo -e "${YELLOW}Creating React application...${NC}"
        
        cd "$PROJECT_ROOT/frontend"
        npx create-react-app react-app --template typescript
        
        cd react-app
        npm install @aws-sdk/client-lex-runtime-v2 @aws-sdk/client-cognito-identity @aws-sdk/credential-provider-cognito-identity
        
        echo -e "${GREEN}✓ Created React application${NC}"
    fi
    
    # Copy component
    cp "$PROJECT_ROOT/frontend/AskIAMChatInterface.jsx" "$REACT_DIR/src/components/" 2>/dev/null || \
        mkdir -p "$REACT_DIR/src/components" && \
        cp "$PROJECT_ROOT/frontend/AskIAMChatInterface.jsx" "$REACT_DIR/src/components/"
    
    # Create environment file for React
    REACT_ENV_FILE="$REACT_DIR/.env"
    cat > "$REACT_ENV_FILE" << EOF
REACT_APP_AWS_REGION=$AWS_REGION
REACT_APP_LEX_BOT_ID=$LEX_BOT_ID
REACT_APP_LEX_ALIAS_ID=$ALIAS_ID
REACT_APP_COGNITO_POOL_ID=$COGNITO_POOL_ID
EOF
    
    echo -e "${GREEN}✓ Configured React environment${NC}"
fi

# Step 7: Deploy to S3 (Optional)
echo -e "\n${YELLOW}Step 7: Deploy to AWS${NC}"

read -p "Deploy frontend to S3 now? (y/n): " -n 1 -r DEPLOY_NOW
echo

if [[ $DEPLOY_NOW =~ ^[Yy]$ ]]; then
    if [ -z "$UI_BUCKET" ]; then
        read -p "Enter S3 bucket name for UI: " UI_BUCKET
    fi
    
    if [ -n "$UI_BUCKET" ]; then
        echo -e "${YELLOW}Deploying HTML version to S3...${NC}"
        
        aws s3 cp "$HTML_FILE" \
            "s3://$UI_BUCKET/index.html" \
            --region "$AWS_REGION" \
            --content-type "text/html" \
            --metadata "generated=$(date)" || echo -e "${RED}✗ HTML upload failed${NC}"
        
        # Deploy config file
        if [ -f "$CONFIG_JS" ]; then
            aws s3 cp "$CONFIG_JS" \
                "s3://$UI_BUCKET/config.js" \
                --region "$AWS_REGION" \
                --content-type "application/javascript" || echo -e "${RED}✗ Config upload failed${NC}"
        fi
        
        echo -e "${GREEN}✓ Deployed to S3${NC}"
        
        if [ -n "$CLOUDFRONT_URL" ]; then
            echo -e "\n${GREEN}Frontend URL:${NC}"
            echo "  $CLOUDFRONT_URL"
        else
            echo -e "\n${GREEN}Frontend S3 URL:${NC}"
            echo "  https://$UI_BUCKET.s3.amazonaws.com"
        fi
    fi
fi

# Step 8: Generate Deployment Report
echo -e "\n${YELLOW}Step 8: Deployment Summary${NC}"

REPORT_FILE="$PROJECT_ROOT/DEPLOYMENT_REPORT.md"

cat > "$REPORT_FILE" << EOF
# AskIAM Assistant - Frontend Deployment Report

Generated: $(date)

## Configuration Summary

### AWS Environment
- **Region:** $AWS_REGION
- **Stack Name:** $STACK_NAME

### Lex Configuration
- **Bot ID:** $LEX_BOT_ID
- **Bot Alias:** $ALIAS_ID

### Cognito Configuration
- **Identity Pool ID:** $COGNITO_POOL_ID

### S3 & CloudFront
- **S3 Bucket:** $UI_BUCKET
- **CloudFront URL:** $CLOUDFRONT_URL

## Configuration Files Created

1. **Environment File:** $ENV_FILE
2. **JavaScript Config:** $CONFIG_JS (if HTML version)

## Testing Checklist

- [ ] Open frontend URL in browser
- [ ] Verify AWS Lex connection message
- [ ] Send test message: "I need access to HR Analyst"
- [ ] Verify bot response with fulfillment
- [ ] Check CloudWatch logs for Lambda invocations
- [ ] Verify DynamoDB table has conversation records

## Troubleshooting

If deployment fails:

1. **Check AWS Credentials**
   \`\`\`bash
   aws sts get-caller-identity
   \`\`\`

2. **Verify CloudFormation Stack**
   \`\`\`bash
   aws cloudformation describe-stack-resources --stack-name $STACK_NAME --region $AWS_REGION
   \`\`\`

3. **Check Cognito Pool**
   \`\`\`bash
   aws cognito-identity describe-identity-pool --identity-pool-id $COGNITO_POOL_ID --region $AWS_REGION
   \`\`\`

4. **Test Lex Bot**
   \`\`\`bash
   aws lexv2-runtime recognize-text \
     --bot-id $LEX_BOT_ID \
     --bot-alias-id $ALIAS_ID \
     --locale-id en_US \
     --session-id test-session \
     --text "I need access to HR Analyst" \
     --region $AWS_REGION
   \`\`\`

## Next Steps

1. Open the frontend URL in a browser
2. Test bot interactions
3. Check CloudWatch logs: \`aws logs tail /aws/lambda/LexFulfillmentFunction --follow\`
4. Monitor in AWS console for errors

EOF

echo -e "${GREEN}✓ Created deployment report: $REPORT_FILE${NC}"

# Final Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}Configuration Summary:${NC}"
echo "  Region: $AWS_REGION"
echo "  Lex Bot: $LEX_BOT_ID"
echo "  Lex Alias: $ALIAS_ID"
echo "  Cognito Pool: $COGNITO_POOL_ID"
echo "  S3 Bucket: $UI_BUCKET"

if [ -n "$CLOUDFRONT_URL" ]; then
    echo -e "\n${GREEN}Frontend URL:${NC}"
    echo "  $CLOUDFRONT_URL"
fi

echo -e "\n${YELLOW}Test the deployment:${NC}"
echo "  1. Open the frontend URL"
echo "  2. Say: 'I need access to HR Analyst'"
echo "  3. Check CloudWatch logs"

echo -e "\n${YELLOW}Environment files created:${NC}"
echo "  - $ENV_FILE"
if [ -f "$CONFIG_JS" ]; then
    echo "  - $CONFIG_JS"
fi

echo -e "\n${BLUE}For detailed instructions, see:${NC}"
echo "  - LEX_INTEGRATION_GUIDE.md"
echo "  - DEPLOYMENT_REPORT.md"

echo ""
