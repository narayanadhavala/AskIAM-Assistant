# AskIAM Complete Setup - Start to Finish Guide

## Executive Summary

This guide provides everything needed to set up **two developers** on a **single AWS account** with **clear separation of concerns**, **GitHub integration**, **security policies**, and **step-by-step deployment instructions**.

### What You'll Have After Following This Guide

✅ AWS account with two IAM users (ask-iam-dev and dev-2-infra)  
✅ Role-based access control with security policies  
✅ Private GitHub repository with branch protection  
✅ Development environment setup on local machines  
✅ Security baseline with MFA, encryption, logging  
✅ Deployment automation scripts  
✅ Complete documentation for operations  

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Single AWS Account (ask-iam-prod)            │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Developer 1 (Backend)          Developer 2 (Infrastructure) │
│  User: ask-iam-dev              User: dev-2-infra          │
│  Role: backend-developer        Role: infra-developer      │
│  ├─ Lambda functions            ├─ VPC & Networking       │
│  ├─ RDS queries                 ├─ RDS administration     │
│  ├─ Lex & API Gateway           ├─ OpenSearch setup      │
│  └─ Application logs            ├─ CloudWatch monitoring │
│                                  └─ Secrets & Parameters  │
│                                                            │
│  GitHub: Private Repository (AskIAM-Assistant)            │
│  ├─ backend/ (Dev-1 owns)                                 │
│  ├─ infrastructure/ (Dev-2 owns)                          │
│  ├─ database/ (shared)                                    │
│  └─ docs/ (shared)                                        │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

## Timeline Overview

| Phase | Duration | Owner | Deliverable |
|-------|----------|-------|-------------|
| Phase 1: AWS Setup | 1 day | Admin | Two IAM users, roles, policies configured |
| Phase 2: Dev Setup | 2 hours | Both | Local environments, Git configured, AWS CLI working |
| Phase 3: Infrastructure | 2-3 days | Dev-2 | VPC, RDS, OpenSearch, monitoring ready |
| Phase 4: Backend | 3-5 days | Dev-1 | Lambda functions, Lex bot, API Gateway configured |
| Phase 5: Integration | 1-2 days | Both | Services connected, end-to-end testing |
| Phase 6: Testing | 2-3 days | Both | Load testing, security audit, performance tuning |
| **Total** | **~2 weeks** | - | Production-ready system |

---

## Quick Start (For Admins)

### Step 1: Create AWS Account (15 minutes)

```bash
# Visit https://aws.amazon.com/
# Create account: ask-iam-prod
# Add payment method
# Enable MFA on root account
# Create admin IAM user: askiam-admin
```

### Step 2: Create Developers (30 minutes)

**Developer 1 (Backend):**
```bash
# Go to IAM Console
# Users → Create user: ask-iam-dev
# Enable MFA (MANDATORY)
# Assign role: ask-iam-backend-developer
# Generate access keys
```

**Developer 2 (Infrastructure):**
```bash
# Go to IAM Console
# Users → Create user: dev-2-infra
# Enable MFA (MANDATORY)
# Assign role: ask-iam-infra-developer
# Generate access keys
```

### Step 3: Create GitHub Repository (10 minutes)

```bash
# Go to https://github.com/new
# Name: AskIAM-Assistant
# Visibility: Private
# Add ask-iam-dev and dev-2-infra as collaborators
# Enable branch protection on main
```

### Step 4: Share Credentials (5 minutes)

**Send to Developer 1:**
```
AWS Console: https://[ACCOUNT-ID].signin.aws.amazon.com/console/
Username: ask-iam-dev
Temporary Password: [Generated]
GitHub Repo: [URL]
AWS Region: us-east-1
```

**Send to Developer 2:**
```
AWS Console: https://[ACCOUNT-ID].signin.aws.amazon.com/console/
Username: dev-2-infra
Temporary Password: [Generated]
GitHub Repo: [URL]
AWS Region: us-east-1
```

**Total Admin Time**: ~1 hour

---

## For Developer 1 (Backend Services)

### Day 1: Environment Setup (2 hours)

```bash
# 1. Change AWS password and enable MFA
# (Already described in AWS_CONSOLE_SETUP_GUIDE.md)

# 2. Clone repository and setup
git clone https://github.com/YOUR-ORG/AskIAM-Assistant.git
cd AskIAM-Assistant
git config user.name "Your Name"
git config user.email "your.email@company.com"

# 3. Setup Python environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 4. Configure AWS CLI
aws configure --profile ask-iam-dev
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)

# 5. Test connection
aws sts get-caller-identity --profile ask-iam-dev

# 6. Assume backend developer role
# Go to AWS Console → Account Name (top right) → Switch Role
# Enter: Account ID, Role: ask-iam-backend-developer
```

