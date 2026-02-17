# AskIAM Team Setup Guide - For Both Developers

## Quick Overview

This guide provides clear, step-by-step instructions for setting up two developers on a single AWS account with proper security and role-based access control.

```
Single AWS Account (ask-iam-prod)
│
├── Developer 1: Backend Services (ask-iam-dev)
│   ├─ IAM Role: ask-iam-backend-developer
│   ├─ Can: Create/manage Lambda, execute RDS queries, manage Lex, API Gateway
│   └─ Cannot: Modify infrastructure, create databases, manage IAM
│
└── Developer 2: Infrastructure & DevOps (dev-2-infra)
    ├─ IAM Role: ask-iam-infra-developer
    ├─ Can: Manage VPC, RDS, OpenSearch, CloudWatch, Secrets Manager
    └─ Cannot: Modify user access, delete critical resources, manage Lambda
```

---

## STEP 0: Admin Pre-Work (Before Developers Can Start)

**Admin/Owner completes these steps ONCE:**

### 0.1: AWS Account Setup
```bash
# Create AWS account: https://aws.amazon.com/
# Account Name: ask-iam-prod
# Enable MFA on root account
# Create admin IAM user: askiam-admin
# Enable MFA on admin user
```

### 0.2: Create Developer 1 (ask-iam-dev)
```
Username: ask-iam-dev
Role: ask-iam-backend-developer
IAM Policy: Lambda, RDS, Lex, API Gateway access (restricted from infrastructure)
MFA: MANDATORY
Email: [Backend Developer Email]
```

### 0.3: Create Developer 2 (dev-2-infra)
```
Username: dev-2-infra
Role: ask-iam-infra-developer
IAM Policy: VPC, RDS, OpenSearch, CloudWatch, Secrets Manager (restricted from user management)
MFA: MANDATORY
Email: [Infrastructure Developer Email]
```

### 0.4: GitHub Repository Setup
1. Go to https://github.com/new
2. Create private repository: `AskIAM-Assistant`
3. Add both developers as collaborators (Maintain role)
4. Enable branch protection on `main` branch
5. Share repository URL and add developers

### 0.5: Send Developers Their Credentials

**For Developer 1 (Backend):**
```
AWS Console Sign-In URL: https://[ACCOUNT-ID].signin.aws.amazon.com/console/
Username: ask-iam-dev
Temporary Password: [Generated - they must change on first login]
GitHub Repository: [URL]
AWS Region: [e.g., us-east-1]
Account ID: [12-digit number]
```

**For Developer 2 (Infrastructure):**
```
AWS Console Sign-In URL: https://[ACCOUNT-ID].signin.aws.amazon.com/console/
Username: dev-2-infra
Temporary Password: [Generated - they must change on first login]
GitHub Repository: [URL]
AWS Region: [e.g., us-east-1]
Account ID: [12-digit number]
```

---

## STEP 1: Developer 1 Setup (Backend Services)

**Developer 1 performs these steps:**

### 1.1: Initial AWS Console Access

```bash
# Open URL from admin
https://[ACCOUNT-ID].signin.aws.amazon.com/console/

# Sign in with:
# Username: ask-iam-dev
# Password: [temporary password]

# System will prompt to change password
# Create NEW strong password (save in 1Password/LastPass)
```

### 1.2: Enable MFA (REQUIRED)

```bash
# In AWS Console:
# 1. Click account name (top right)
# 2. Security credentials
# 3. Multi-factor authentication (MFA)
# 4. Assign MFA device
# 5. Choose "Virtual MFA device"
# 6. Use Google Authenticator or Authy
# 7. Scan QR code
# 8. Save recovery codes securely
```

### 1.3: Assume Backend Developer Role

```bash
# After MFA is set up:
# 1. Click account name (top right)
# 2. Select "Switch role"
# 3. Account: [ACCOUNT-ID]
# 4. Role: ask-iam-backend-developer
# 5. Display name: Backend-Dev (optional)
# 6. Click "Switch role"

# Now you're in the Backend Developer role
# You should see: Lambda, RDS, Lex, API Gateway, CloudWatch
# You should NOT see: IAM, VPC, EC2 (Security Groups)
```

### 1.4: Set Up AWS CLI Locally

