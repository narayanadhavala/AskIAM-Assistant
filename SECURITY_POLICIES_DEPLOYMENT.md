# AskIAM AWS Security Policies & Deployment Guide

## Table of Contents
1. [Security Policies](#security-policies)
2. [Deployment Commands](#deployment-commands)
3. [Git to AWS Deployment Pipeline](#git-to-aws-deployment-pipeline)
4. [Security Compliance](#security-compliance)

---

## Security Policies

### Policy 1: Backend Developer Policy (ask-iam-dev)

**File**: `infrastructure/iam-roles/backend-developer-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaFunctionManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "lambda:InvokeFunction",
        "lambda:CreateEventSourceMapping",
        "lambda:DeleteEventSourceMapping",
        "lambda:GetEventSourceMapping",
        "lambda:UpdateEventSourceMapping"
      ],
      "Resource": "arn:aws:lambda:*:*:function:ask-iam-*"
    },
    {
      "Sid": "IAMPassRoleForLambda",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/ask-iam-lambda-execution-role",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    },
    {
      "Sid": "RDSAccess",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBClusterSnapshots",
        "rds-db:connect"
      ],
      "Resource": [
        "arn:aws:rds:*:*:db:ask-iam-*",
        "arn:aws:rds-db:*:*:dbuser:*/*"
      ]
    },
    {
      "Sid": "LexBotAccess",
      "Effect": "Allow",
      "Action": [
        "lex:RecognizeText",
        "lex:PostText",
        "lex:GetBot",
        "lex:GetBots",
        "lex:ListBots",
        "lex:GetBotAlias",
        "lex:GetBotAliases",
        "lex:GetIntent",
        "lex:GetIntents",
        "lex:GetSlotType",
        "lex:GetSlotTypes"
      ],
      "Resource": "arn:aws:lex:*:*:bot-alias/AskIAMBot/*"
    },
    {
      "Sid": "APIGatewayLimited",
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST",
        "apigateway:PUT",
        "apigateway:PATCH",
        "apigateway:DELETE"
      ],
      "Resource": [
        "arn:aws:apigateway:*::/restapis/*/resources/*",
        "arn:aws:apigateway:*::/restapis/*/methods/*",
        "arn:aws:apigateway:*::/restapis/*/stages/*"
      ]
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/ask-iam-*"
    },
    {
      "Sid": "SecretsManagerReadWrite",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:ask-iam/*"
    },
    {
      "Sid": "ParameterStoreRead",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:DescribeParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/ask-iam/*"
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Sid": "XRayTracing",
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyIAMChanges",
      "Effect": "Deny",
      "Action": [
        "iam:*",
        "organizations:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyInfrastructureChanges",
      "Effect": "Deny",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:ModifySecurityGroupRules",
        "rds:CreateDBInstance",
        "rds:DeleteDBInstance",
        "rds:ModifyDBInstance",
        "rds:RebootDBInstance"
      ],
      "Resource": "*"
    }
  ]
}
```

### Policy 2: Infrastructure Developer Policy (dev-2-infra)

**File**: `infrastructure/iam-roles/infra-developer-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy",
        "iam:UpdateRole",
        "iam:GetRole",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:PassRole",
        "iam:DeleteRolePolicy",
        "iam:DetachRolePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicies",
        "iam:GetRolePolicy"
      ],
      "Resource": [
        "arn:aws:iam::*:role/ask-iam-*",
        "arn:aws:iam::*:policy/ask-iam-*"
      ]
    },
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:ModifySubnetAttribute",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:DescribeRouteTables",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:DescribeAddresses",
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:DescribeNatGateways",
        "ec2:DescribeNetworkInterfaces"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecurityGroupManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:ModifySecurityGroupRules",
        "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
        "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
        "ec2:TagResource",
        "ec2:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSManagement",
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBInstance",
        "rds:DeleteDBInstance",
        "rds:ModifyDBInstance",
        "rds:RebootDBInstance",
        "rds:RestoreDBInstanceFromDBSnapshot",
        "rds:CreateDBSnapshot",
        "rds:DeleteDBSnapshot",
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBParameterGroups",
        "rds:CreateDBCluster",
        "rds:DeleteDBCluster",
        "rds:ModifyDBCluster",
        "rds:CreateDBClusterSnapshot",
        "rds:DescribeDBEngineVersions",
        "rds:CreateDBSubnetGroup",
        "rds:DescribeDBSubnetGroups",
        "rds:DeleteDBSubnetGroup",
        "rds:ListTagsForResource",
        "rds:AddTagsToResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "OpenSearchServerlessManagement",
      "Effect": "Allow",
      "Action": [
        "aoss:CreateCollection",
        "aoss:DeleteCollection",
        "aoss:DescribeCollection",
        "aoss:ListCollections",
        "aoss:UpdateCollection",
        "aoss:TagResource",
        "aoss:UntagResource",
        "aoss:ListTagsForResource",
        "aoss:CreateSecurityPolicy",
        "aoss:DeleteSecurityPolicy",
        "aoss:GetSecurityPolicy",
        "aoss:ListSecurityPolicies",
        "aoss:CreateAccessPolicy",
        "aoss:DeleteAccessPolicy",
        "aoss:GetAccessPolicy",
        "aoss:ListAccessPolicies",
        "aoss:BatchGetCollection",
        "aoss:CreateLifecyclePolicy",
        "aoss:GetLifecyclePolicy",
        "aoss:ListLifecyclePolicies",
        "aoss:UpdateLifecyclePolicy",
        "aoss:DeleteLifecyclePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchManagement",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DeleteLogGroup",
        "logs:DeleteLogStream",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:PutRetentionPolicy",
        "logs:TagLogGroup",
        "logs:UntagLogGroup",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:CreateLogDeliveryConfiguration",
        "logs:DeleteLogDeliveryConfiguration",
        "logs:GetQueryResults",
        "logs:StopQuery",
        "logs:StartQuery"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManagerManagement",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:UpdateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:ListSecrets",
        "secretsmanager:RotateSecret",
        "secretsmanager:TagResource",
        "secretsmanager:UntagResource",
        "secretsmanager:ListSecretVersionIds",
        "secretsmanager:RestoreSecret",
        "secretsmanager:PutSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:ask-iam/*"
    },
    {
      "Sid": "ParameterStoreManagement",
      "Effect": "Allow",
      "Action": [
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:DescribeParameters",
        "ssm:DeleteParameter",
        "ssm:GetParametersByPath",
        "ssm:AddTagsToResource",
        "ssm:RemoveTagsFromResource",
        "ssm:ListTagsForResource",
        "ssm:LabelParameterVersion"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/ask-iam/*"
    },
    {
      "Sid": "CloudTrailAuditLogging",
      "Effect": "Allow",
      "Action": [
        "cloudtrail:CreateTrail",
        "cloudtrail:DeleteTrail",
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:StartLogging",
        "cloudtrail:StopLogging",
        "cloudtrail:UpdateTrail",
        "cloudtrail:PutEventSelectors",
        "cloudtrail:GetEventSelectors",
        "cloudtrail:ListTrails"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudFormationManagement",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:UpdateStack",
        "cloudformation:ValidateTemplate",
        "cloudformation:ListStackResources",
        "cloudformation:CreateChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:ListChangeSets"
      ],
      "Resource": "arn:aws:cloudformation:*:*:stack/ask-iam-*"
    },
    {
      "Sid": "ElastiCacheManagement",
      "Effect": "Allow",
      "Action": [
        "elasticache:CreateCacheCluster",
        "elasticache:DeleteCacheCluster",
        "elasticache:DescribeCacheClusters",
        "elasticache:ModifyCacheCluster",
        "elasticache:CreateCacheSubnetGroup",
        "elasticache:DeleteCacheSubnetGroup",
        "elasticache:DescribeCacheSubnetGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyUserManagement",
      "Effect": "Deny",
      "Action": [
        "iam:DeleteUser",
        "iam:DeleteRole",
        "iam:DeleteAccessKey",
        "iam:CreateAccessKey",
        "iam:CreateUser",
        "iam:AttachUserPolicy",
        "iam:PutUserPolicy",
        "iam:CreateLoginProfile"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyBillingAndOrganizations",
      "Effect": "Deny",
      "Action": [
        "organizations:*",
        "billing:*",
        "ce:*",
        "aws-portal:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Policy 3: Lambda Execution Role Policy

**File**: `infrastructure/iam-roles/lambda-execution-role.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogsBasic",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/ask-iam-*"
    },
    {
      "Sid": "VPCExecution",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSAccess",
      "Effect": "Allow",
      "Action": [
        "rds-db:connect"
      ],
      "Resource": "arn:aws:rds-db:*:*:dbuser:*/*"
    },
    {
      "Sid": "SecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:ask-iam/*"
    },
    {
      "Sid": "ParameterStoreAccess",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/ask-iam/*"
    },
    {
      "Sid": "OpenSearchAccess",
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "*"
    },
    {
      "Sid": "XRayAccess",
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Deployment Commands

### Create IAM Roles

```bash
# Set variables
ACCOUNT_ID="123456789012"  # Replace with your account ID
REGION="us-east-1"

# Create Backend Developer Role
aws iam create-role \
  --role-name ask-iam-backend-developer \
  --assume-role-policy-document file://infrastructure/iam-roles/trust-policy-dev1.json \
  --description "Backend developer role - manages Lambda, RDS, Lex, API Gateway" \
  --tags Key=Project,Value=AskIAM Key=Developer,Value=Backend

# Add inline policy to Backend Developer Role
aws iam put-role-policy \
  --role-name ask-iam-backend-developer \
  --policy-name ask-iam-backend-developer-policy \
  --policy-document file://infrastructure/iam-roles/backend-developer-policy.json

# Create Infrastructure Developer Role
aws iam create-role \
  --role-name ask-iam-infra-developer \
  --assume-role-policy-document file://infrastructure/iam-roles/trust-policy-dev2.json \
  --description "Infrastructure developer role - manages VPC, RDS, OpenSearch, CloudWatch" \
  --tags Key=Project,Value=AskIAM Key=Developer,Value=Infrastructure

# Add inline policy to Infrastructure Developer Role
aws iam put-role-policy \
  --role-name ask-iam-infra-developer \
  --policy-name ask-iam-infra-developer-policy \
  --policy-document file://infrastructure/iam-roles/infra-developer-policy.json

# Create Lambda Execution Role
aws iam create-role \
  --role-name ask-iam-lambda-execution-role \
  --assume-role-policy-document file://infrastructure/iam-roles/trust-policy-lambda.json \
  --description "Lambda execution role for AskIAM functions" \
  --tags Key=Project,Value=AskIAM Key=Service,Value=Lambda

# Add inline policy to Lambda Execution Role
aws iam put-role-policy \
  --role-name ask-iam-lambda-execution-role \
  --policy-name ask-iam-lambda-execution-policy \
  --policy-document file://infrastructure/iam-roles/lambda-execution-role.json
```

### Create Trust Policy Documents

**File**: `infrastructure/iam-roles/trust-policy-dev1.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/ask-iam-dev"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**File**: `infrastructure/iam-roles/trust-policy-dev2.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:user/dev-2-infra"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**File**: `infrastructure/iam-roles/trust-policy-lambda.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## Git to AWS Deployment Pipeline

### Full Deployment Workflow

```bash
#!/bin/bash
# File: deploy.sh

set -e  # Exit on error

# Configuration
GITHUB_REPO="https://github.com/YOUR-ORG/AskIAM-Assistant.git"
AWS_REGION="us-east-1"
ENVIRONMENT="prod"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Starting AskIAM Deployment${NC}"

# Step 1: Clone/Update Repository
echo -e "${BLUE}[1/6] Updating Git repository...${NC}"
if [ -d "AskIAM-Assistant" ]; then
    cd AskIAM-Assistant
    git fetch origin
    git checkout main
    git pull origin main
else
    git clone $GITHUB_REPO
    cd AskIAM-Assistant
fi

# Step 2: Infrastructure Deployment (Dev-2)
echo -e "${BLUE}[2/6] Deploying Infrastructure...${NC}"
cd infrastructure
aws cloudformation create-stack \
    --stack-name ask-iam-infra-$ENVIRONMENT \
    --template-body file://template-infrastructure.yaml \
    --parameters \
        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        ParameterKey=Region,ParameterValue=$AWS_REGION \
    --profile dev-2-infra \
    --region $AWS_REGION

# Wait for stack to complete
echo "Waiting for infrastructure stack to complete..."
aws cloudformation wait stack-create-complete \
    --stack-name ask-iam-infra-$ENVIRONMENT \
    --profile dev-2-infra \
    --region $AWS_REGION

cd ..

# Step 3: Backend Deployment (Dev-1)
echo -e "${BLUE}[3/6] Packaging backend functions...${NC}"
cd backend

# Deploy each Lambda function
for func_dir in orchestrator entity-extractor rag-validator mcp-validator audit-logger; do
    echo "Deploying $func_dir..."
    cd $func_dir
    
    # Create deployment package
    zip -r lambda_package.zip lambda_function.py
    
    # Update Lambda function
    aws lambda update-function-code \
        --function-name ask-iam-$func_dir \
        --zip-file fileb://lambda_package.zip \
        --profile ask-iam-dev \
        --region $AWS_REGION
    
    # Wait for update
    aws lambda wait function-updated \
        --function-name ask-iam-$func_dir \
        --profile ask-iam-dev \
        --region $AWS_REGION
    
    rm lambda_package.zip
    cd ..
done

cd ..

# Step 4: Database Setup (Dev-2)
echo -e "${BLUE}[4/6] Setting up database...${NC}"
cd database

# Run migrations if needed
if [ -f "migrations/01_initial_schema.sql" ]; then
    # Get RDS endpoint from Parameter Store
    RDS_ENDPOINT=$(aws ssm get-parameter \
        --name /ask-iam/$ENVIRONMENT/rds/endpoint \
        --query 'Parameter.Value' \
        --output text \
        --profile dev-2-infra)
    
    echo "Running database migrations on $RDS_ENDPOINT..."
    # Note: This requires database client installed locally
    # psql -h $RDS_ENDPOINT -U postgres -d askiam_db -f migrations/01_initial_schema.sql
fi

cd ..

# Step 5: Verification Tests
echo -e "${BLUE}[5/6] Running verification tests...${NC}"

# Test Lambda function
echo "Testing orchestrator Lambda..."
aws lambda invoke \
    --function-name ask-iam-orchestrator \
    --payload file://tests/payload.json \
    --profile ask-iam-dev \
    response.json

if grep -q "statusCode.*200" response.json; then
    echo -e "${GREEN}Lambda test passed${NC}"
else
    echo -e "${RED}Lambda test failed${NC}"
    cat response.json
    exit 1
fi

rm response.json

# Step 6: Deployment Summary
echo -e "${BLUE}[6/6] Deployment Summary${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"

# Get deployment info
echo ""
echo "Infrastructure Stack Status:"
aws cloudformation describe-stacks \
    --stack-name ask-iam-infra-$ENVIRONMENT \
    --query 'Stacks[0].StackStatus' \
    --profile dev-2-infra \
    --region $AWS_REGION

echo ""
echo "Lambda Functions Deployed:"
aws lambda list-functions \
    --query 'Functions[?starts_with(FunctionName, `ask-iam-`)].FunctionName' \
    --profile ask-iam-dev \
    --region $AWS_REGION \
    --output table

echo ""
echo -e "${GREEN}Ready for testing!${NC}"
```

### Run Deployment

```bash
# Make script executable
chmod +x deploy.sh

# Execute deployment
./deploy.sh

# If using AWS Profiles:
export AWS_PROFILE=dev-2-infra  # For infrastructure work
export AWS_PROFILE=ask-iam-dev   # For backend work
```

---

## Security Compliance

### Compliance Checklist

```bash
# Security Audit Script
# File: scripts/security-audit.sh

#!/bin/bash

echo "AskIAM Security Audit"
echo "===================="

# Check 1: MFA enabled on IAM users
echo ""
echo "Check 1: MFA Status on IAM Users"
aws iam get-credential-report --output text | \
    grep -E "(ask-iam-dev|dev-2-infra)" | \
    awk -F',' '{print $1, "MFA:", $8}'

# Check 2: Access keys age
echo ""
echo "Check 2: Access Key Age (should be < 90 days)"
aws iam get-access-key-last-used \
    --access-key-id AKIAIOSFODNN7EXAMPLE \
    --query 'AccessKeyLastUsed.LastUsedDate' \
    --output text

# Check 3: CloudTrail enabled
echo ""
echo "Check 3: CloudTrail Logging Status"
aws cloudtrail describe-trails --query 'trailList[].IsMultiRegionTrail' --output table

# Check 4: S3 Bucket Encryption
echo ""
echo "Check 4: S3 Bucket Encryption"
aws s3api get-bucket-encryption --bucket ask-iam-bucket 2>/dev/null || echo "No encryption policy found"

# Check 5: RDS Encryption
echo ""
echo "Check 5: RDS Database Encryption"
aws rds describe-db-instances \
    --query 'DBInstances[].{Name:DBInstanceIdentifier,Encrypted:StorageEncrypted}' \
    --output table

# Check 6: Security Group Ingress Rules
echo ""
echo "Check 6: Security Group Ingress Rules"
aws ec2 describe-security-groups \
    --filters "Name=tag:Project,Values=AskIAM" \
    --query 'SecurityGroups[].{GroupId:GroupId,Ingress:IpPermissions}' \
    --output json | jq '.[] | .Ingress[] | {Protocol:.IpProtocol, FromPort, ToPort}'

# Check 7: Secrets with Rotation
echo ""
echo "Check 7: Secrets Manager Rotation Status"
aws secretsmanager list-secrets \
    --query 'SecretList[].{Name:Name,RotationEnabled:RotationEnabled}' \
    --output table
```

### Automated Compliance Enforcement

```bash
# File: scripts/enforce-security.sh

#!/bin/bash

# Force MFA for IAM users
echo "Enforcing MFA requirement..."

# Create deny policy for users without MFA
aws iam put-user-policy \
    --user-name ask-iam-dev \
    --policy-name DenyAllExceptListUsersIfMFAIsActive \
    --policy-document file://policies/deny-without-mfa.json

# Enable encryption on RDS instances
echo "Enforcing RDS encryption..."
aws rds modify-db-instance \
    --db-instance-identifier ask-iam-db \
    --storage-encrypted \
    --apply-immediately

# Enable CloudTrail logging
echo "Enforcing CloudTrail logging..."
aws cloudtrail start-logging \
    --name ask-iam-trail

# Enable CloudWatch detailed monitoring
echo "Enabling detailed CloudWatch monitoring..."
aws monitoring put-metric-alarm \
    --alarm-name ask-iam-security-alarm \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:ask-iam-alerts

echo "Security enforcement complete!"
```

---

## Summary

### Before Deployment
- [ ] Both developers have AWS access
- [ ] GitHub repository created and configured
- [ ] Security policies reviewed and approved
- [ ] IAM roles created with proper permissions
- [ ] MFA enabled on all user accounts
- [ ] AWS CLI configured locally

### Deployment Steps
1. Create IAM roles and policies
2. Push code to GitHub
3. Run infrastructure deployment (Dev-2)
4. Run backend deployment (Dev-1)
5. Setup databases and data
6. Run tests and verification
7. Enable monitoring and alerts

### Post-Deployment
- [ ] CloudWatch dashboards created
- [ ] Alarms configured
- [ ] Logging enabled
- [ ] Regular backups scheduled
- [ ] Security audit completed
- [ ] Team trained on operations

---

**Document Version**: 1.0
**Last Updated**: [Date]
**Created By**: AWS Security Team