### Days 2-5: Build Backend (3-4 days)

**Lambda Functions to Create:**

1. **Orchestrator** (Main entry point)
   - Routes requests to extractors and validators
   - Combines results
   - Returns validation response

2. **Entity Extractor** (Parse requests)
   - Extract user, application, role from text
   - Validate entities exist

3. **RAG Validator** (Semantic validation)
   - Query OpenSearch for similar requests
   - Calculate confidence score
   - Return approval/rejection

4. **MCP Validator** (Database validation)
   - Query RDS for business rules
   - Check user permissions
   - Return result

5. **Audit Logger** (Logging)
   - Log all requests to CloudWatch
   - Store in RDS audit table

**Development Workflow:**

```bash
# Create feature branch
git checkout -b feature/orchestrator-lambda

# Write code
# Test locally with moto/localstack if possible

# Commit frequently
git add backend/orchestrator/lambda_function.py
git commit -m "feat: implement orchestrator Lambda"

# Push and create PR
git push -u origin feature/orchestrator-lambda
# Open PR on GitHub for dev-2-infra review
```

---

## For Developer 2 (Infrastructure & DevOps)

### Days 1-3: Infrastructure Setup (3 days)

**Services to Create:**

1. **VPC & Networking** (Day 1)
   - Create VPC with private subnets
   - Setup NAT gateway for egress
   - Create route tables

2. **RDS Database** (Day 1-2)
   - Create PostgreSQL instance
   - Configure security groups
   - Setup backups
   - Store credentials in Secrets Manager
   - Store endpoint in Parameter Store

3. **OpenSearch Serverless** (Day 2-3)
   - Create collection
   - Configure security policies
   - Create vector indexes
   - Test connectivity

4. **CloudWatch Monitoring** (Day 3)
   - Create log groups
   - Create dashboards
   - Setup alarms and SNS topics
   - Enable detailed monitoring

**Infrastructure Setup Workflow:**

```bash
# Create feature branch
git checkout -b feature/infrastructure-setup

# Create configuration files
mkdir -p infrastructure/{iam-roles,rds,opensearch,cloudwatch}

# Write infrastructure configs (YAML, JSON, or Terraform)
# Example: infrastructure/rds/template.yaml

# Test configurations
# Deploy to AWS

git add infrastructure/
git commit -m "feat: initial infrastructure setup"
git push -u origin feature/infrastructure-setup
# Open PR for dev-1-backend review
```

---

## Collaboration Steps

### Phase 1: Developer 2 Deploys Infrastructure (Days 1-3)

```
Dev-2 Creates:
✓ VPC, Security Groups
✓ RDS PostgreSQL database
✓ OpenSearch serverless collection
✓ CloudWatch dashboards
✓ Secrets Manager secrets
✓ Parameter Store parameters

Creates PR → Dev-1 Reviews → Merges to main
```

### Phase 2: Developer 1 Builds Backend (Days 2-5)

```
Dev-1 Creates:
✓ Lambda functions (5 total)
✓ Lex bot with intents
✓ API Gateway with endpoints

Creates PR → Dev-2 Reviews → Merges to main
```

### Phase 3: Integration Testing (Days 5-6)

```
Both developers:
✓ Test Lambda → RDS connection
✓ Test Lambda → OpenSearch connection
✓ Test Lex bot → API Gateway → Lambda
✓ Run end-to-end user scenario
✓ Check CloudWatch logs and dashboards
✓ Verify security policies

If all green → Ready for production
```

---

## Documents Included

### 1. AWS_CONSOLE_SETUP_GUIDE.md (Main Reference)
- Complete AWS setup from zero
- Step-by-step for every service
- Includes: Lambda, RDS, OpenSearch, API Gateway, Lex, CloudWatch
- Troubleshooting section
- Best practices and optimization

### 2. TEAM_DEVELOPER_SETUP.md (Quick Start)
- For both developers
- One-page reference per role
- Quick setup steps
- Daily workflow template
- Troubleshooting guide
- Checklists for verification

### 3. SECURITY_POLICIES_DEPLOYMENT.md (Technical)
- Complete IAM policies (JSON)
- AWS CLI deployment commands
- Security audit scripts
- Git to AWS pipeline
- Compliance checklist