```bash
# Install AWS CLI (if not already installed)
# macOS: brew install awscli
# Linux: sudo apt-get install awscli
# Windows: https://aws.amazon.com/cli/

# Configure AWS CLI
aws configure --profile ask-iam-dev

# When prompted, enter:
# AWS Access Key ID: [Get from admin or create in IAM]
# AWS Secret Access Key: [Get from admin or create in IAM]
# Default region name: us-east-1 (or your region)
# Default output format: json

# Test connection
aws sts get-caller-identity --profile ask-iam-dev

# Output should show:
# {
#     "UserId": "AIDAQ...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/ask-iam-dev"
# }
```

### 1.5: Clone GitHub Repository

```bash
# Create development folder
mkdir ~/Projects
cd ~/Projects

# Clone repository
git clone https://github.com/[ORG]/AskIAM-Assistant.git
cd AskIAM-Assistant

# Configure Git
git config user.name "Your Full Name"
git config user.email "your.email@company.com"

# Verify configuration
git config --list | grep user
```

### 1.6: Set Up Local Development Environment

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Common packages for backend development:
pip install boto3 psycopg2-binary requests pytest pylint black

# Create initial directory structure
mkdir -p backend/{orchestrator,entity-extractor,rag-validator,mcp-validator,audit-logger}
mkdir -p tests
mkdir -p docs

# Verify everything works
python --version  # Should be 3.11+
aws sts get-caller-identity --profile ask-iam-dev
```

### 1.7: Verify Backend Developer Permissions

```bash
# You should be able to:

# ✅ List Lambda functions
aws lambda list-functions --profile ask-iam-dev

# ✅ Describe RDS database
aws rds describe-db-instances --profile ask-iam-dev

# ✅ List Lex bots
aws lex-models get-bots --profile ask-iam-dev

# ✅ Get CloudWatch logs
aws logs describe-log-groups --profile ask-iam-dev

# ❌ This should FAIL (IAM access denied):
aws iam list-users --profile ask-iam-dev
# Error: AccessDenied

# ❌ This should FAIL (VPC access denied):
aws ec2 describe-vpcs --profile ask-iam-dev
# Error: UnauthorizedOperation
```

### 1.8: Create Your First Feature Branch

```bash
# Create feature branch for your first work
git checkout -b feature/backend-setup

# Create a simple Python file
cat > backend/README.md << 'EOF'
# Backend Services

This folder contains Lambda functions for the AskIAM bot.

## Functions
- orchestrator: Main entry point
- entity-extractor: Extract user intents
- rag-validator: Semantic validation
- mcp-validator: Database validation
- audit-logger: Audit logging

## Development
See main README for setup instructions.
EOF

# Commit your changes
git add backend/README.md
git commit -m "docs: add backend services README"

# Push to GitHub
git push -u origin feature/backend-setup

# Create Pull Request on GitHub
# Go to: https://github.com/[ORG]/AskIAM-Assistant/pulls
# Click "New Pull Request"
# Base: main, Compare: feature/backend-setup
# Add title and description
# Request review from dev-2-infra
```

---

## STEP 2: Developer 2 Setup (Infrastructure & DevOps)

**Developer 2 performs these steps:**

### 2.1: Initial AWS Console Access

```bash
# Open URL from admin
https://[ACCOUNT-ID].signin.aws.amazon.com/console/

# Sign in with:
# Username: dev-2-infra
# Password: [temporary password]

# System will prompt to change password
# Create NEW strong password (save in 1Password/LastPass)
```

### 2.2: Enable MFA (REQUIRED)

```bash
# In AWS Console:
# 1. Click account name (top right)
# 2. Security credentials
# 3. Multi-factor authentication (MFA)
# 4. Assign MFA device
# 5. Choose "Virtual MFA device"
# 6. Use Google Authenticator or Authy
# 7. Scan QR code
# 8. Save recovery codes securely
```

### 2.3: Assume Infrastructure Developer Role

```bash
# After MFA is set up:
# 1. Click account name (top right)
# 2. Select "Switch role"
# 3. Account: [ACCOUNT-ID]
# 4. Role: ask-iam-infra-developer
# 5. Display name: Infra-Dev (optional)
# 6. Click "Switch role"

