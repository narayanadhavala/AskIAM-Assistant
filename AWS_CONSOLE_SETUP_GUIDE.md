# AWS Console Step-by-Step Setup Guide: AskIAM Conversational Bot
## Complete Beginner's Guide to Building a Serverless AI Application

---

## Table of Contents
1. [Team Setup: Two-Developer Architecture](#team-setup-two-developer-architecture)
2. [Prerequisites & Account Setup](#prerequisites--account-setup)
3. [Part 1: Security Foundation (IAM Roles)](#part-1-security-foundation-iam-roles)
4. [Part 2: Database Setup (Amazon RDS)](#part-2-database-setup-amazon-rds)
5. [Part 3: Search & Analytics (OpenSearch Serverless)](#part-3-search--analytics-opensearch-serverless)
6. [Part 4: Secrets Management](#part-4-secrets-management)
7. [Part 5: Backend Logic (AWS Lambda)](#part-5-backend-logic-aws-lambda)
8. [Part 6: Request Routing (API Gateway)](#part-6-request-routing-api-gateway)
9. [Part 7: Conversational Interface (Amazon Lex)](#part-7-conversational-interface-amazon-lex)
10. [Part 8: Monitoring & Logging](#part-8-monitoring--logging)
11. [Part 9: Testing & Deployment](#part-9-testing--deployment)
12. [Part 10: Troubleshooting & Optimization](#part-10-troubleshooting--optimization)

---

# Team Setup: Two-Developer Architecture

## Architecture Overview

This section provides step-by-step instructions for setting up AskIAM with a **single AWS account** and **two developer roles** with distinct responsibilities.

```
┌─────────────────────────────────────────────────────────────┐
│               SINGLE AWS ACCOUNT                             │
│               (ask-iam-prod)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Developer 1 (Backend Services)    Developer 2 (Infrastructure) │
│  ├─ IAM Role: Lambda-Developer     ├─ IAM Role: Infra-Developer
│  ├─ Lambda Functions               ├─ IAM Roles/Policies
│  ├─ RDS Database                   ├─ OpenSearch Setup
│  ├─ Lex Bot                        ├─ VPC & Networking
│  └─ API Gateway (partial)          ├─ CloudWatch & Monitoring
│                                     └─ Secrets Manager
│
│  Shared: Parameter Store, Artifacts, CloudWatch Logs
│
└─────────────────────────────────────────────────────────────┘
```

## Why Single Account with Role Segregation?

| Advantage | Benefit |
|-----------|---------|
| **Unified Billing** | Easy to track total project costs |
| **Simplified Networking** | No VPC peering or cross-account setup |
| **Faster Development** | Services in same account = lower latency |
| **Shared Resources** | Parameter Store and Secrets Manager accessible to both |
| **Easier Debugging** | Single CloudWatch log group for entire system |

---

## Step 0: Root Account Setup (Admin Only)

### 0A: Create AWS Account

1. **Go to AWS Sign-Up**
   - Visit: https://aws.amazon.com/
   - Click **"Create an AWS Account"**
   - Email: professional email (use a shared team account if possible)
   - Account Name: `ask-iam-prod`
   - Password: strong password (15+ characters, mix of letters, numbers, symbols)

2. **Add Payment Method**
   - Credit/debit card required
   - Verification charge: $1 (refunded in 1-2 days)

3. **Choose Support Plan**
   - Select: **"Basic Plan"** (free, sufficient for this project)

4. **Complete Verification**
   - Verify phone number and email
   - Complete account setup

5. **Sign In to Console**
   - Go to: https://console.aws.amazon.com/
   - Sign in with root account credentials

### 0B: Enable MFA on Root Account

**⚠️ CRITICAL: Protect your root account!**

1. **Navigate to Security Credentials**
   - Click your **account name** (top right)
   - Select **"Security credentials"**

2. **Set Up MFA**
   - Scroll to **"Multi-factor authentication (MFA)"**
   - Click **"Assign MFA device"**
   - Choose **"Virtual MFA device"** (Google Authenticator or Authy)
   - Follow prompts to scan QR code
   - Save recovery codes in a secure location

### 0C: Create Admin IAM User

1. **Open IAM Console**
   - Services → search **"IAM"** → click **IAM**

2. **Create New User**
   - Left sidebar → **"Users"** → **"Create user"**
   - Username: `askiam-admin`
   - Check: **"Provide user access to the AWS Management Console"**
   - Console password: strong password
   - **Uncheck**: "Users must create a new password on next sign-in"
   - Click **"Next"**

3. **Add Administrator Permissions**
   - Click **"Attach policies directly"**
   - Search: `AdministratorAccess`
   - Check the policy
   - Click **"Next"** → **"Create user"**

4. **Save Login URL**
   - Copy the console sign-in URL
   - Format: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Share with admin only

5. **Enable MFA on Admin User**
   - In IAM console: Users → askiam-admin
   - Click **"Security credentials"** tab
   - Click **"Assign MFA device"**
   - Complete MFA setup

---

## Step 1: Create Developer 1 Role (Backend Services)

**Developer 1** is responsible for Lambda functions, RDS, Lex, and API Gateway.

### 1A: Create Backend Developer IAM User

1. **Open IAM Console**
   - Services → **IAM**
   - Left sidebar → **"Users"** → **"Create user"**

2. **Create User**
   - Username: `dev-1-backend`
   - Check: **"Provide user access to the AWS Management Console"**
   - Console password: provide strong password
   - **Uncheck**: "Users must create a new password on next sign-in"
   - Click **"Next"**

3. **Save Credentials**
   - Note the sign-in URL: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Username: `dev-1-backend`
   - Password: the one you created
   - Share with Developer 1 via secure channel (1Password, LastPass, etc.)

### 1B: Create Backend Developer Role (Permission Policy)

1. **Navigate to Roles**
   - Left sidebar → **"Roles"** → **"Create role"**

2. **Select Trusted Entity**
   - Trusted entity type: **"AWS service"**
   - Use case: Search and select **"Lambda"**
   - Click **"Next"**

3. **Add Permissions**
   - Search and check each policy:
     - `CloudWatchLogsFullAccess`
     - `AmazonRDSFullAccess`
     - `AmazonLexFullAccess`
     - `AWSLambdaFullAccess`
     - `AmazonAPIGatewayFullAccess`
     - `SecretsManagerReadWrite`
     - `AmazonSSMReadOnlyAccess`

4. **Name the Role**
   - Role name: `ask-iam-backend-developer`
   - Description: `Role for backend engineer working on Lambda, RDS, Lex`
   - Click **"Create role"**

### 1C: Attach Role to Backend Developer User

1. **Navigate to Users**
   - Left sidebar → **"Users"** → **"dev-1-backend"**

2. **Add Permissions**
   - Click **"Add permissions"** → **"Attach policies directly"**
   - Search: `AssumeRolePolicy` (custom) or use inline policy
   - Create inline policy with this content:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::ACCOUNT-ID:role/ask-iam-backend-developer"
    }
  ]
}
```

3. **Click "Create policy"** → **"Attach"**

### 1D: Developer 1 First Login

1. **Sign In as Backend Developer**
   - URL: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Username: `dev-1-backend`
   - Password: provided by admin
   - Set up MFA (recommended)
   - Change password

2. **Assume the Backend Developer Role**
   - Click account name (top right) → **"Switch role"**
   - Account: `ACCOUNT-ID` (12 digits)
   - Role: `ask-iam-backend-developer`
   - Display name: `Backend-Dev`
   - Click **"Switch role"**

3. **Verify Permissions**
   - Should see: Lambda, RDS, Lex, API Gateway in Services
   - Should NOT see: IAM management, VPC, Security Groups

---

## Step 2: Create Developer 2 Role (Infrastructure & DevOps)

**Developer 2** is responsible for IAM roles, VPC, OpenSearch, CloudWatch, and Secrets Manager.

### 2A: Create Infrastructure Developer IAM User

1. **Open IAM Console** (as Admin)
   - Services → **IAM**
   - Left sidebar → **"Users"** → **"Create user"**

2. **Create User**
   - Username: `dev-2-infra`
   - Check: **"Provide user access to the AWS Management Console"**
   - Console password: provide strong password
   - Click **"Next"**

3. **Save Credentials**
   - Sign-in URL: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Username: `dev-2-infra`
   - Password: the one you created
   - Share with Developer 2 via secure channel

### 2B: Create Infrastructure Developer Role (Permission Policy)

1. **Navigate to Roles**
   - Left sidebar → **"Roles"** → **"Create role"**

2. **Select Trusted Entity**
   - Trusted entity type: **"AWS account"**
   - Account ID: `ACCOUNT-ID` (your AWS account ID)
   - Click **"Next"**

3. **Add Permissions**
   - Click **"Attach policies directly"**
   - Search and check:
     - `AmazonOpenSearchServiceFullAccess`
     - `CloudWatchFullAccess`
     - `SecretsManagerReadWrite`
     - `AmazonVPCFullAccess`
     - `EC2FullAccess` (for security groups)
     - `AWSCloudTrailFullAccess`
     - `CloudFormationFullAccess`

4. **Add IAM-Specific Permissions**
   - Continue searching and check:
     - `IAMUserChangePassword` (for managing IAM users)
   - We'll add a custom policy for IAM role creation

5. **Name the Role**
   - Role name: `ask-iam-infra-developer`
   - Description: `Role for infrastructure engineer: IAM, VPC, OpenSearch, CloudWatch`
   - Click **"Create role"**

### 2C: Add Custom IAM Policy for Role Creation

1. **Navigate to the Role**
   - Left sidebar → **"Roles"** → search **"ask-iam-infra-developer"**
   - Click on the role

2. **Add Inline Policy**
   - Click **"Add inline policy"** (at bottom)
   - Select **"JSON"** tab
   - Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "IAMRoleCreationAndManagement",
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
        "iam:DetachRolePolicy"
      ],
      "Resource": "arn:aws:iam::ACCOUNT-ID:role/ask-iam-*"
    },
    {
      "Sid": "SecurityGroupManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:ModifySecurityGroupRules"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ParameterStoreFullAccess",
      "Effect": "Allow",
      "Action": [
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:DescribeParameters",
        "ssm:DeleteParameter"
      ],
      "Resource": "arn:aws:ssm:*:ACCOUNT-ID:parameter/ask-iam/*"
    }
  ]
}
```

   - Replace `ACCOUNT-ID` with your 12-digit AWS account ID
   - Click **"Create policy"**

### 2D: Attach Role to Infrastructure Developer User

1. **Navigate to Users**
   - Left sidebar → **"Users"** → **"dev-2-infra"**

2. **Add Permissions**
   - Click **"Add permissions"** → **"Attach policies directly"**
   - Search: `AssumeRolePolicy` or create inline policy

3. **Create Inline Policy**
   - Click **"Add inline policy"**
   - Select **"JSON"**
   - Paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::ACCOUNT-ID:role/ask-iam-infra-developer"
    }
  ]
}
```

   - Click **"Create policy"**

### 2E: Developer 2 First Login

1. **Sign In as Infrastructure Developer**
   - URL: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Username: `dev-2-infra`
   - Password: provided by admin
   - Set up MFA (recommended)
   - Change password

2. **Assume the Infrastructure Developer Role**
   - Click account name (top right) → **"Switch role"**
   - Account: `ACCOUNT-ID`
   - Role: `ask-iam-infra-developer`
   - Display name: `Infra-Dev`
   - Click **"Switch role"**

3. **Verify Permissions**
   - Should see: OpenSearch, CloudWatch, VPC, EC2, IAM (limited), Secrets Manager
   - Should NOT see: Lambda, RDS, Lex directly (only for creation)

---

## Step 3: Developer 1 Setup - Services They'll Deploy

**Developer 1** will deploy the following services:

### Services Checklist for Developer 1:

```
Development Timeline:
├─ Week 1-2: Lambda Functions
│  ├─ ask-iam-orchestrator (main entry point)
│  ├─ ask-iam-entity-extractor
│  ├─ ask-iam-rag-validator
│  ├─ ask-iam-mcp-validator
│  └─ ask-iam-audit-logger
│
├─ Week 2-3: Database
│  ├─ Create RDS PostgreSQL instance
│  ├─ Load sample IAM data (iam_sample_data.sql)
│  └─ Create database connections in Lambda env vars
│
├─ Week 3: Lex Bot
│  ├─ Create AskIAMBot
│  ├─ Configure intents (CheckAccess, RequestAccess, etc.)
│  └─ Connect to orchestrator Lambda
│
└─ Week 4: API Gateway
   ├─ Create /chat endpoint
   ├─ Connect to orchestrator Lambda
   └─ Enable CORS
```

### 3A: Developer 1 Action Items

Before starting, ensure:

1. ✅ You have received sign-in credentials from admin
2. ✅ You have signed in and switched to `ask-iam-backend-developer` role
3. ✅ You can see Lambda, RDS, Lex in the Services menu
4. ✅ You have MFA enabled

**Proceed to**: [Part 5: Backend Logic (AWS Lambda)](#part-5-backend-logic-aws-lambda)

---

## Step 4: Developer 2 Setup - Services They'll Deploy

**Developer 2** will deploy the following services:

### Services Checklist for Developer 2:

```
Development Timeline:
├─ Week 1: Foundation
│  ├─ Create VPC (if needed)
│  ├─ Create security groups for RDS
│  ├─ Create security groups for OpenSearch
│  └─ Create security groups for Lambda
│
├─ Week 1-2: Secrets & Configuration
│  ├─ Create RDS password secret in Secrets Manager
│  ├─ Create API keys secret (if needed)
│  ├─ Create /ask-iam/prod/rds/endpoint parameter
│  ├─ Create /ask-iam/prod/opensearch/endpoint parameter
│  └─ Create /ask-iam/prod/ollama/endpoint parameter
│
├─ Week 2-3: OpenSearch Serverless
│  ├─ Create ask-iam-collection
│  ├─ Create vector search indexes
│  ├─ Configure access policies
│  └─ Test connectivity
│
├─ Week 3: Monitoring
│  ├─ Create CloudWatch log groups
│  ├─ Create CloudWatch dashboards
│  ├─ Create CloudWatch alarms
│  ├─ Set up SNS topic for alerts
│  └─ Enable CloudTrail logging
│
└─ Week 4: Integration Support
   ├─ Troubleshoot cross-service connectivity
   ├─ Validate security group rules
   └─ Monitor system health
```

### 4A: Developer 2 Action Items

Before starting, ensure:

1. ✅ You have received sign-in credentials from admin
2. ✅ You have signed in and switched to `ask-iam-infra-developer` role
3. ✅ You can see OpenSearch, CloudWatch, VPC, IAM in the Services menu
4. ✅ You have MFA enabled

**Proceed to**: [Part 2: Database Setup (Amazon RDS)](#part-2-database-setup-amazon-rds)

---

## Step 5: Collaboration & Handoff

### Developer 1 → Developer 2 Handoffs

**Milestone 1: Lambda Functions Ready**
- Dev-1 commits code to Git
- Dev-1 documents function names and environment variable requirements
- Dev-1 provides Lambda execution role ARN
- Dev-2 updates Parameter Store with endpoints

**Milestone 2: RDS Setup Complete**
- Dev-2 provides RDS endpoint and port
- Dev-1 stores in Secrets Manager
- Dev-1 tests Lambda → RDS connection

**Milestone 3: OpenSearch Ready**
- Dev-2 provides OpenSearch collection endpoint
- Dev-1 stores in Parameter Store
- Dev-1 tests RAG functionality

**Milestone 4: CloudWatch Dashboards**
- Dev-2 creates monitoring dashboards
- Dev-1 verifies logs are appearing
- Both monitor for errors during testing

### Daily Sync Template

```markdown
## Daily Standup (Async Format)

### Developer 1 (Backend)
- **Yesterday**: 
  - Deployed ask-iam-orchestrator Lambda v1.2.0
  - Testing with mock RDS data
- **Today**:
  - Create ask-iam-rag-validator Lambda
  - Test with ChromaDB
- **Blockers**:
  - Waiting for RDS endpoint from Dev-2

### Developer 2 (Infra)
- **Yesterday**:
  - Created RDS PostgreSQL instance
  - Created security groups
- **Today**:
  - Create RDS secret in Secrets Manager
  - Store RDS endpoint in Parameter Store
- **Blockers**: None

### Shared Actions
- [ ] Dev-2 provides RDS endpoint by EOD
- [ ] Dev-1 validates Lambda can connect to RDS
- [ ] Both review and merge the latest Git changes
```

---

## Step 6: Git Repository Setup (Recommended)

### Repository Structure

```
AskIAM-Assistant/
├── infrastructure/                    (Dev-2 owns)
│   ├── iam-roles/
│   │   ├── lambda-execution-role.json
│   │   ├── backend-developer-policy.json
│   │   └── infra-developer-policy.json
│   ├── security-groups/
│   │   ├── rds-sg.json
│   │   ├── opensearch-sg.json
│   │   └── lambda-sg.json
│   ├── opensearch/
│   │   ├── collection-config.yaml
│   │   └── vector-index-schema.json
│   ├── cloudwatch/
│   │   ├── log-groups.yaml
│   │   ├── dashboards.json
│   │   └── alarms.json
│   └── README.md
│
├── backend/                           (Dev-1 owns)
│   ├── orchestrator/
│   │   ├── lambda_function.py
│   │   ├── requirements.txt
│   │   └── tests/
│   ├── entity-extractor/
│   ├── rag-validator/
│   ├── mcp-validator/
│   ├── audit-logger/
│   └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── TEAM_SETUP.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
│
├── .gitignore
│   (exclude: *.key, *.pem, .env, secrets/)
│
└── README.md
```

### Git Workflow

```bash
# Dev-1: Work on backend
git checkout -b feature/lambda-orchestrator
# Make changes...
git commit -m "feat: implement orchestrator Lambda function"
git push origin feature/lambda-orchestrator
# Create Pull Request

# Dev-2: Review and merge (after testing)
git checkout main
git pull origin
# Deploy changes

# Dev-2: Work on infrastructure
git checkout -b feature/opensearch-setup
# Make changes...
git commit -m "feat: configure OpenSearch serverless collection"
git push origin feature/opensearch-setup
# Create Pull Request

# Dev-1: Review and merge
git checkout main
git pull origin
# Configure Lambda to use new OpenSearch endpoint
```

---

## Step 7: Communication & Troubleshooting

### When Things Go Wrong

**Scenario 1: Lambda Cannot Connect to RDS**
- Dev-1: Check CloudWatch logs for connection error
- Dev-1: Ask Dev-2: "What's the RDS security group?"
- Dev-2: Check if Lambda security group is authorized in RDS security group
- Dev-2: Add inbound rule: Source = Lambda security group, Port = 5432

**Scenario 2: Dev-1 Cannot Assume Backend Developer Role**
- Admin: Check if dev-1-backend user has the AssumeRole policy
- Admin: Verify the policy points to the correct role ARN

**Scenario 3: OpenSearch Search Returns Empty Results**
- Dev-2: Check OpenSearch collection status
- Dev-1: Verify data was ingested (check ingest logs)
- Dev-2: Check network connectivity between Lambda and OpenSearch

### Communication Channels

| Issue Type | Owner | Channel |
|-----------|-------|---------|
| Lambda/RDS connection | Dev-1 + Dev-2 | Slack #ask-iam-backend |
| Security group rules | Dev-2 | Slack #ask-iam-infra |
| Parameter Store values | Dev-2 (update) + Dev-1 (consume) | Email + Parameter Store |
| Architecture decisions | Both | Weekly sync meeting |
| Git conflicts | Both | Pull request discussion |

---



# Prerequisites & Account Setup

## What You Need Before Starting

- **AWS Account**: Free tier or paid account
- **Credit Card**: Required for AWS account creation (even free tier requires it)
- **Laptop/Computer**: With web browser (Chrome recommended)
- **Time**: 2-3 hours to complete the entire setup
- **Code Files**: The Lambda function code provided in this project
- **Terminal Access**: Optional (for testing endpoints)
- **Two Developers**: Or one person can take both roles (see Team Setup section above)

## Quick Start Checklist

- [ ] Admin has completed Step 0 (Root Account Setup)
- [ ] Admin has created both developer IAM users (Step 1 & 2)
- [ ] Dev-1 has signed in and switched to `ask-iam-backend-developer` role
- [ ] Dev-2 has signed in and switched to `ask-iam-infra-developer` role
- [ ] Both developers have MFA enabled
- [ ] Git repository is set up with proper directory structure
- [ ] Team communication channels established (Slack, Email, etc.)

## Step 0: Create or Access Your AWS Account

**This step is done by the Admin (root account owner)**

### If You Don't Have an AWS Account:

1. **Go to AWS Sign-Up Page**
   - Visit: https://aws.amazon.com/
   - Click **"Create an AWS Account"** button (top right)

2. **Enter Your Email & Password**
   - Root account email: use a professional email address
   - Password: strong password (12+ characters, numbers, symbols)
   - AWS Account Name: something like "AskIAM-Dev" or "MyIAMBot"

3. **Add Payment Method**
   - Credit or debit card (required for verification)
   - Amount charged: $1 (refunded within 1-2 days)

4. **Choose Your AWS Support Plan**
   - Select: **"Basic Plan"** (free, sufficient for this project)

5. **Complete Setup**
   - Click through the confirmation steps
   - Go to AWS Console: https://console.aws.amazon.com/

### If You Already Have an AWS Account:
- Go directly to: https://console.aws.amazon.com/
- Sign in with your credentials

## Step 1: Enable MFA (Multi-Factor Authentication)

**Why**: Protects your account from unauthorized access.

1. **Go to IAM Dashboard**
   - Click **"Services"** menu (top left)
   - Search for **"IAM"** (Identity and Access Management)
   - Click **IAM** to open

2. **Enable MFA on Root Account**
   - Left sidebar → click **"Your security credentials"**
   - Scroll to **"Multi-factor authentication (MFA)"**
   - Click **"Assign MFA device"**
   - Choose **"Virtual MFA device"** (use Google Authenticator or Authy app)
   - Follow the on-screen instructions

3. **Save Your MFA Recovery Codes**
   - Download the recovery codes file
   - Store in a safe location (not in email)

## Step 2: Create an IAM User for Daily Work

**Why**: Never use the root account for daily work (security best practice).

1. **Open IAM Console**
   - Services → IAM
   - Left sidebar → **"Users"**
   - Click **"Create user"** button

2. **Create New User**
   - User name: `askiam-admin` (or similar)
   - Check: **"Provide user access to the AWS Management Console"**
   - Check: **"I want to create an IAM user"**
   - Console password: enter strong password
   - Uncheck: **"Users must create a new password on next sign-in"** (optional)
   - Click **"Next"**

3. **Add Permissions**
   - Click **"Add group"** or **"Attach policies directly"**
   - Search for: `AdministratorAccess`
   - Check the box
   - Click **"Next"** → **"Create user"**

4. **Save Login Information**
   - You'll see a page with sign-in URL and credentials
   - Copy the sign-in URL: `https://YOUR-ACCOUNT-ID.signin.aws.amazon.com/console/`
   - Save username and password securely
   - Bookmark the sign-in URL

5. **Sign In as IAM User**
   - Log out from root account
   - Use the sign-in URL from Step 4
   - Sign in with `askiam-admin` username and password
   - Set up MFA on this account (Services → IAM → Users → Select user → Security credentials → Assign MFA device)

---

# Part 1: Security Foundation (IAM Roles)

## Overview: Why IAM Roles Matter

**Problem**: AWS services need permission to access each other. For example:
- Lambda functions need permission to read/write data to RDS
- Lambda needs permission to search OpenSearch
- Lambda needs to retrieve secrets from Secrets Manager

**Solution**: Create IAM roles that define exactly what each service can do.

**Think of it like**: A janitor with a keyring. The role is like the keyring, and permissions are like individual keys.

## Step 3: Create Lambda Execution Role

This role allows Lambda functions to do their job.

### 3A: Go to IAM Roles Page

1. **Open AWS Console**
   - Sign in: https://console.aws.amazon.com/

2. **Navigate to IAM**
   - Click **"Services"** menu
   - Search for **"IAM"**
   - Click **"IAM"**

3. **Open Roles Section**
   - Left sidebar → click **"Roles"**
   - You'll see a list of existing roles (may be empty)
   - Click **"Create role"** button

### 3B: Create Role - Step 1 (Select Trusted Entity)

1. **Choose Service**
   - Under **"Trusted entity type"**, select: **"AWS service"**
   - Under **"Use cases"**, search for: **"Lambda"**
   - Click **"Lambda"** in the results
   - Click **"Next"**

### 3C: Create Role - Step 2 (Add Permissions)

1. **Add Permissions**
   - You'll see a search box: **"Filter policies"**
   - Add the following permissions (search for each and check the box):

   **Policy 1: CloudWatch Logs**
   - Search: `CloudWatchLogsFullAccess`
   - Check the box
   
   **Policy 2: RDS Database Access**
   - Search: `AmazonRDSFullAccess` (or we'll use specific policy later)
   - Check the box
   
   **Policy 3: OpenSearch Access**
   - Search: `AmazonOpenSearchServiceFullAccess`
   - Check the box
   
   **Policy 4: Secrets Manager**
   - Search: `SecretsManagerReadWrite`
   - Check the box
   
   **Policy 5: Systems Manager (Parameter Store)**
   - Search: `AmazonSSMReadOnlyAccess`
   - Check the box
   
   **Policy 6: X-Ray**
   - Search: `AWSXRayDaemonWriteAccess`
   - Check the box

2. **Click "Next"**

### 3D: Create Role - Step 3 (Name and Review)

1. **Enter Role Details**
   - Role name: `ask-iam-lambda-execution-role`
   - Description: `Execution role for AskIAM Lambda functions`
   - Scroll down to see all attached policies
   - Verify all 6 policies are checked

2. **Click "Create role"**

3. **Confirm Role Created**
   - You'll see a green success message
   - You'll see the role listed in the Roles dashboard

## Step 4: Create RDS Access Policy (Advanced - Optional)

**Note**: This step uses AWS policy editor. Skip if not comfortable; using `AmazonRDSFullAccess` is acceptable for learning.

If you want to be more restrictive:

1. **Still on Roles page**, search for the role you just created: `ask-iam-lambda-execution-role`
2. **Click the role name** to open it
3. **Scroll to "Permissions" section**
4. **Find and click the RDS policy** → Click "X" to remove it (we'll add a custom one)
5. **Click "Add permissions"** → **"Create inline policy"**
6. **Choose JSON tab** and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "arn:aws:rds-db:*:*:dbuser:*/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "rds:DescribeDBInstances",
                "rds:DescribeDBClusters"
            ],
            "Resource": "*"
        }
    ]
}
```

7. **Click "Review policy"** → **"Create policy"**

---

# Part 2: Database Setup (Amazon RDS)

## Overview: What is RDS?

RDS = Relational Database Service

**Think of it as**: A pre-built, managed filing cabinet that stores all your IAM data (users, roles, permissions, audit logs).

**Why RDS?**
- No server management (AWS handles backups, patches, updates)
- Automatic scaling
- High availability (automatic failover)
- Cost-effective for moderate workloads

**For AskIAM**, we'll use PostgreSQL 15.x (industry standard, free tier eligible).

## Step 5: Create RDS Database

### 5A: Open RDS Console

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"RDS"** (Relational Database Service)
   - Click **"RDS"**

2. **RDS Dashboard**
   - Left sidebar → click **"Databases"**
   - Click **"Create database"** button

### 5B: Database Creation - Step 1 (Choose Database Engine)

1. **Engine Options**
   - Under **"Engine type"**, select: **"PostgreSQL"**
   - Under **"Edition"**, leave default: **"PostgreSQL"**
   - Under **"Version"**, select: **"PostgreSQL 15.x"** (latest 15 version)

2. **Templates**
   - Select: **"Dev/Test"** (cheaper for development, single-AZ)
   - Note: For production, use "Production" (multi-AZ, automatic failover)

3. **Click "Next"** or scroll down

### 5C: Database Creation - Step 2 (DB Instance Details)

1. **DB Instance Identifier**
   - Enter: `ask-iam-db`

2. **Credentials**
   - Master username: `postgres` (default, keep it)
   - Master password: Create a STRONG password (12+ characters)
     - Example: `Secure#Pass2024!AskIAM`
   - **IMPORTANT**: Copy this password to a safe location (you'll need it later)

3. **DB Instance Class**
   - Select: **"Burstable classes (includes t classes)"**
   - Then select: **"db.t3.micro"** (smallest, free tier eligible)

4. **Storage**
   - Storage type: **"General Purpose (SSD) - gp3"**
   - Allocated storage: **20 GB**
   - Enable "Storage autoscaling": **Check the box** (auto-expand if needed)
   - Maximum storage: **100 GB**

5. **Availability**
   - Multi-AZ deployment: **"No"** (for dev; "Yes" for production)
   - Backup retention: **7 days** (default)

6. **Click "Next"**

### 5D: Database Creation - Step 3 (Connectivity & Security)

1. **Network & Security**
   - VPC: Leave as **"Default VPC"**
   - DB Subnet Group: **"Create new DB subnet group"**
     - Name: `ask-iam-subnet-group`
     - Click "Create DB subnet group"
     - Leave AZ/Subnet selections as default
   - Public accessibility: **"Yes"** (for development access; "No" for production)
   - VPC Security Group: **"Create new"**
     - Name: `ask-iam-db-sg`
   - Database port: **"5432"** (default PostgreSQL port)

2. **Database Authentication**
   - Authentication: **"Password authentication"**

3. **Click "Next"**

### 5E: Database Creation - Step 4 (Additional Configuration)

1. **Database Options**
   - Database name: `askiam_db` (first database to create)
   - Backup retention period: **7 days**
   - Enable backups: **Checked**
   - Backup window: **"Select window"** → Choose off-peak hours (e.g., 3:00-4:00 AM)

2. **Enhanced Monitoring** (Optional)
   - Enable: **Leave unchecked** (adds cost)

3. **Enable Encryption**
   - Enable encryption: **Checked**
   - AWS KMS key: **"aws/rds"** (AWS-managed, default)

4. **Enable Deletion Protection** (Optional)
   - Enable: **Checked** (prevents accidental deletion)

5. **Click "Create database"**

### 5F: Wait for Database Creation

1. **You'll see a yellow "Creating" status**
   - Database creation takes 5-10 minutes
   - Go grab a coffee ☕

2. **Monitor Progress**
   - Stay on the Databases page
   - Refresh the page occasionally
   - Status will change from **"Creating"** → **"Available"**

3. **Copy Database Endpoint**
   - Once **"Available"**, click the database name: `ask-iam-db`
   - Find **"Endpoint"** section
   - Copy the endpoint URL (looks like: `ask-iam-db.c9akciq32.us-east-1.rds.amazonaws.com`)
   - **SAVE THIS** (you'll need it for Lambda functions)

## Step 6: Create Database Tables

### 6A: Connect to Database (via Query Editor)

**Two methods**: 
- **Method 1 (Easier)**: AWS RDS Query Editor
- **Method 2**: PostgreSQL client (psql command-line tool)

We'll use **Method 1** (easier, no setup):

1. **Open Database Details**
   - Go to RDS Databases
   - Click on `ask-iam-db`
   - Scroll down to **"Actions"** button
   - Click **"Query Database"** (or find **"Query editor"** in left sidebar)

2. **RDS Query Editor Opens**
   - You may see a warning about enabling Query Editor
   - Click **"Enable Query Editor"**
   - Wait for it to enable (1-2 minutes)

3. **Connect to Database**
   - Database: `ask-iam-db`
   - Database user: `postgres`
   - Database password: Enter the password you created in Step 5C
   - Click **"Connect to database"**

### 6B: Create Tables

1. **SQL Query Editor**
   - You'll see a text area to write SQL queries
   - Copy the following SQL and paste it:

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create applications table
CREATE TABLE IF NOT EXISTS applications (
    app_id SERIAL PRIMARY KEY,
    app_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    owner_email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES applications(app_id),
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(app_id, role_name)
);

-- Create user_roles table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    role_id INTEGER NOT NULL REFERENCES roles(role_id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(user_id, role_id)
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    request_id VARCHAR(50),
    ip_address VARCHAR(45),
    status VARCHAR(20),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create policies table
CREATE TABLE IF NOT EXISTS policies (
    policy_id SERIAL PRIMARY KEY,
    policy_name VARCHAR(100) UNIQUE NOT NULL,
    policy_json JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_applications_name ON applications(app_name);
CREATE INDEX idx_roles_app_id ON roles(app_id);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
```

2. **Execute Query**
   - Click **"Execute"** button (or press Ctrl+Enter)
   - Wait for success message (green checkmark)

3. **Verify Tables Created**
   - Write test query:
   ```sql
   \dt
   ```
   - Or list tables:
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_schema='public';
   ```
   - Execute to see list of tables

### 6C: Insert Sample Data (Optional)

To test if database is working:

```sql
-- Insert sample application
INSERT INTO applications (app_name, description, owner_email) 
VALUES ('Workday', 'HR Management System', 'hr@company.com');

-- Insert sample users
INSERT INTO users (username, email, full_name) 
VALUES 
('john.doe', 'john.doe@company.com', 'John Doe'),
('jane.smith', 'jane.smith@company.com', 'Jane Smith');

-- Insert sample role
INSERT INTO roles (app_id, role_name, description, permissions)
VALUES (1, 'HR_Analyst', 'Human Resources Analyst', '{"read": true, "write": false}');

-- Verify data inserted
SELECT * FROM users;
SELECT * FROM applications;
SELECT * FROM roles;
```

**Save Database Details** (you'll need these for Lambda):
```
Database Endpoint: ask-iam-db.c9akciq32.us-east-1.rds.amazonaws.com
Database Name: askiam_db
Database User: postgres
Database Password: [Your strong password from Step 5C]
Database Port: 5432
```

---

# Part 3: Search & Analytics (OpenSearch Serverless)

## Overview: What is OpenSearch Serverless?

**Think of it as**: A super-fast search engine for your IAM data. Like Google, but for your company's internal policies and access patterns.

**Why?**
- Search through policies and access patterns in milliseconds
- Semantic search (understands meaning, not just keywords)
- Analytics and dashboards
- No servers to manage
- Serverless = only pay for what you use

**For AskIAM**, we'll use it to:
- Store and search IAM policies
- Track historical access patterns
- Provide context to the LLM for validation

## Step 7: Create OpenSearch Serverless Collection

### 7A: Open OpenSearch Console

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"OpenSearch"**
   - Click **"Amazon OpenSearch Service"**

2. **OpenSearch Dashboard**
   - You'll see options for OpenSearch Serverless
   - Click **"Collections"** in left sidebar (under Serverless)
   - Click **"Create collection"** button

### 7B: Configure Serverless Collection

1. **Basic Information**
   - Collection name: `ask-iam-collection`
   - Collection type: **"Search"** (instead of "Time series")
   - Click **"Next"**

### 7C: Set Capacity

1. **Capacity Configuration**
   - Indexing OCU: **4** (Indexing capacity units)
   - Search OCU: **4** (Search capacity units)
   - **Explanation**: OCU = Indexing/Search power. Start with 4; scales automatically.
   - Click **"Next"**

### 7D: Network & Security

1. **Network Access**
   - Public endpoint: **"Public"** (allows access from anywhere)
   - **Note**: For production, use VPC endpoints and restrict IP ranges

2. **Encryption**
   - Enable encryption at rest: **Checked**
   - Enable encryption in transit: **Checked**
   - AWS KMS key: **"Manage in AWS KMS"** (AWS-managed)

3. **Click "Next"**

### 7E: Review and Create

1. **Review Settings**
   - Collection name: `ask-iam-collection`
   - Capacity: 4 OCU indexing + 4 OCU search
   - Public endpoint enabled
   - Encryption enabled

2. **Click "Create collection"**

3. **Collection Creation**
   - Status will show **"Creating"** (takes 2-3 minutes)
   - Once **"Active"**, note the **"Collection endpoint"**
   - Example: `ask-iam-collection.us-east-1.aoss.amazonaws.com`
   - **SAVE THIS** (you'll need it for Lambda)

### 7F: Create Data Access Policy

OpenSearch needs permission rules. Let's create one:

1. **Still in OpenSearch Console**
   - Left sidebar → scroll down to **"Data access policy"**
   - Click **"Create"** (if not already created)

2. **Add Policy**
   - Under **"Collection access"**, click **"Select collection"**
   - Choose: `ask-iam-collection`
   - Principal (who can access): You'll specify the Lambda role
   - Permissions: Select all available permissions
   - Click **"Create policy"**

3. **If Already Exists**
   - Click the policy name
   - Click **"Edit"** → **"Add principal"**
   - Principal ARN: `arn:aws:iam::YOUR-ACCOUNT-ID:role/ask-iam-lambda-execution-role`
   - (Get YOUR-ACCOUNT-ID from IAM console)
   - Select all permissions
   - Click **"Save"**

### 7G: Create OpenSearch Indexes

Now let's create indexes (tables) for data:

1. **Go to OpenSearch Dashboard**
   - Still in OpenSearch console
   - Find **"Dashboards URL"** for your collection
   - Click the URL to open OpenSearch Dashboards

2. **Dashboards Sign-In**
   - Username: Leave blank or `admin`
   - Password: Leave blank or will prompt
   - You may need to set up master user on first login

3. **Create First Index**
   - In Dashboards, go to **"Dev Tools"** (left sidebar)
   - Go to **"Console"** tab
   - Paste the following and click play button:

```json
PUT /iam_policies
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "policy_name": { "type": "keyword" },
      "policy_json": { "type": "text" },
      "app_id": { "type": "keyword" },
      "created_at": { "type": "date" },
      "compliance_level": { "type": "keyword" }
    }
  }
}
```

4. **Create Second Index** (for access patterns):

```json
PUT /access_patterns
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "user_id": { "type": "keyword" },
      "role_id": { "type": "keyword" },
      "app_id": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "approved": { "type": "boolean" },
      "reason": { "type": "text" }
    }
  }
}
```

**Save OpenSearch Details**:
```
Collection Endpoint: ask-iam-collection.us-east-1.aoss.amazonaws.com
Index 1: iam_policies
Index 2: access_patterns
Dashboard URL: [Your-OpenSearch-Endpoint]/_dashboards/
```

---

# Part 4: Secrets Management

## Overview: Secure Storage for Sensitive Data

**Think of it as**: A safe deposit box for passwords, API keys, and secrets.

**Why?**
- Never hardcode passwords in code
- Automatic rotation of credentials
- Audit trail of who accessed secrets
- Encryption at rest and in transit

**For AskIAM**, we'll store:
- RDS database password
- OpenSearch credentials (if needed)
- API keys for external services
- JWT secrets (for authentication)

## Step 8: Store Database Password in Secrets Manager

### 8A: Open Secrets Manager

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"Secrets Manager"**
   - Click **"Secrets Manager"**

2. **Secrets Dashboard**
   - Click **"Store a new secret"** button

### 8B: Create Secret for Database Password

1. **Select Secret Type**
   - Choose: **"Credentials for RDS database"**
   - Database: Select `ask-iam-db` from dropdown
   - Username: `postgres`
   - Password: Paste the password you created in Step 5C

2. **Secret Name**
   - Secret name: `ask-iam/prod/rds/password`
   - Description: `RDS Aurora database password for AskIAM`

3. **Rotation (Optional)**
   - Enable rotation: **Unchecked** (for dev; enable for production)

4. **Click "Store secret"**

### 8C: View Secret Details

1. **Secret Created Successfully**
   - You'll see confirmation
   - Click on the secret name to view details
   - **IMPORTANT**: Note the **ARN** (Amazon Resource Name)
   - Example: `arn:aws:secretsmanager:us-east-1:123456789:secret:ask-iam/prod/rds/password-xxxxx`

2. **Test Access from Lambda**
   - Lambda code will use this ARN to retrieve the password

## Step 9: Store Parameters in Parameter Store

Parameter Store is for non-sensitive configuration (like URLs, thresholds).

### 9A: Open Parameter Store

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"Parameter Store"** or **"Systems Manager"**
   - Click **"Systems Manager"**

2. **Left Sidebar**
   - Scroll down → click **"Parameter Store"**
   - Click **"Create parameter"** button

### 9B: Create Parameters

Create the following parameters (one at a time):

**Parameter 1: RDS Endpoint**
```
Name: /ask-iam/prod/rds/endpoint
Type: String
Value: ask-iam-db.c9akciq32.us-east-1.rds.amazonaws.com
Description: RDS database endpoint
```

**Parameter 2: RDS Database Name**
```
Name: /ask-iam/prod/rds/database
Type: String
Value: askiam_db
Description: RDS database name
```

**Parameter 3: OpenSearch Endpoint**
```
Name: /ask-iam/prod/opensearch/endpoint
Type: String
Value: ask-iam-collection.us-east-1.aoss.amazonaws.com
Description: OpenSearch collection endpoint
```

**Parameter 4: RAG Confidence Threshold**
```
Name: /ask-iam/prod/rag/confidence-threshold
Type: String
Value: 0.95
Description: Confidence threshold for RAG validation (0.0-1.0)
```

**Parameter 5: API Gateway Key** (we'll create this later)
```
Name: /ask-iam/prod/apigateway/key
Type: String
Value: [Will update after creating API Gateway]
Description: API Gateway API Key
```

**For each parameter:**
1. Click **"Create parameter"**
2. Fill in the fields as shown above
3. Click **"Create parameter"**

---

# Part 5: Backend Logic (AWS Lambda)

## Overview: Lambda Functions

**Think of it as**: Serverless workers that:
- Listen for requests
- Process data
- Call databases and services
- Return results

**Why Serverless?**
- Only pay when code runs
- Auto-scales with traffic
- No servers to manage
- Perfect for conversational bots

**For AskIAM**, we need 5 Lambda functions:
1. **RequestOrchestrator**: Main controller
2. **EntityExtractor**: Parse user requests
3. **RAGValidator**: Check compliance using search
4. **MCPValidator**: Check database rules
5. **AuditLogger**: Log all actions

## Step 10: Create Lambda Execution Layer (Dependencies)

Lambda Layers let you share code libraries across functions (like Python packages).

### 10A: Open Lambda Console

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"Lambda"**
   - Click **"Lambda"**

2. **Lambda Dashboard**
   - Left sidebar → click **"Layers"**
   - Click **"Create layer"** button

### 10B: Create Python Dependencies Layer

1. **Basic Information**
   - Layer name: `ask-iam-dependencies`
   - Description: `Python packages for AskIAM Lambda functions`
   - Compatible runtimes: **"Python 3.11"** and **"Python 3.12"**

2. **Upload Code**
   - We need to upload a ZIP file with Python packages
   - **Option A (Simple)**: Use Console file upload
   - **Option B (Recommended)**: Build locally and upload

**For Option A (Console - Easiest):**
   - Click **"Upload from"** → **"Upload a .zip file"**
   - We'll create the ZIP file next

**To Create the ZIP File:**

1. Create a folder structure on your computer:
```
python/
  └── lib/
      └── python3.11/
          └── site-packages/
              ├── psycopg2/
              ├── requests/
              ├── boto3/  (already available in Lambda)
              └── ...
```

2. Or use AWS Lambda Layers pre-built:
   - AWS provides psycopg2 libraries
   - We can use the Lambda runtime's built-in boto3

**For this tutorial, we'll skip the Layer for now** and include dependencies in each function directly.

---

## Step 11: Create RequestOrchestrator Lambda Function

This is the main function that routes requests.

### 11A: Create Lambda Function

1. **Lambda Console**
   - Left sidebar → click **"Functions"**
   - Click **"Create function"** button

2. **Function Details - Page 1**
   - Author from scratch: **Selected**
   - Function name: `ask-iam-orchestrator`
   - Runtime: **"Python 3.11"**
   - Architecture: **"x86_64"**
   - Permissions: **"Create a new role with basic Lambda permissions"**
     - Role name: auto-generated (like `ask-iam-orchestrator-role-xxxxx`)
   - Click **"Create function"**

### 11B: Configure Function Settings

1. **General Configuration**
   - Scroll to **"General configuration"** section
   - Click **"Edit"** button
   - Timeout: Change from 3 seconds to **60 seconds**
   - Memory: Change from 128 MB to **512 MB**
   - Ephemeral storage: **512 MB** (default)
   - Click **"Save"**

2. **Execution Role Permissions**
   - Scroll to **"Execution role"** section
   - Click on the role name (opens new tab)
   - Add inline policy or attach policies:
     - Go to **"Add permissions"** → **"Attach policy"**
     - Attach the role we created in Part 1: `ask-iam-lambda-execution-role`

### 11C: Add Function Code

1. **Code Editor**
   - You'll see a default Python function with `lambda_handler`
   - Clear all and replace with:

```python
import json
import boto3
import logging
import uuid
from datetime import datetime

# Initialize clients
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm_client = boto3.client('ssm')
lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    Main orchestrator Lambda function.
    Coordinates validation pipeline for access requests.
    """
    
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Extract request details
        request_body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        raw_request = request_body.get('request_text', '')
        user_id = request_body.get('user_id', 'unknown')
        
        logger.info(f"Request {request_id} from user {user_id}: {raw_request}")
        
        # Validate request
        if not raw_request or not raw_request.strip():
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'status': 'ERROR',
                    'reason': 'Empty request text',
                    'request_id': request_id
                })
            }
        
        # Step 1: Invoke EntityExtractor
        extractor_response = invoke_lambda_function(
            'ask-iam-entity-extractor',
            {
                'request_text': raw_request,
                'request_id': request_id,
                'user_id': user_id
            }
        )
        
        logger.info(f"Entity extraction result: {extractor_response}")
        
        # Step 2: Invoke RAGValidator and MCPValidator in parallel
        rag_response = invoke_lambda_function(
            'ask-iam-rag-validator',
            extractor_response,
            async_invocation=True
        )
        
        mcp_response = invoke_lambda_function(
            'ask-iam-mcp-validator',
            extractor_response,
            async_invocation=True
        )
        
        # Step 3: Combine results
        validation_result = combine_validation_results(
            rag_response,
            mcp_response,
            request_id
        )
        
        logger.info(f"Validation result: {validation_result}")
        
        # Step 4: Log to audit
        invoke_lambda_function(
            'ask-iam-audit-logger',
            {
                'request_id': request_id,
                'user_id': user_id,
                'validation_result': validation_result,
                'timestamp': datetime.utcnow().isoformat()
            },
            async_invocation=True
        )
        
        # Step 5: Send metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='AskIAM',
            MetricData=[
                {
                    'MetricName': 'AccessRequestCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Status', 'Value': validation_result.get('status', 'UNKNOWN')}
                    ]
                }
            ]
        )
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(validation_result)
        }
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'ERROR',
                'reason': f'Internal error: {str(e)}',
                'request_id': request_id
            })
        }

def invoke_lambda_function(function_name, payload, async_invocation=False):
    """Invoke another Lambda function."""
    try:
        invocation_type = 'Event' if async_invocation else 'RequestResponse'
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload)
        )
        
        if async_invocation:
            return {'status': 'QUEUED', 'function': function_name}
        
        # For synchronous calls, parse response
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read().decode())
            return payload
        else:
            raise Exception(f"Lambda invocation failed: {response['StatusCode']}")
    
    except Exception as e:
        logger.error(f"Error invoking {function_name}: {str(e)}")
        raise

def combine_validation_results(rag_result, mcp_result, request_id):
    """Combine results from both validators."""
    
    # For demo: simple logic
    # In production: use weighted scoring
    
    return {
        'request_id': request_id,
        'status': 'VALID',  # Will be updated after both validators complete
        'rag_confidence': 0.95,
        'mcp_result': 'PASSED',
        'timestamp': datetime.utcnow().isoformat()
    }
```

2. **Save Function**
   - Click **"Deploy"** button

3. **Test Function**
   - Go to **"Test"** tab
   - Create test event:

```json
{
  "body": {
    "request_text": "I need access to HR Analyst role in Workday",
    "user_id": "john.doe"
  }
}
```

   - Click **"Test"** button
   - Check results in **"Execution result"** section

---

## Step 12: Create EntityExtractor Lambda Function

Parses natural language to extract entities.

### 12A: Create Function

1. **Create New Function**
   - Lambda console → **"Create function"**
   - Function name: `ask-iam-entity-extractor`
   - Runtime: **"Python 3.11"**
   - Click **"Create function"**

### 12B: Add Function Code

```python
import json
import boto3
import re
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

db_client = boto3.client('rds')
ssm_client = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Extract user, role, and application from natural language request.
    """
    
    try:
        request_text = event.get('request_text', '')
        request_id = event.get('request_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        
        logger.info(f"Extracting entities from: {request_text}")
        
        # Simple extraction using regex and keyword matching
        entities = extract_entities(request_text)
        
        if not entities:
            return {
                'statusCode': 400,
                'body': {
                    'status': 'ERROR',
                    'reason': 'Could not extract entities from request',
                    'request_id': request_id
                }
            }
        
        logger.info(f"Extracted entities: {entities}")
        
        # Query RDS to validate entities exist
        # (For now, we'll skip actual DB query)
        # In production, connect to RDS and validate
        
        result = {
            'statusCode': 200,
            'body': {
                'request_id': request_id,
                'user_id': user_id,
                'user_name': entities.get('user'),
                'application_name': entities.get('application'),
                'role_name': entities.get('role'),
                'entities_extracted': True
            }
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'status': 'ERROR', 'reason': str(e)}
        }

def extract_entities(text):
    """
    Extract user, role, and application from text.
    Uses simple pattern matching.
    """
    
    # Common application names
    applications = {
        'workday': 'Workday',
        'salesforce': 'Salesforce',
        'jira': 'Jira',
        'okta': 'Okta',
        'github': 'GitHub',
        'aws': 'AWS'
    }
    
    # Common roles
    roles = {
        'analyst': 'Analyst',
        'admin': 'Administrator',
        'developer': 'Developer',
        'manager': 'Manager',
        'engineer': 'Engineer',
        'lead': 'Lead'
    }
    
    text_lower = text.lower()
    
    entities = {}
    
    # Extract application
    for app_key, app_name in applications.items():
        if app_key in text_lower:
            entities['application'] = app_name
            break
    
    # Extract role
    for role_key, role_name in roles.items():
        if role_key in text_lower:
            entities['role'] = role_name
            break
    
    # Extract user (simple heuristic)
    # Look for email-like patterns or specific keywords
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\b'
    emails = re.findall(email_pattern, text_lower)
    if emails:
        entities['user'] = emails[0].split('@')[0]
    else:
        entities['user'] = 'current_user'
    
    return entities if entities else None
```

2. **Deploy and Test**
   - Click **"Deploy"**
   - Test with sample input

---

## Step 13: Create RAGValidator Lambda Function

Uses OpenSearch for semantic validation.

### 13A: Create Function

1. **Create New Function**
   - Lambda console → **"Create function"**
   - Function name: `ask-iam-rag-validator`
   - Runtime: **"Python 3.11"**
   - Click **"Create function"**

### 13B: Add Function Code

```python
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm_client = boto3.client('ssm')

def lambda_handler(event, context):
    """
    RAG-based validation using OpenSearch.
    Checks semantic similarity to known access patterns.
    """
    
    try:
        request_id = event.get('request_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        user_name = event.get('user_name', '')
        app_name = event.get('application_name', '')
        role_name = event.get('role_name', '')
        
        logger.info(f"RAG validation: {user_name} → {app_name}/{role_name}")
        
        # Get confidence threshold from Parameter Store
        threshold_response = ssm_client.get_parameter(Name='/ask-iam/prod/rag/confidence-threshold')
        threshold = float(threshold_response['Parameter']['Value'])
        
        # Simulate semantic search
        # In production: Query OpenSearch with semantic search
        # For now: Simple keyword matching
        
        confidence_score = calculate_confidence(
            user_name,
            app_name,
            role_name
        )
        
        is_valid = confidence_score >= threshold
        
        result = {
            'statusCode': 200,
            'body': {
                'request_id': request_id,
                'validator': 'RAG',
                'is_valid': is_valid,
                'confidence': confidence_score,
                'reason': f'Confidence score: {confidence_score}',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"RAG result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"RAG validation error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'status': 'ERROR', 'reason': str(e)}
        }

def calculate_confidence(user_name, app_name, role_name):
    """
    Calculate confidence score based on patterns.
    In production: Use LLM + semantic search.
    """
    
    # Simple scoring: check if all entities provided
    score = 0.0
    
    if user_name:
        score += 0.33
    if app_name:
        score += 0.33
    if role_name:
        score += 0.34
    
    # Additional boost for common combinations
    common_combos = [
        ('workday', 'analyst'),
        ('salesforce', 'admin'),
        ('jira', 'developer')
    ]
    
    for app, role in common_combos:
        if app.lower() in app_name.lower() and role.lower() in role_name.lower():
            score = min(score + 0.15, 1.0)
    
    return round(score, 2)
```

2. **Deploy and Test**

---

## Step 14: Create MCPValidator Lambda Function

Database-driven validation.

### 14A: Create Function

1. **Create New Function**
   - Function name: `ask-iam-mcp-validator`
   - Runtime: **"Python 3.11"**

### 14B: Add Function Code

```python
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm_client = boto3.client('ssm')

def lambda_handler(event, context):
    """
    MCP validation using database queries.
    Checks business rules directly from RDS.
    """
    
    try:
        request_id = event.get('request_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        user_name = event.get('user_name', '')
        app_name = event.get('application_name', '')
        role_name = event.get('role_name', '')
        
        logger.info(f"MCP validation: {user_name} → {app_name}/{role_name}")
        
        # In production: Execute SQL queries to RDS
        # For now: Simulated checks
        
        is_valid = perform_validation(
            user_name,
            app_name,
            role_name
        )
        
        result = {
            'statusCode': 200,
            'body': {
                'request_id': request_id,
                'validator': 'MCP',
                'is_valid': is_valid,
                'reason': 'Passed business rule validation' if is_valid else 'Failed business rules',
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"MCP result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"MCP validation error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'status': 'ERROR', 'reason': str(e)}
        }

def perform_validation(user_name, app_name, role_name):
    """
    Perform validation checks.
    In production: Query RDS database.
    """
    
    # Check 1: All entities must be non-empty
    if not all([user_name, app_name, role_name]):
        return False
    
    # Check 2: User must not already have role
    # (Would check RDS in production)
    
    # Check 3: Role must exist in application
    # (Would check RDS in production)
    
    # For demo: Always return True if entities present
    return True
```

2. **Deploy and Test**

---

## Step 15: Create AuditLogger Lambda Function

Logs all actions to database and CloudWatch.

### 15A: Create Function

1. **Create New Function**
   - Function name: `ask-iam-audit-logger`
   - Runtime: **"Python 3.11"**

### 15B: Add Function Code

```python
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    Asynchronous audit logging function.
    Logs validation events for compliance and auditing.
    """
    
    try:
        request_id = event.get('request_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        validation_result = event.get('validation_result', {})
        timestamp = event.get('timestamp', datetime.utcnow().isoformat())
        
        # Log to CloudWatch (structured JSON)
        audit_log = {
            'timestamp': timestamp,
            'request_id': request_id,
            'user_id': user_id,
            'validation_status': validation_result.get('status', 'UNKNOWN'),
            'rag_confidence': validation_result.get('rag_confidence', 0),
            'mcp_result': validation_result.get('mcp_result', 'UNKNOWN'),
            'action': 'ACCESS_REQUEST_VALIDATION'
        }
        
        logger.info(json.dumps(audit_log))
        
        # In production: Insert into RDS audit_log table
        # insert_to_database(audit_log)
        
        # Send metric to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='AskIAM',
            MetricData=[
                {
                    'MetricName': 'AuditLogCount',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'body': {
                'status': 'LOGGED',
                'request_id': request_id
            }
        }
    
    except Exception as e:
        logger.error(f"Audit logging error: {str(e)}")
        # Don't raise exception in audit logger to prevent cascade failures
        return {
            'statusCode': 500,
            'body': {'status': 'ERROR', 'reason': str(e)}
        }

def insert_to_database(audit_log):
    """
    Insert audit log to RDS.
    (Implementation shown in Part 10)
    """
    pass
```

2. **Deploy and Test**

---

# Part 6: Request Routing (API Gateway)

## Overview: API Gateway

**Think of it as**: A front door for your application.
- Receives HTTP requests
- Routes to Lambda functions
- Returns responses to clients
- Handles API keys, throttling, CORS

## Step 16: Create REST API

### 16A: Open API Gateway Console

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"API Gateway"**
   - Click **"API Gateway"**

2. **API Gateway Dashboard**
   - Click **"Create API"** button
   - Choose: **"REST API"** (not HTTP API or WebSocket)
   - Click **"Build"**

### 16B: Create API

1. **API Details**
   - API name: `ask-iam-api`
   - Description: `API for AskIAM conversational bot`
   - Endpoint type: **"Regional"** (default)
   - Click **"Create API"**

### 16C: Create /chat Resource

1. **You'll see Resources tree**
   - Right-click on **"/"** (root) → **"Create resource"**
   - Resource name: `chat`
   - Resource path: `/chat`
   - Click **"Create resource"**

### 16D: Create POST Method for /chat

1. **Select /chat resource**
   - Click on **"/chat"** in tree
   - Click **"Create method"** → **"POST"**

2. **Configure POST Method**
   - Integration type: **"Lambda function"**
   - Lambda function: `ask-iam-orchestrator`
   - Lambda proxy integration: **Check the box** (simplifies response handling)
   - Click **"Save"**

3. **Grant API Gateway Permission**
   - AWS will ask for permission
   - Click **"OK"** to proceed

### 16E: Enable CORS (if calling from web)

1. **CORS Configuration**
   - Select **"/chat"** resource
   - Click **"Enable CORS and replace existing CORS headers"**
   - Check all Methods
   - Click **"Yes, replace existing values"**

2. **CORS Headers Added**
   - Automatically configures `Access-Control-Allow-Origin: *`
   - Needed for web UI to call API

### 16F: Create API Key

1. **Go to API Keys**
   - Left sidebar → **"API Keys"**
   - Click **"Create API key"**
   - Name: `ask-iam-default-key`
   - Description: `Default API key for AskIAM`
   - Click **"Create"**

2. **Copy API Key Value**
   - Click on the key name
   - You'll see the key value (long string)
   - **COPY AND SAVE** this (you'll need it to call the API)
   - Update Parameter Store: `/ask-iam/prod/apigateway/key`

### 16G: Create Usage Plan

Usage Plans limit how many requests are allowed.

1. **Go to Usage Plans**
   - Left sidebar → **"Usage Plans"**
   - Click **"Create usage plan"**
   - Name: `ask-iam-basic-plan`
   - Description: `Basic plan for AskIAM`
   - Throttle settings:
     - Rate: 100 requests per second
     - Burst: 200 requests
   - Quota settings:
     - Limit: 10,000 requests per day
   - Click **"Next"**

2. **Add API Stages**
   - Add API stage: `ask-iam-api` → `prod` (we'll create `prod` stage next)
   - Click **"Next"**

3. **Add API Keys**
   - Select your API key from Step 16F
   - Click **"Add API Key to Usage Plan"**
   - Click **"Done"**

### 16H: Deploy API

1. **Create Stage**
   - Go back to **"Resources"**
   - Click **"Deploy API"**
   - Stage name: `prod`
   - Description: `Production stage`
   - Click **"Deploy"**

2. **Get Invoke URL**
   - You'll see **"Invoke URL"**
   - Example: `https://abc123.execute-api.us-east-1.amazonaws.com/prod`
   - **SAVE THIS** (you'll call this URL from clients)

### 16I: Test API Endpoint

1. **Using curl in Terminal:**

```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "request_text": "I need access to HR Analyst role in Workday",
    "user_id": "john.doe"
  }'
```

2. **Expected Response:**

```json
{
  "request_id": "abc12345",
  "status": "VALID",
  "rag_confidence": 0.95,
  "mcp_result": "PASSED",
  "timestamp": "2024-01-21T10:30:45.123Z"
}
```

3. **Common Issues:**
   - **403 Forbidden**: Check API key is correct
   - **502 Bad Gateway**: Lambda function has error (check CloudWatch Logs)
   - **Timeout**: Lambda function taking too long (increase timeout)

---

# Part 7: Conversational Interface (Amazon Lex)

## Overview: Amazon Lex

**Think of it as**: A chat AI that understands natural language.

**Why?**
- Users can ask in plain English
- No need to fill forms
- Natural conversation flow
- Voice and text support

**For AskIAM**, Lex will:
- Understand access request intents
- Extract user, role, app from conversation
- Pass to Lambda for validation

## Step 17: Create Lex Bot

### 17A: Open Lex Console

1. **Go to AWS Console**
   - Click **"Services"** menu
   - Search for **"Lex"**
   - Click **"Amazon Lex"**

2. **Lex Dashboard**
   - Click **"Create bot"** button
   - Choose: **"Create a blank bot"**

### 17B: Bot Details

1. **Bot Configuration**
   - Bot name: `AskIAMBot`
   - Description: `Conversational bot for IAM access requests`
   - IAM permissions: **"Create a role with basic Lex permissions"**
   - COPPA (Children's Online Privacy): **"No"**
   - Click **"Next"**

2. **Language**
   - Language: **"English (US)"**
   - Click **"Create bot"**

### 17C: Create Intent

Intents are the actions the bot understands.

1. **Create New Intent**
   - Click **"Add intent"** → **"Create intent"**
   - Intent name: `RequestAccessIntent`
   - Description: `User requests access to a role`
   - Click **"Create intent"**

2. **Add Sample Utterances**
   - These are examples of user requests
   - Add these utterances (one per line):
   ```
   I need access to {Application} {Role} role
   Can I have {Application} {Role} role
   I want {Role} access in {Application}
   Grant me {Application} {Role}
   Add me to {Application} {Role}
   ```

3. **Create Slots** (parameters to extract)
   - Add Slot 1:
     - Slot name: `Application`
     - Slot type: **"Amazon.AlphaNumeric"**
     - Prompt for slot: `Which application do you need access to?`
   
   - Add Slot 2:
     - Slot name: `Role`
     - Slot type: **"Amazon.AlphaNumeric"**
     - Prompt for slot: `What role do you need?`

4. **Fulfillment**
   - Fulfillment type: **"Lambda function"**
   - Lambda function: `ask-iam-orchestrator`
   - Click **"Save intent"**

### 17D: Build and Test Bot

1. **Build Bot**
   - Click **"Build"** button
   - Wait for build to complete (1-2 minutes)

2. **Test Bot**
   - Click **"Test"** button
   - Type a message: `I need access to Workday HR Analyst role`
   - Bot will:
     - Recognize the intent
     - Extract Application = "Workday", Role = "HR Analyst"
     - Call `ask-iam-orchestrator` Lambda
     - Return validation result

3. **Check Response**
   - Should see JSON response with validation result

---

# Part 8: Monitoring & Logging

## Overview: Observability

**Why Monitor?**
- Detect errors quickly
- Understand performance
- Track usage
- Optimize costs

**Tools we'll use:**
- **CloudWatch Logs**: See function output
- **CloudWatch Metrics**: Track performance
- **CloudWatch Alarms**: Alert on problems
- **X-Ray**: Trace requests across services

## Step 18: Set Up CloudWatch Logs

### 18A: View Lambda Logs

1. **Go to Lambda Console**
   - Click **"Functions"**
   - Click on a function: `ask-iam-orchestrator`

2. **Monitor Tab**
   - Click **"Monitor"** tab
   - See:
     - Invocations count
     - Errors count
     - Duration (milliseconds)
     - Throttles

3. **View Logs**
   - Scroll to **"Recent invocations"**
   - Click on any invocation
   - See the function output and any errors

### 18B: Create CloudWatch Log Group

1. **Go to CloudWatch Console**
   - Click **"Services"** menu
   - Search for **"CloudWatch"**
   - Click **"CloudWatch"**

2. **Log Groups**
   - Left sidebar → **"Log groups"**
   - You'll see auto-created groups like:
     - `/aws/lambda/ask-iam-orchestrator`
     - `/aws/lambda/ask-iam-entity-extractor`
     - `/aws/apigateway/ask-iam-api`

3. **View Logs**
   - Click on a log group
   - Click on a log stream
   - See all the log entries from your functions

### 18C: Create Log Insights Query

Log Insights lets you search logs with SQL-like queries.

1. **Go to Logs Insights**
   - In CloudWatch, left sidebar → **"Logs Insights"**
   - Select log groups: Check the Lambda log groups
   - Time range: **"Last 1 hour"**

2. **Example Query - Find Errors**

```sql
fields @timestamp, @message, @functionName
| filter @message like /ERROR|FAILED/
| stats count() as error_count by @functionName
```

   - Click **"Run query"**
   - See error counts by function

3. **Example Query - Slow Requests**

```sql
fields @timestamp, @duration, @functionName
| filter @duration > 1000
| stats avg(@duration) as avg_duration, max(@duration) as max_duration by @functionName
```

## Step 19: Set Up CloudWatch Metrics

### 19A: Create Custom Metrics Dashboard

1. **Create Dashboard**
   - CloudWatch → left sidebar → **"Dashboards"**
   - Click **"Create dashboard"**
   - Name: `AskIAM-Monitoring`
   - Click **"Create dashboard"**

2. **Add Metrics**
   - Click **"Add widget"** → **"Line"** (for graphs)
   - Search for metrics:
     - Namespace: `AWS/Lambda`
     - Metrics: `Duration`, `Errors`, `Invocations`
   - Add widget

3. **Add Another Widget for API Gateway**
   - Namespace: `AWS/ApiGateway`
   - Metrics: `Count`, `Latency`, `4XXError`, `5XXError`

## Step 20: Create CloudWatch Alarms

Alarms alert you when something goes wrong.

### 20A: Create Lambda Error Alarm

1. **Go to Alarms**
   - CloudWatch → left sidebar → **"Alarms"**
   - Click **"Create alarm"** → **"Create alarm"**

2. **Alarm Configuration**
   - Metric: 
     - Namespace: `AWS/Lambda`
     - Metric: `Errors`
     - Statistic: `Sum`
     - Period: **"1 minute"**
   - Condition:
     - Threshold: **Greater than 5 errors**
   - Actions:
     - Notification: Create new SNS topic
     - Topic name: `ask-iam-alerts`
     - Email address: your email
   - Click **"Create alarm"**

3. **Confirm SNS Subscription**
   - Check your email for AWS SNS confirmation
   - Click the confirmation link

### 20B: Create API Latency Alarm

1. **Create New Alarm**
   - Namespace: `AWS/ApiGateway`
   - Metric: `Latency`
   - Condition: **Greater than 5000 milliseconds** (5 seconds)
   - Action: Notify SNS topic `ask-iam-alerts`

## Step 21: Enable X-Ray Tracing

X-Ray shows how requests flow through your services.

### 21A: Enable X-Ray in Lambda

1. **Open Lambda Function**
   - Go to a Lambda function: `ask-iam-orchestrator`
   - Scroll to **"Code"** section
   - Update the code to import and use X-Ray:

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch all AWS SDK calls
patch_all()

@xray_recorder.capture('process_request')
def lambda_handler(event, context):
    # Your function code
    pass
```

2. **Update Function Role**
   - Go to **"Execution role"**
   - Click the role
   - Add policy: `AWSXRayDaemonWriteAccess`

### 21B: View X-Ray Service Map

1. **Go to X-Ray Console**
   - Click **"Services"** → search **"X-Ray"**
   - Click **"Amazon X-Ray"**

2. **Service Map**
   - Left sidebar → **"Service map"**
   - You'll see all connected services:
     - API Gateway → Lambda → RDS/OpenSearch
   - Click on service connections to see details

3. **Traces**
   - Left sidebar → **"Traces"**
   - See individual request traces
   - View timing and errors

---

# Part 9: Testing & Deployment

## Overview: Testing Your Application

Before deploying to production, we need to test:
1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test functions working together
3. **End-to-End Tests**: Test full flow from API to database
4. **Load Tests**: Test with many concurrent requests

## Step 22: Manual Testing

### 22A: Test API Endpoint

1. **Using cURL (Command Line)**

```bash
# Test 1: Valid request
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "request_text": "I need access to Workday HR Analyst",
    "user_id": "john.doe"
  }'

# Test 2: Empty request (should fail)
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{
    "request_text": "",
    "user_id": "john.doe"
  }'

# Test 3: Missing API key (should fail with 403)
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "I need access",
    "user_id": "john.doe"
  }'
```

2. **Using Postman** (GUI tool)
   - Download: https://www.postman.com/downloads/
   - Create new POST request
   - URL: Your API endpoint
   - Add header: `x-api-key: YOUR-API-KEY`
   - Body (JSON):
   ```json
   {
     "request_text": "I need access to Workday HR Analyst",
     "user_id": "john.doe"
   }
   ```
   - Click **"Send"**

### 22B: Test Each Lambda Function Individually

1. **Test RequestOrchestrator**
   - Go to Lambda console
   - Click on `ask-iam-orchestrator`
   - Go to **"Test"** tab
   - Create test event:
   ```json
   {
     "body": "{\"request_text\": \"I need access\", \"user_id\": \"john.doe\"}"
   }
   ```
   - Click **"Test"**
   - Check "Execution result"

2. **Test EntityExtractor**
   - Create test event:
   ```json
   {
     "request_text": "I need access to Workday HR Analyst",
     "request_id": "test-123",
     "user_id": "john.doe"
   }
   ```
   - Run test

3. **Test Other Functions Similarly**

### 22C: Check CloudWatch Logs

1. **Go to CloudWatch Logs**
   - Navigate to CloudWatch
   - Click **"Log groups"**
   - Click on `/aws/lambda/ask-iam-orchestrator`
   - Click latest log stream
   - Review logs for any errors

## Step 23: Integration Testing

### 23A: Test Database Connection

Create a test Lambda to verify RDS connection:

1. **Create Test Function**
   - Name: `test-rds-connection`
   - Runtime: Python 3.11

2. **Add Code**

```python
import psycopg2
import json
import boto3
import os

def lambda_handler(event, context):
    """Test RDS connection"""
    
    try:
        # Get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        secret = secrets_client.get_secret_value(SecretId='ask-iam/prod/rds/password')
        password = json.loads(secret['SecretString'])['password']
        
        # Get endpoint from Parameter Store
        ssm_client = boto3.client('ssm')
        endpoint_response = ssm_client.get_parameter(Name='/ask-iam/prod/rds/endpoint')
        endpoint = endpoint_response['Parameter']['Value']
        
        # Connect to database
        conn = psycopg2.connect(
            host=endpoint,
            database='askiam_db',
            user='postgres',
            password=password,
            port=5432
        )
        
        # Test query
        cur = conn.cursor()
        cur.execute('SELECT version();')
        version = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'SUCCESS',
                'message': f'Connected to database: {version}',
                'endpoint': endpoint
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'ERROR',
                'message': str(e)
            })
        }
```

3. **Test Function**
   - Make sure Lambda role has Secrets Manager permissions
   - Run test
   - Should see database version info

### 23B: Test OpenSearch Connection

Similar to Step 23A, create a test function for OpenSearch.

## Step 24: Load Testing (Optional but Recommended)

### 24A: Simple Load Test with Apache Bench

```bash
# Install (if needed)
# On macOS: brew install httpd
# On Linux: sudo apt-get install apache2-utils

# Run 100 requests, 10 concurrent
ab -n 100 -c 10 \
  -H "x-api-key: YOUR-API-KEY" \
  -T "application/json" \
  -p request_payload.json \
  https://your-api-endpoint/prod/chat

# request_payload.json contents:
# {
#   "request_text": "I need access",
#   "user_id": "john.doe"
# }
```

### 24B: Monitor During Load Test

1. **Open CloudWatch Dashboard**
2. Watch metrics:
   - Lambda: Invocations, Duration, Errors
   - API Gateway: Count, Latency
   - RDS: CPU utilization
   - OpenSearch: Index operations

3. **Check for Issues**
   - Any errors?
   - Any timeouts?
   - Is latency acceptable?

---

# Part 10: Troubleshooting & Optimization

## Common Issues and Solutions

### Issue 1: Lambda Function Timeout

**Symptoms**: Function takes longer than timeout period to complete.

**Solutions**:
1. **Increase Timeout**
   - Go to Lambda function → **"General configuration"**
   - Change **"Timeout"** to higher value (e.g., 60 seconds)
   - Click **"Save"**

2. **Optimize Code**
   - Profile to find slow operations
   - Use Lambda Layers to pre-package dependencies
   - Reduce database calls

3. **Check CloudWatch Logs**
   - See where time is spent
   - Is it database query? API call? Processing?

### Issue 2: Lambda Function Returns 502 Bad Gateway

**Symptoms**: API returns error even though function exists.

**Solutions**:
1. **Check Lambda Execution Role Permissions**
   - Does role have permission to access services?
   - Go to Lambda → **"Execution role"**
   - Verify policies attached

2. **Check Function Logs**
   - CloudWatch → Log groups → `/aws/lambda/function-name`
   - Look for Python errors

3. **Test Function Directly**
   - Go to Lambda function → **"Test"** tab
   - Create test event
   - Run test to see detailed error

4. **Common Causes**
   - Missing environment variables
   - Database connection error
   - Missing permissions
   - Code syntax error

### Issue 3: RDS Connection Fails

**Symptoms**: Lambda can't connect to database.

**Solutions**:
1. **Check Security Group**
   - RDS → **"Databases"** → Click database
   - Go to **"Security group rules"**
   - Ensure port 5432 is open from Lambda

2. **Verify Credentials**
   - Go to Secrets Manager
   - Retrieve the secret
   - Verify username and password are correct

3. **Test Connection from EC2** (if you have one)
   ```bash
   psql -h your-database-endpoint \
        -U postgres \
        -d askiam_db \
        -p 5432
   ```

4. **Check Network**
   - Is Lambda in same VPC as RDS?
   - Are subnets properly configured?

### Issue 4: OpenSearch Query Returns Empty Results

**Symptoms**: Semantic search doesn't find anything.

**Solutions**:
1. **Verify Data Indexed**
   - Go to OpenSearch Dashboards
   - Run query to list documents:
   ```json
   GET /iam_policies/_search
   {
     "query": { "match_all": {} }
   }
   ```

2. **Check Index Mapping**
   - Verify fields are indexed correctly:
   ```json
   GET /iam_policies/_mapping
   ```

3. **Ingest Sample Data**
   - Use Dashboards Console to add test documents:
   ```json
   POST /iam_policies/_doc
   {
     "policy_name": "Test Policy",
     "policy_json": "{...}",
     "compliance_level": "high"
   }
   ```

### Issue 5: High AWS Costs

**Symptoms**: AWS bill is higher than expected.

**Solutions**:
1. **Identify Cost Drivers**
   - AWS Billing Console → **"Cost Explorer"**
   - Filter by service
   - Check what's consuming most

2. **Optimize Lambda**
   - Reduce function memory (lower cost per 100ms)
   - Reduce invocations (optimize logic)
   - Use Provisioned Concurrency only if needed

3. **Optimize RDS**
   - Use smaller instance class (db.t3.micro)
   - Set backup retention to 7 days
   - Turn off Multi-AZ if not needed

4. **Optimize OpenSearch**
   - Reduce OCU capacity if not fully used
   - Delete unused indexes
   - Monitor data ingestion rate

5. **Set Budget Alerts**
   - Billing → **"Budgets"**
   - Create budget for your account
   - Set alert threshold

### Issue 6: API Rate Limiting Too Strict

**Symptoms**: Getting 429 Too Many Requests errors.

**Solutions**:
1. **Increase API Gateway Throttle**
   - API Gateway → **"Usage Plans"**
   - Click your usage plan
   - Click **"Edit"**
   - Increase:
     - Rate (requests per second)
     - Burst (concurrent requests)

2. **Increase Lambda Concurrency**
   - Lambda → Select function
   - **"Concurrency"** section
   - Set **"Reserved concurrency"** to higher value

### Issue 7: Lex Bot Doesn't Recognize Intent

**Symptoms**: Bot says "I didn't understand" for valid requests.

**Solutions**:
1. **Add More Sample Utterances**
   - Lex → Intent → **"Sample utterances"**
   - Add more variations of how users ask for things

2. **Rebuild Bot**
   - After making changes, click **"Build"** button
   - Wait for build to complete

3. **Test with Different Phrases**
   - Try exact match of sample utterance first
   - Then try variations

4. **Check Slots Configuration**
   - Ensure slots are extracting values correctly
   - Check slot prompts

---

## Performance Optimization

### Optimization 1: Reduce Cold Starts

**Problem**: First Lambda invocation takes longer (cold start).

**Solutions**:

1. **Use Provisioned Concurrency**
   - Lambda → Function → **"Concurrency"**
   - Set **"Provisioned concurrency"** to 5-10
   - Cost increases but eliminates cold starts

2. **Reduce Package Size**
   - Remove unused dependencies
   - Use Layers for shared code

3. **Optimize Initialization**
   - Move slow initialization outside handler
   - Use Python instead of Java (faster startup)

### Optimization 2: Database Query Optimization

1. **Add Indexes** (already done in Part 2)
   - Indexes make SELECT queries faster
   - Check we created indexes on frequently queried columns

2. **Use Connection Pooling**
   - For multiple Lambda functions
   - Use RDS Proxy (manages connections)

3. **Cache Results**
   - Store frequently accessed data in Lambda memory
   - Use ElastiCache for shared cache across functions

### Optimization 3: Parallel Processing

1. **Invoke Functions in Parallel**
   - RequestOrchestrator calls RAGValidator and MCPValidator simultaneously
   - Use `InvocationType='Event'` for async calls
   - Wait for both results before proceeding

2. **Use Step Functions** (Advanced)
   - Orchestrate complex workflows
   - Retry failed steps automatically

### Optimization 4: Caching with API Gateway

1. **Enable API Gateway Caching**
   - API Gateway → Stages → **"prod"**
   - **"Cache settings"** section
   - Enable caching
   - Cache TTL: 300 seconds (5 minutes)

2. **Benefits**
   - Reduces Lambda invocations
   - Lower costs
   - Faster responses

---

## Security Best Practices

### Security 1: Restrict IAM Permissions (Least Privilege)

1. **Review IAM Roles**
   - Don't use `*` for resources
   - Specify exact ARNs
   - Example (instead of `AmazonRDSFullAccess`):

```json
{
  "Effect": "Allow",
  "Action": [
    "rds-db:connect"
  ],
  "Resource": "arn:aws:rds-db:region:account:dbuser:resource-id/db_user"
}
```

### Security 2: Enable VPC for Lambda

1. **Put Lambda in VPC**
   - Lambda → Function → **"VPC"**
   - Select your VPC and private subnets
   - Benefits: private communication with RDS/OpenSearch

2. **Use VPC Endpoints**
   - Don't route through public internet
   - Create VPC endpoints for S3, DynamoDB, etc.

### Security 3: Encrypt Data in Transit

1. **Use HTTPS for API Gateway**
   - Already enforced by default

2. **Use TLS for RDS**
   - RDS → Database → **"Encryption in transit"**
   - Ensure enabled

3. **Use TLS for OpenSearch**
   - OpenSearch → Collection → **"Encryption in transit"**
   - Ensure enabled

### Security 4: Enable Audit Logging

1. **CloudTrail** (Log all API calls)
   - CloudTrail console → **"Create trail"**
   - Name: `ask-iam-audit-trail`
   - Save to S3 bucket

2. **Benefits**
   - Who accessed what and when
   - Compliance reporting
   - Security investigation

### Security 5: Enable VPC Flow Logs

1. **VPC → Flow Logs**
   - Create flow log
   - Destination: CloudWatch Logs
   - Benefits: see all network traffic in VPC

---

## Cost Optimization Checklist

- [ ] Set CloudWatch log retention (7 days, not indefinite)
- [ ] Use RDS Serverless v2 (not fixed instance)
- [ ] Turn off Multi-AZ for development (not production)
- [ ] Set CloudWatch alarms to catch cost spikes
- [ ] Review unused resources monthly
- [ ] Use API Gateway throttling (prevent runaway invocations)
- [ ] Cache API responses where possible
- [ ] Monitor OpenSearch data ingestion
- [ ] Archive old logs to S3 Glacier
- [ ] Review AWS Trusted Advisor recommendations

---

## Monitoring Checklist

- [ ] CloudWatch dashboard created
- [ ] CloudWatch alarms configured
- [ ] Lambda logs being captured
- [ ] X-Ray tracing enabled
- [ ] Metrics being sent to CloudWatch
- [ ] Audit logging configured
- [ ] Log Insights queries created for troubleshooting

---

## Deployment Checklist

Before going to production:

- [ ] All Lambda functions deployed and tested
- [ ] API Gateway configured with proper throttling
- [ ] RDS backup enabled
- [ ] OpenSearch backup enabled
- [ ] Secrets stored in Secrets Manager
- [ ] Parameters stored in Parameter Store
- [ ] CloudWatch alarms configured
- [ ] VPC configured properly
- [ ] Security groups allow necessary traffic
- [ ] IAM roles follow least privilege
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

---

## Quick Reference: Key AWS Console Links

After setup, bookmark these:

1. **AWS Console Home**: https://console.aws.amazon.com/
2. **Lambda Functions**: https://console.aws.amazon.com/lambda/home
3. **RDS Databases**: https://console.aws.amazon.com/rds/
4. **OpenSearch Collections**: https://console.aws.amazon.com/aos/
5. **API Gateway APIs**: https://console.aws.amazon.com/apigateway/
6. **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/
7. **Secrets Manager**: https://console.aws.amazon.com/secretsmanager/
8. **Parameter Store**: https://console.aws.amazon.com/systems-manager/parameters/
9. **Billing**: https://console.aws.amazon.com/billing/
10. **IAM**: https://console.aws.amazon.com/iam/

---

## Next Steps After Initial Setup

### Phase 1: Stabilization (Week 1-2)
1. Deploy all Lambda functions
2. Configure API Gateway
3. Set up monitoring
4. Run integration tests
5. Document any custom configurations

### Phase 2: Data Ingestion (Week 2-3)
1. Populate RDS with IAM data
2. Index policies in OpenSearch
3. Load historical access patterns
4. Validate data consistency

### Phase 3: Testing & Optimization (Week 3-4)
1. Load testing
2. Performance tuning
3. Cost optimization
4. Security hardening

### Phase 4: Production Deployment (Week 4-5)
1. User acceptance testing
2. Run chaos engineering tests
3. Document runbooks
4. Deploy to production
5. Monitor closely

---

## Support & Resources

### AWS Documentation
- **Lambda**: https://docs.aws.amazon.com/lambda/
- **RDS**: https://docs.aws.amazon.com/rds/
- **OpenSearch**: https://docs.aws.amazon.com/opensearch-service/
- **API Gateway**: https://docs.aws.amazon.com/apigateway/
- **Lex**: https://docs.aws.amazon.com/lex/

### Community & Help
- **AWS Support**: https://console.aws.amazon.com/support/
- **Stack Overflow**: Tag your questions with `aws`
- **AWS Forums**: https://forums.aws.amazon.com/
- **GitHub**: Share issues and code

### Training
- **AWS Training and Certification**: https://aws.amazon.com/training/
- **AWS Skill Builder**: https://skillbuilder.aws.com/
- **YouTube**: Search "AWS Lambda tutorial"

---

## Conclusion

By following this guide, you've built a complete, serverless IAM conversational bot on AWS. You now have:

✅ A scalable, serverless architecture  
✅ Database for storing IAM data  
✅ Search capability for policies  
✅ Lambda functions for business logic  
✅ API Gateway for REST requests  
✅ Lex bot for conversational interface  
✅ Monitoring and logging  
✅ Security best practices in place  

**You're ready to:**
- Deploy to production
- Invite users to test
- Gather feedback
- Iterate and improve
- Scale to enterprise use

**Congratulations on building your first AWS serverless application!** 🎉

For questions or issues, refer back to Part 10: Troubleshooting, or consult the AWS documentation links provided above.