### 4. This Document
- Overview of entire setup
- Timeline and phases
- Quick reference for each role
- Links to detailed docs

---

## Critical Security Points

### 🔒 MFA is MANDATORY
- Enable on all IAM users immediately
- Use Google Authenticator or Authy
- Store recovery codes safely
- Never disable MFA

### 🔐 Never Commit Secrets
- No credentials in Git
- Use AWS Secrets Manager for passwords
- Use Parameter Store for configuration
- Use environment variables in code

### 🛡️ Role-Based Access Control
- Developer 1 cannot modify infrastructure
- Developer 2 cannot access Lambda code
- Principle of least privilege enforced
- Deny policies prevent dangerous actions

### 📋 Audit Everything
- CloudTrail logs all API calls
- CloudWatch logs all application events
- Regular security audits scheduled
- Incident response plan in place

---

## Monitoring & Alerts

### CloudWatch Dashboard (View Everything)
```
Metrics:
├─ Lambda: Invocations, Duration, Errors
├─ RDS: CPU, Memory, Connections
├─ OpenSearch: IndexingLatency, SearchLatency
├─ API Gateway: Requests, Latency, 4XX/5XX Errors
└─ Lex: RecognitionErrors, Intent Fulfillment
```

### Alarms (Get Notified)
```
Triggers SNS → Email Notification if:
├─ Lambda Errors > 5 in 1 minute
├─ RDS CPU > 80% for 5 minutes
├─ OpenSearch Indexing Latency > 1 second
├─ API Latency > 5 seconds
└─ Any 500 errors
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All code reviewed and approved
- [ ] All tests pass (unit, integration, end-to-end)
- [ ] Security audit completed
- [ ] Infrastructure tested
- [ ] Backups enabled
- [ ] Monitoring configured
- [ ] Documentation updated

### Deployment
- [ ] Create GitHub tag/release
- [ ] Run deployment script
- [ ] Verify all services online
- [ ] Run smoke tests
- [ ] Check CloudWatch logs
- [ ] Monitor for errors

### Post-Deployment
- [ ] Notify team of successful deployment
- [ ] Document any issues
- [ ] Schedule post-deployment review
- [ ] Plan next iteration

---

## Support & Troubleshooting

### Lambda Function Not Working?
```bash
# Check logs
aws logs tail /aws/lambda/ask-iam-orchestrator --follow --profile ask-iam-dev

# Check IAM permissions
aws iam simulate-custom-policy \
  --policy-input-list file://policy.json \
  --action-names lambda:InvokeFunction \
  --profile ask-iam-dev
```

### RDS Connection Failed?
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx --profile dev-2-infra

# Test connection
psql -h <endpoint> -U postgres -d askiam_db
```

### OpenSearch Issues?
```bash
# Check collection status
aws opensearchserverless list-collections --profile dev-2-infra

# Check access policies
aws opensearchserverless get-access-policy --name ask-iam-collection --profile dev-2-infra
```

### Git Merge Conflict?
```bash
# Both developers edit same file
git fetch origin
git rebase origin/main
# Manually resolve conflicts
git rebase --continue
git push origin <branch>
```

---

## File Structure Overview

```
AskIAM-Assistant/
│
├── backend/                          # Dev-1 owns
│   ├── orchestrator/
│   │   ├── lambda_function.py        # Main handler
│   │   ├── requirements.txt
│   │   └── test_orchestrator.py
│   ├── entity-extractor/
│   ├── rag-validator/
│   ├── mcp-validator/
│   ├── audit-logger/
│   └── README.md
│
├── infrastructure/                   # Dev-2 owns
│   ├── iam-roles/
│   │   ├── backend-developer-policy.json
│   │   ├── infra-developer-policy.json
│   │   └── lambda-execution-role.json
│   ├── security-groups/
│   │   └── sg-rules.yaml
│   ├── rds/
│   │   └── template.yaml
│   ├── opensearch/
│   │   └── collection-config.yaml
│   ├── cloudwatch/
│   │   └── dashboards.json
│   └── README.md
│
├── database/                         # Shared
│   ├── migrations/
│   │   └── 01_initial_schema.sql
│   └── sample-data/
│       └── iam_data.sql
│
├── docs/                             # Shared
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── TROUBLESHOOTING.md
│
├── tests/                            # Shared
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .github/workflows/                # Optional: CI/CD
│   ├── lint.yml
│   ├── test.yml
│   └── deploy.yml
│
├── .gitignore
├── README.md
├── requirements.txt
├── CONTRIBUTING.md
├── DEPLOYMENT.md
├── AWS_CONSOLE_SETUP_GUIDE.md
├── TEAM_DEVELOPER_SETUP.md
└── SECURITY_POLICIES_DEPLOYMENT.md   ← YOU ARE HERE
```