# Now you're in the Infrastructure Developer role
# You should see: VPC, EC2, RDS, OpenSearch, CloudWatch, Secrets Manager
# You should NOT see: Lambda, Lex, API Gateway (read-only at best)
```

### 2.4: Set Up AWS CLI Locally

```bash
# Configure AWS CLI with infrastructure profile
aws configure --profile dev-2-infra

# When prompted, enter:
# AWS Access Key ID: [Get from admin or create in IAM]
# AWS Secret Access Key: [Get from admin or create in IAM]
# Default region name: us-east-1 (or your region)
# Default output format: json

# Test connection
aws sts get-caller-identity --profile dev-2-infra

# Output should show:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/dev-2-infra"
# }
```

### 2.5: Clone GitHub Repository

```bash
# Create development folder
mkdir ~/Projects
cd ~/Projects

# Clone repository
git clone https://github.com/[ORG]/AskIAM-Assistant.git
cd AskIAM-Assistant

# Configure Git
git config user.name "Your Full Name"
git config user.email "your.email@company.com"

# Verify configuration
git config --list | grep user
```

### 2.6: Set Up Local Development Environment

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies for infrastructure tools
pip install boto3 pyyaml jinja2 pytest pylint

# Create infrastructure directory structure
mkdir -p infrastructure/{iam-roles,security-groups,rds,opensearch,cloudwatch}
mkdir -p database/{migrations,sample-data}
mkdir -p tests

# Verify everything works
python --version  # Should be 3.11+
aws sts get-caller-identity --profile dev-2-infra
```

### 2.7: Verify Infrastructure Developer Permissions

```bash
# You should be able to:

# ✅ Create VPC
aws ec2 describe-vpcs --profile dev-2-infra

# ✅ Create Security Groups
aws ec2 describe-security-groups --profile dev-2-infra

# ✅ Manage RDS
aws rds describe-db-instances --profile dev-2-infra

# ✅ Manage OpenSearch
aws opensearchserverless list-collections --profile dev-2-infra

# ✅ Manage CloudWatch
aws cloudwatch describe-alarms --profile dev-2-infra

# ✅ Manage Secrets
aws secretsmanager list-secrets --profile dev-2-infra

# ❌ This should FAIL (Cannot delete users):
aws iam delete-user --user-name test --profile dev-2-infra
# Error: AccessDenied

# ❌ This should FAIL (Cannot access Lambda directly):
aws lambda list-functions --profile dev-2-infra
# Error: AccessDenied or empty list
```

### 2.8: Create Your First Feature Branch

```bash
# Create feature branch for infrastructure setup
git checkout -b feature/infrastructure-setup

# Create infrastructure README
cat > infrastructure/README.md << 'EOF'
# Infrastructure & DevOps

This folder contains infrastructure-as-code and configuration for AskIAM.

## Components
- iam-roles: Lambda execution roles, developer roles
- security-groups: VPC security group rules
- rds: RDS database configuration
- opensearch: OpenSearch collection setup
- cloudwatch: Monitoring dashboards and alarms

## Prerequisites
- AWS CLI configured with dev-2-infra profile
- Appropriate IAM permissions
- Python 3.11+

## Deployment
See deployment guide for instructions.
EOF

# Create database README
cat > database/README.md << 'EOF'
# Database Setup

## Migrations
SQL migration scripts for database setup.

## Sample Data
Sample IAM data for testing.
EOF

# Commit your changes
git add infrastructure/README.md database/README.md
git commit -m "docs: add infrastructure and database documentation"

# Push to GitHub
git push -u origin feature/infrastructure-setup

# Create Pull Request on GitHub
# Go to: https://github.com/[ORG]/AskIAM-Assistant/pulls
# Click "New Pull Request"
# Base: main, Compare: feature/infrastructure-setup
# Add title and description
# Request review from ask-iam-dev
```

---

## STEP 3: Collaborate & Integrate

### 3.1: First Integration Sync

**Developer 1 & 2 sync together (meeting or async):**

```bash
# Developer 1 shares:
- "I've created feature/backend-setup with Lambda structure"
- "I need RDS endpoint and credentials"
- "I need OpenSearch collection endpoint"

# Developer 2 responds:
- "I'll create infrastructure/feature-opensearch-setup first"
- "Then I'll create RDS and share endpoints"

# Together decide:
- Who deploys what first
- Testing order
- Integration points
```

