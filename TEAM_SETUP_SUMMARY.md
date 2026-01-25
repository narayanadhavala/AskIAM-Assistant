# AskIAM Team Setup Summary

## What Was Added to AWS_CONSOLE_SETUP_GUIDE.md

A comprehensive **Team Setup: Two-Developer Architecture** section has been added to the beginning of the guide with complete step-by-step instructions for:

### 1. **Root Account Setup (Admin Only)** - Step 0
- Creating AWS account
- Enabling MFA on root account
- Creating admin IAM user

### 2. **Developer 1 Setup (Backend Services)** - Step 1
**Responsible for:**
- Lambda Functions (Orchestrator, Entity Extractor, RAG Validator, MCP Validator, Audit Logger)
- RDS Database (schema, data loading, connections)
- Lex Bot (intent configuration, integration)
- API Gateway (endpoint creation, CORS)

**Created:**
- IAM User: `dev-1-backend`
- IAM Role: `ask-iam-backend-developer`
- Permissions include: Lambda, RDS, Lex, API Gateway, CloudWatch Logs (read-only)

### 3. **Developer 2 Setup (Infrastructure & DevOps)** - Step 2
**Responsible for:**
- IAM Roles & Policies (foundation)
- VPC & Security Groups (networking)
- OpenSearch Serverless (vector search setup)
- Secrets Manager & Parameter Store (configuration)
- CloudWatch & Monitoring (dashboards, alarms, logs)

**Created:**
- IAM User: `dev-2-infra`
- IAM Role: `ask-iam-infra-developer`
- Permissions include: OpenSearch, CloudWatch, VPC, EC2, IAM (limited), Secrets Manager, CloudFormation

### 4. **Developer 1 Action Items** - Step 3
Checklist of services to deploy with timeline:
- Week 1-2: Lambda Functions
- Week 2-3: Database
- Week 3: Lex Bot
- Week 4: API Gateway

### 5. **Developer 2 Action Items** - Step 4
Checklist of services to deploy with timeline:
- Week 1: Foundation (VPC, Security Groups)
- Week 1-2: Secrets & Configuration
- Week 2-3: OpenSearch Serverless
- Week 3: Monitoring
- Week 4: Integration Support

### 6. **Collaboration & Handoff** - Step 5
- Developer-to-developer handoff milestones
- Daily sync template
- Blocker resolution

### 7. **Git Repository Structure** - Step 6
Recommended folder organization:
- `infrastructure/` → Dev-2 owns (IAM roles, security groups, OpenSearch, CloudWatch)
- `backend/` → Dev-1 owns (Lambda functions, tests)
- `docs/` → Shared (Architecture, deployment, troubleshooting)

### 8. **Git Workflow** - Step 6
Example feature branch workflow for both developers with Pull Request reviews

### 9. **Communication & Troubleshooting** - Step 7
- Common troubleshooting scenarios
- Communication channels by issue type
- Ownership matrix

---

## Quick Implementation Guide

### For Admin (Root Account Owner)

1. Create AWS account at https://aws.amazon.com/
2. Follow **Step 0** in the guide to:
   - Enable MFA on root account
   - Create admin IAM user (`askiam-admin`)
3. Follow **Step 1** to create:
   - IAM User: `dev-1-backend`
   - IAM Role: `ask-iam-backend-developer`
4. Follow **Step 2** to create:
   - IAM User: `dev-2-infra`
   - IAM Role: `ask-iam-infra-developer`
5. Share sign-in URLs and credentials with developers via secure channel (1Password, LastPass, etc.)

**Time Required:** ~1 hour

### For Developer 1 (Backend)

1. Receive sign-in credentials from admin
2. Sign in: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
3. Switch to role: `ask-iam-backend-developer` (using "Switch role" button)
4. Verify you can see: Lambda, RDS, Lex, API Gateway
5. Set up MFA (recommended)
6. Proceed with Lambda/RDS/Lex deployments

**Reference:** Step 1D and Step 3A in the guide

### For Developer 2 (Infrastructure)

1. Receive sign-in credentials from admin
2. Sign in: `https://ACCOUNT-ID.signin.aws.amazon.com/console/`
3. Switch to role: `ask-iam-infra-developer` (using "Switch role" button)
4. Verify you can see: OpenSearch, CloudWatch, VPC, EC2, IAM, Secrets Manager
5. Set up MFA (recommended)
6. Proceed with infrastructure deployments

**Reference:** Step 2E and Step 4A in the guide

---

## Key Features of This Setup

✅ **Single AWS Account** - Unified billing and simplified networking  
✅ **Role-Based Access Control** - Clear separation of duties  
✅ **Scalable Design** - Easy to add more developers with new roles  
✅ **Git-Ready** - Directory structure matches team responsibilities  
✅ **Security Best Practices** - MFA, least privilege, resource naming conventions  
✅ **Collaboration Framework** - Handoff milestones and communication channels  
✅ **Troubleshooting Guide** - Common scenarios and resolution paths  

---

## File Locations

| Document | Location |
|----------|----------|
| **Complete Setup Guide** | [AWS_CONSOLE_SETUP_GUIDE.md](AWS_CONSOLE_SETUP_GUIDE.md#team-setup-two-developer-architecture) |
| **This Summary** | [TEAM_SETUP_SUMMARY.md](TEAM_SETUP_SUMMARY.md) |
| **Architecture Overview** | [ReadME.md](ReadME.md) |

---

## Account Structure Summary

```
Single AWS Account: ask-iam-prod
├── Admin User
│   └── Role: AdministratorAccess (root account owner)
│
├── Developer 1 (dev-1-backend)
│   └── Role: ask-iam-backend-developer
│       ├── Lambda: Create, update, delete functions
│       ├── RDS: Full access to databases
│       ├── Lex: Full bot management
│       ├── API Gateway: Full endpoint management
│       └── CloudWatch: Logs read-only
│
├── Developer 2 (dev-2-infra)
│   └── Role: ask-iam-infra-developer
│       ├── IAM: Create/manage roles (ask-iam-* pattern only)
│       ├── OpenSearch: Full serverless management
│       ├── VPC: Full network management
│       ├── EC2: Security groups management
│       ├── CloudWatch: Full monitoring
│       ├── Secrets Manager: Full access
│       └── Parameter Store: Full access
│
└── Shared Resources
    ├── Parameter Store (/ask-iam/*)
    ├── Secrets Manager (ask-iam/*)
    ├── CloudWatch Logs (/aws/lambda/ask-iam-*)
    └── CloudTrail
```

---

## Next Steps

1. **Admin**: Follow Steps 0-2 in AWS_CONSOLE_SETUP_GUIDE.md
2. **Dev-1**: Follow Step 1D and proceed to Part 5 (Lambda setup)
3. **Dev-2**: Follow Step 2E and proceed to Part 2 (RDS setup)
4. **Team**: Establish communication channels and run daily standups

---

## Support & Troubleshooting

If you encounter issues:

1. Check the **Communication & Troubleshooting** section (Step 7) in the guide
2. Review the **FAQ** section at the end of AWS_CONSOLE_SETUP_GUIDE.md
3. Verify IAM roles and permissions are correctly assigned
4. Check CloudWatch logs for service-specific errors