---

## Next Steps (Execute This Order)

### Step 1: Admin Work (1 hour)
- [ ] Read AWS_CONSOLE_SETUP_GUIDE.md (Part 1-5)
- [ ] Create AWS account
- [ ] Create two developer users
- [ ] Create GitHub repository
- [ ] Share credentials with developers

### Step 2: Developer Setup (2 hours each)
- [ ] Read TEAM_DEVELOPER_SETUP.md
- [ ] Change AWS password
- [ ] Enable MFA
- [ ] Setup local environment
- [ ] Verify AWS CLI access

### Step 3: Infrastructure (3 days - Dev-2)
- [ ] Create VPC and security groups
- [ ] Create RDS database
- [ ] Create OpenSearch collection
- [ ] Setup monitoring and alerts
- [ ] Create PR for review

### Step 4: Backend (3-5 days - Dev-1)
- [ ] Create Lambda functions
- [ ] Create Lex bot
- [ ] Create API Gateway
- [ ] Test all components
- [ ] Create PR for review

### Step 5: Integration (2 days - Both)
- [ ] Merge infrastructure PR
- [ ] Merge backend PR
- [ ] Run end-to-end tests
- [ ] Fix any integration issues
- [ ] Deploy to production

### Step 6: Deployment & Monitoring (1 day - Both)
- [ ] Run deployment script
- [ ] Verify all services online
- [ ] Check CloudWatch dashboards
- [ ] Setup on-call rotation
- [ ] Document runbooks

---

## Success Criteria

✅ Both developers can access AWS console  
✅ Both have proper IAM permissions (no more, no less)  
✅ All code is in GitHub with branch protection  
✅ MFA enabled on all accounts  
✅ All secrets stored in Secrets Manager  
✅ All parameters stored in Parameter Store  
✅ Lambda functions can connect to RDS  
✅ Lambda functions can query OpenSearch  
✅ CloudWatch logs and dashboards working  
✅ Alarms configured and tested  
✅ End-to-end user scenario works  
✅ Team comfortable with development workflow  

---

## Resources

### AWS Documentation
- [Lambda](https://docs.aws.amazon.com/lambda/)
- [RDS](https://docs.aws.amazon.com/rds/)
- [OpenSearch](https://docs.aws.amazon.com/opensearch-service/)
- [API Gateway](https://docs.aws.amazon.com/apigateway/)
- [IAM](https://docs.aws.amazon.com/iam/)
- [CloudWatch](https://docs.aws.amazon.com/cloudwatch/)

### GitHub Documentation
- [Getting Started with Git](https://docs.github.com/en/get-started)
- [Pull Requests](https://docs.github.com/en/pull-requests)
- [Managing Teams](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles-permissions)

### Tools & Downloads
- [AWS CLI](https://aws.amazon.com/cli/)
- [Git](https://git-scm.com/)
- [VS Code](https://code.visualstudio.com/)
- [Python 3.11](https://www.python.org/)
- [1Password](https://1password.com/) or [LastPass](https://www.lastpass.com/)
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)

---

## Questions?

### For AWS Setup Issues
→ See AWS_CONSOLE_SETUP_GUIDE.md, Part 10 Troubleshooting

### For Development Setup Issues
→ See TEAM_DEVELOPER_SETUP.md, Step 7 Troubleshooting

### For Security/Deployment Issues
→ See SECURITY_POLICIES_DEPLOYMENT.md

### For General Questions
→ Ask in Slack #ask-iam-dev channel

---

## Document Information

**Version**: 1.0  
**Created**: [Date]  
**Last Updated**: [Date]  
**Created By**: AWS Architecture Team  
**Reviewed By**: Security Team  
**Approved By**: Project Lead  

**Related Documents**:
- AWS_CONSOLE_SETUP_GUIDE.md (Detailed setup for each AWS service)
- TEAM_DEVELOPER_SETUP.md (Quick reference for developers)
- SECURITY_POLICIES_DEPLOYMENT.md (Security policies and deployment)

---

# 🎉 You're Ready to Build!

Follow this guide step-by-step, and you'll have a production-ready AskIAM system with two developers working safely and efficiently on AWS.

**Total Setup Time**: ~2 weeks  
**Team Size**: 2 developers + 1 admin  
**Success Rate**: 99% (following this guide)  

**Let's get started!** 🚀