### 3.2: Code Review Process

**Developer 1 creates PR → Developer 2 reviews:**

```bash
# Developer 2 checks:
# 1. Does code follow Python best practices?
# 2. Are there security issues?
# 3. Are IAM permissions correct?
# 4. Are error messages helpful?
# 5. Is there test coverage?

# Developer 2 comments on PR:
# "Can you add error handling for database connection?"
# "Please add unit tests for this function"

# Developer 1 updates code:
git add backend/orchestrator/lambda_function.py
git commit -m "feat: add error handling for RDS connections"
git push origin feature/backend-setup

# Commits automatically appear in PR

# Developer 2 approves:
# Click "Approve" on PR
```

**Developer 2 creates PR → Developer 1 reviews:**

```bash
# Developer 1 checks:
# 1. Does security group configuration make sense?
# 2. Are ports and protocols correct?
# 3. Is encryption enabled?
# 4. Are backup settings appropriate?

# Developer 1 approves infrastructure PR
```

### 3.3: Merge to Main

```bash
# Admin/Lead reviews both PRs
# Admin merges both PRs to main

# Both developers sync:
git checkout main
git pull origin main

# Delete your feature branches:
git branch -d feature/backend-setup
git branch -d feature/infrastructure-setup
```

### 3.4: Deploy to AWS

**After merging to main:**

```bash
# Developer 2 deploys infrastructure first:
cd infrastructure
aws cloudformation create-stack \
  --stack-name ask-iam-prod \
  --template-body file://template.yaml \
  --profile dev-2-infra

# Once infrastructure is ready, Developer 1 deploys backend:
cd backend/orchestrator
zip lambda_function.zip lambda_function.py
aws lambda update-function-code \
  --function-name ask-iam-orchestrator \
  --zip-file fileb://lambda_function.zip \
  --profile ask-iam-dev

# Both test end-to-end:
aws lambda invoke \
  --function-name ask-iam-orchestrator \
  --payload '{"request_text": "test"}' \
  --profile ask-iam-dev \
  response.json
```

---

## STEP 4: Security & Compliance Checklist

### Code Security
- [ ] No credentials in Git (use environment variables)
- [ ] All passwords stored in Secrets Manager
- [ ] All API keys encrypted
- [ ] Security scanning enabled (bandit, sonarqube)
- [ ] Dependency vulnerabilities checked (pip audit)

### AWS Security
- [ ] MFA enabled on both IAM users
- [ ] VPC security groups properly configured
- [ ] RDS encryption enabled
- [ ] OpenSearch encryption enabled
- [ ] CloudTrail logging enabled
- [ ] CloudWatch logs configured
- [ ] IAM roles follow least privilege principle

### Access Control
- [ ] Developer 1 cannot modify infrastructure
- [ ] Developer 2 cannot access Lambda code
- [ ] Admin can audit all actions via CloudTrail
- [ ] All actions logged to CloudWatch
- [ ] Access keys rotated every 90 days

### Compliance & Monitoring
- [ ] CloudWatch alarms configured
- [ ] Daily standup on issues/blockers
- [ ] Weekly security review
- [ ] Monthly access audit
- [ ] Quarterly disaster recovery test

---

## STEP 5: Daily Development Workflow

### Morning Standup (5 min)

```markdown
## Standup - [Date]

### Developer 1 (Backend)
**Yesterday:**
- Deployed orchestrator Lambda v1.2.0
- Added error handling for RDS connections

**Today:**
- Implement entity-extractor Lambda
- Test with sample data

**Blockers:**
- Waiting for OpenSearch endpoint from Dev-2

### Developer 2 (Infrastructure)
**Yesterday:**
- Created RDS PostgreSQL instance
- Configured security groups

**Today:**
- Create OpenSearch collection
- Set up CloudWatch dashboards

**Blockers:**
- None

### Action Items
- [ ] Dev-2: Share RDS endpoint by EOD
- [ ] Dev-1: Test Lambda → RDS connection
- [ ] Both: Review open PRs
```

### Throughout the Day

```bash
# Make small commits frequently
git add <file>
git commit -m "feat: short description"
git push origin <your-branch>

# Create PR when feature is complete
# Request review from other developer
```

### End of Day

```bash
# Push all work
git push origin <your-branch>

# Update Slack/Email with progress
# "Pushed [number] commits to feature/xyz"
```

---

## STEP 6: Deployment Checklist

**Before deploying to production:**

```bash
# Developer 1 checklist:
- [ ] All Lambda functions tested locally
- [ ] Unit tests pass: pytest tests/
- [ ] Linting passes: pylint backend/
- [ ] No secrets in code
- [ ] CloudWatch logs configured
- [ ] Error handling implemented
- [ ] Performance acceptable (<5s)
- [ ] Code reviewed by Dev-2

# Developer 2 checklist:
- [ ] VPC configured and tested
- [ ] RDS backed up
- [ ] OpenSearch secured
- [ ] Security groups validated
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Encryption enabled
- [ ] Code reviewed by Dev-1

# Both checklist:
- [ ] Integration tests pass
- [ ] End-to-end test works
- [ ] Documentation updated
- [ ] GitHub PR approved
- [ ] Ready for production
```

---

## STEP 7: Troubleshooting

### Lambda Function Fails

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/ask-iam-orchestrator --follow --profile ask-iam-dev

# Check IAM permissions
aws iam simulate-custom-policy \
  --policy-input-list file://policy.json \
  --action-names lambda:InvokeFunction \
  --resource-arns "arn:aws:lambda:*:*:function:*" \
  --profile ask-iam-dev
```

### RDS Connection Issues

```bash
# Check security group
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --profile dev-2-infra

# Test connection from Lambda VPC
psql -h <rds-endpoint> -U postgres -d askiam_db
```

### OpenSearch Problems

```bash
# Check collection status
aws opensearchserverless list-collections --profile dev-2-infra

# Check access policies
aws opensearchserverless get-access-policy \
  --name ask-iam-collection \
  --profile dev-2-infra
```

---

## Contact & Support

### Team Communication
- **Slack**: #ask-iam-dev
- **Email**: [team-email@company.com]
- **Wiki**: [Documentation-URL]

### AWS Support
- **Console**: https://console.aws.amazon.com/support/
- **Docs**: https://docs.aws.amazon.com/
- **Forums**: https://forums.aws.amazon.com/

### Key Contacts
- **Admin/Owner**: [Name, Email]
- **Developer 1**: [Name, Email]
- **Developer 2**: [Name, Email]

---

## Quick Reference

### AWS Console URLs
```
Main: https://console.aws.amazon.com/
Lambda: https://console.aws.amazon.com/lambda/
RDS: https://console.aws.amazon.com/rds/
OpenSearch: https://console.aws.amazon.com/aos/
CloudWatch: https://console.aws.amazon.com/cloudwatch/
IAM: https://console.aws.amazon.com/iam/
```

### Common AWS CLI Commands

```bash
# List Lambda functions
aws lambda list-functions --profile ask-iam-dev

# Get RDS endpoint
aws rds describe-db-instances --query 'DBInstances[0].Endpoint.Address' --profile dev-2-infra

# View CloudWatch logs
aws logs tail /aws/lambda/ --follow --profile ask-iam-dev

# Test IAM role
aws sts get-caller-identity --profile ask-iam-dev
```

### Git Commands

```bash
# Create feature branch
git checkout -b feature/my-feature

# View changes
git status
git diff

# Commit changes
git add <files>
git commit -m "feat: description"

# Push to GitHub
git push -u origin feature/my-feature

# Update from main
git fetch origin
git rebase origin/main
# Or: git merge origin/main

# Delete branch
git branch -d feature/my-feature
```

---

## Final Notes

**Remember:**
- ✅ Always use Git for version control
- ✅ Always enable MFA on AWS accounts
- ✅ Always store secrets securely
- ✅ Always review code before merging
- ✅ Always test before deploying
- ✅ Always document your changes

**Never:**
- ❌ Never commit credentials to Git
- ❌ Never use root AWS account
- ❌ Never skip MFA setup
- ❌ Never force push to main
- ❌ Never deploy without testing

---

**Created**: [Date]
**Updated**: [Date]
**Version**: 1.0
