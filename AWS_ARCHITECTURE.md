# AWS Serverless Architecture for AskIAM Assistant

## Executive Summary

This document outlines a production-ready, serverless AWS architecture for the AskIAM IAM Access Validation system. The design prioritizes:

- **Serverless-First**: AWS Lambda, API Gateway, and managed services
- **Cost Optimization**: Auto-scaling, pay-per-use pricing model
- **Security**: IAM roles, encryption, least privilege access
- **Observability**: CloudWatch, X-Ray tracing, detailed audit logs
- **Scalability**: Handle thousands of concurrent requests with zero infrastructure management

---

## 1. High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │   Web UI         │  │  Amazon Lex      │  │  Mobile App              │  │
│  │  (React/Vue)     │  │  Chatbot         │  │  (iOS/Android)           │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────────────┘  │
│           │                     │                     │                      │
└───────────┼─────────────────────┼─────────────────────┼──────────────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
        ┌─────────────────────────▼──────────────────────────┐
        │       AMAZON API GATEWAY                           │
        │  • Request routing (REST API)                      │
        │  • API Key authentication                          │
        │  • Request/response transformation                 │
        │  • Rate limiting & throttling                      │
        └────┬────────────────────┬─────────────────────┬───┘
             │                    │                     │
        ┌────▼──────┐    ┌────────▼────────┐   ┌───────▼──────┐
        │ POST /chat │    │ POST /requests │   │ GET /status  │
        └────┬──────┘    └────────┬────────┘   └───────┬──────┘
             │                    │                     │
        ┌────▼──────────────────────────────────────────▼────────────────────────┐
        │              AWS LAMBDA - ORCHESTRATION LAYER                           │
        ├──────────────────────────────────────────────────────────────────────────┤
        │                                                                          │
        │  ┌────────────────────────────────────────────────────────────────┐    │
        │  │  RequestOrchestrator Lambda                                   │    │
        │  │  • Parse and validate incoming request                        │    │
        │  │  • Route to entity extraction                                 │    │
        │  │  • Coordinate validation pipeline                             │    │
        │  │  • Return validation result                                   │    │
        │  └────────────────────────────────────────────────────────────────┘    │
        │                                                                          │
        └──────┬───────────────────┬─────────────────────┬──────────┬──────────────┘
               │                   │                     │          │
        ┌──────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐  │
        │ EntityEx-   │   │ RAGValidator    │   │ MCPValidator│  │
        │ tractor     │   │ Lambda          │   │ Lambda      │  │
        │ Lambda      │   │                 │   │             │  │
        └──────┬──────┘   └────────┬────────┘   └──────┬──────┘  │
               │                   │                     │         │
        ┌──────▼───────────┬───────▼────────┬────────────▼──────────┬──────────┐
        │                  │                │                       │          │
    ┌───▼─────────┐  ┌──────▼────────┐ ┌───▼─────────────┐  ┌──────▼──────┐ │
    │ RDS Aurora  │  │ OpenSearch    │ │ Secrets Manager│  │ Parameter   │ │
    │ (PostgreSQL)│  │ Serverless    │ │ • DB Creds     │  │ Store       │ │
    │             │  │ • Search      │ │ • API Keys     │  │ • Config    │ │
    │ • Users     │  │ • Analytics   │ │ • Tokens       │  │ • URLs      │ │
    │ • Roles     │  │ • Metadata    │ │                │  │             │ │
    │ • Audit Log │  │   Indexing    │ │                │  │             │ │
    └─────────────┘  └───────────────┘ └────────────────┘  └─────────────┘ │
        │                   │                                                │
        │                   │         ┌───────────────────────────┐          │
        │                   │         │  AWS DATA & STORAGE LAYER │          │
        │                   │         └───────────────────────────┘          │
        │                   │                                                │
        └───────────────────┴────────────────────────────────────────────────┘
                │                   │
        ┌───────▼───────────────────▼────────────────────────┐
        │    OBSERVABILITY & LOGGING LAYER                  │
        ├────────────────────────────────────────────────────┤
        │  • CloudWatch Logs (Lambda, API Gateway)           │
        │  • X-Ray Tracing (service map & latency)           │
        │  • CloudWatch Metrics (custom & built-in)          │
        │  • EventBridge (audit events to centralized log)   │
        │  • Structured JSON logging (Lambda functions)      │
        └────────────────────────────────────────────────────┘
```

---

## 2. Service Interaction & Request Lifecycle

### End-to-End Request Flow

#### **1. Request Initiation**
- User submits access request via:
  - **Web UI** → API Gateway POST `/chat`
  - **Amazon Lex** → Natural language input
  - **Mobile App** → REST API call
- **API Gateway** validates API key, rate limits, and forwards to Lambda

#### **2. RequestOrchestrator Lambda**
```
Input: {
  "user_id": "john.doe",
  "raw_request": "I need access to HR Analyst role in Workday",
  "request_context": {
    "ip": "10.0.0.1",
    "timestamp": "2024-01-21T10:30:00Z",
    "session_id": "sess-12345"
  }
}

Processing:
1. Validate request schema
2. Check authentication/authorization
3. Log request to CloudWatch
4. Invoke EntityExtractor Lambda (async)
```

#### **3. EntityExtractor Lambda**
```
Responsibilities:
- Parse raw request using LLM or pattern matching
- Extract: {user_name, application_name, role_name}
- Validate entity format
- Query RDS to verify entities exist
- Return: {user_id, app_id, role_id}

Data Sources:
- RDS Aurora (entity validation)
- Parameter Store (extraction patterns)
```

#### **4. Parallel Validation Path**

**Path A: RAG Validation (OpenSearch Serverless)**
```
1. Search OpenSearch for similar access patterns:
   Query: "HR Analyst + Workday + john.doe"
2. Retrieve top-k matching documents from knowledge base
3. Use LLM (via Lambda) to evaluate compliance:
   "Is this access request compliant with org policy?"
4. Return: {is_valid: boolean, confidence: 0.0-1.0}
```

**Path B: MCP Validation (Direct Database)**
```
1. Execute SQL queries (via Lambda):
   SELECT * FROM roles WHERE role_id = ?
   SELECT * FROM user_roles WHERE user_id = ? AND role_id = ?
   SELECT * FROM app_roles WHERE app_id = ? AND role_id = ?
2. Validate:
   - User exists and is active
   - Role exists in application
   - User not already assigned role
   - User meets prerequisites
3. Return: {is_valid: boolean, reason: string}
```

#### **5. Decision Logic**
```
If RAG_CONFIDENCE > 0.95:
  → Accept RAG result, skip MCP
Else If MCP_VALIDATION == PASSED:
  → Accept MCP result
Else:
  → Return INVALID with audit trail
```

#### **6. Finalize & Audit**
```
1. Combine validation results
2. Log audit event to RDS audit table
3. Send metrics to CloudWatch
4. Return response to API Gateway
5. If approved: Queue workflow to execute access grant
```

---

## 3. AWS Services & Their Roles

### **3.1 API Gateway (Request Entry Point)**
| Feature | Purpose |
|---------|---------|
| REST API | Route requests to Lambda functions |
| API Keys | Track and throttle API consumers |
| Request/Response Models | Validate schema, transform input |
| CORS | Allow cross-origin requests from web UI |
| Logging | CloudWatch integration for all requests |
| Authorization | JWT, IAM, custom authorizers |

**Configuration:**
```yaml
POST /access-request → RequestOrchestrator Lambda
POST /lex-webhook → Lex Connector Lambda
GET /status/{request_id} → StatusChecker Lambda
```

### **3.2 Amazon Lex (Conversational Interface)**
| Feature | Purpose |
|---------|---------|
| Natural Language Understanding | Parse user intents |
| Slots | Extract entities (user, role, app) |
| Dialog Management | Multi-turn conversation flow |
| Custom Fulfillment | Lambda integration |
| Session Management | Track conversation context |

**Intents:**
```
AccessRequest Intent:
  - Slot: UserName (required)
  - Slot: ApplicationName (required)
  - Slot: RoleName (required)
  - Fulfillment: RequestOrchestrator Lambda
```

### **3.3 AWS Lambda (Business Logic)**

#### **Lambda Function 1: RequestOrchestrator**
- **Timeout**: 60 seconds
- **Memory**: 512 MB
- **Concurrency**: Unreserved (auto-scaling)
- **Responsibilities**:
  - Parse Lex intent or API request
  - Orchestrate entity extraction
  - Decide validation path
  - Return response

#### **Lambda Function 2: EntityExtractor**
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Responsibilities**:
  - Extract user, role, application from raw text
  - Validate entity existence in RDS
  - Standardize entity names

#### **Lambda Function 3: RAGValidator**
- **Timeout**: 45 seconds
- **Memory**: 1024 MB
- **Responsibilities**:
  - Query OpenSearch Serverless
  - Call LLM for semantic validation
  - Return compliance decision

#### **Lambda Function 4: MCPValidator**
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Responsibilities**:
  - Execute parameterized SQL queries
  - Validate business rules
  - Return validation decision

#### **Lambda Function 5: AuditLogger**
- **Timeout**: 15 seconds
- **Memory**: 256 MB
- **Trigger**: Asynchronous (via EventBridge)
- **Responsibilities**:
  - Write audit events to RDS
  - Update metrics
  - Archive to S3 (optional)

### **3.4 Amazon RDS (Relational Data)**
| Service | Configuration | Purpose |
|---------|---------------|---------|
| Engine | PostgreSQL 15.x | Industry standard, ACID compliance |
| Instance Class | db.serverless-v2 | Auto-scaling, cost-effective |
| Multi-AZ | Yes | High availability |
| Backup | 30-day retention | Disaster recovery |
| Storage | gp3 (100 GB initial) | General purpose, scalable |

**Key Tables:**
```sql
users (user_id, email, name, status, created_at)
applications (app_id, name, description, owner, created_at)
roles (role_id, app_id, name, permissions, created_at)
user_roles (user_id, role_id, granted_at, expires_at, status)
audit_log (id, user_id, action, resource, status, timestamp, ip_address)
policies (id, policy_json, version, created_at)
```

### **3.5 Amazon OpenSearch Serverless (Search & Analytics)**
| Feature | Purpose |
|---------|---------|
| Serverless | No capacity planning, auto-scaling |
| Indexing | Full-text search on IAM metadata |
| Vector Search | Semantic similarity for RAG |
| Analytics | Query patterns, compliance reporting |
| Security | Encryption at rest/transit, VPC isolation |

**Indexes:**
```
iam_metadata:
  - Fields: user_name, app_name, role_name, policy_json, compliance_level
  - Vector embeddings for semantic search
  
access_patterns:
  - Fields: user_id, role_id, app_id, timestamp, approved
  - Historical access grants for pattern matching
```

### **3.6 Secrets Manager & Parameter Store**
| Service | Use Case | Example |
|---------|----------|---------|
| **Secrets Manager** | Sensitive credentials | DB password, API keys, JWT secret |
| **Parameter Store** | Configuration | Lex bot ID, OpenSearch endpoint, thresholds |

**Values to Store:**
```
/askiam/prod/db/password → RDS Aurora password
/askiam/prod/openai/api-key → LLM API key (if external)
/askiam/prod/lex/bot-id → Lex bot ID
/askiam/prod/app/rag-threshold → RAG confidence threshold (0.95)
/askiam/prod/app/audit-enabled → Boolean flag for audit logging
```

---

## 4. Data Flow Diagrams

### **4.1 Access Request Validation Flow**

```
START: User submits "I need HR Analyst role in Workday"
  ↓
[API Gateway] Validates API key, enforces rate limit
  ↓
[RequestOrchestrator Lambda]
  ├─→ Log to CloudWatch (raw request)
  ├─→ Extract tracing context (X-Ray)
  └─→ Invoke EntityExtractor
      ↓
  [EntityExtractor Lambda]
    ├─→ Parse text → {user: "john.doe", app: "workday", role: "hr_analyst"}
    ├─→ Query RDS to verify entities exist
    └─→ Return {user_id: 123, app_id: 456, role_id: 789}
      ↓
  [RequestOrchestrator] Receives extracted entities
    ├─→ Invoke RAGValidator (async)
    └─→ Invoke MCPValidator (async)
      ↓
  ┌─────────────────────────────────────────────┐
  │ Parallel Validation (30 second timeout)     │
  ├─────────────────────────────────────────────┤
  │ [RAGValidator Lambda]          [MCPValidator Lambda]
  │ ├─→ OpenSearch query           ├─→ SQL: SELECT role...
  │ ├─→ LLM semantic check         ├─→ SQL: SELECT user_roles...
  │ └─→ Confidence score           └─→ Business rule validation
  └─────────────────────────────────────────────┘
      ↓
  [RequestOrchestrator] Receives results
    ├─→ If RAG confidence > 95%: Accept
    ├─→ Else If MCP PASSED: Accept
    └─→ Else: Reject
      ↓
  [AuditLogger Lambda]
    ├─→ Insert audit record to RDS
    ├─→ Send metric to CloudWatch
    └─→ X-Ray annotate
      ↓
  [API Gateway] Return response to client
    └─→ {status: "VALID", reason: "...", request_id: "..."}
```

### **4.2 Audit & Compliance Flow**

```
[Validation Completed]
  ↓
[EventBridge Rule] Triggers on Lambda completion
  ↓
[AuditLogger Lambda]
  ├─→ Fetch validation result
  ├─→ Enrich with context (IP, user agent, timestamp)
  ├─→ Insert into RDS audit_log table
  ├─→ Upload to CloudWatch as structured JSON
  └─→ Optional: Archive to S3 for long-term retention
      ↓
[CloudWatch Logs Insights] Query for compliance reporting
  ├─→ "How many access requests from john.doe this week?"
  ├─→ "What was approved/rejected ratio?"
  └─→ "Who accessed sensitive roles?"
```

---

## 5. Lambda Function Responsibilities & Boundaries

### **Function 1: RequestOrchestrator**
**Boundary**: Coordinates entire validation workflow

| Responsibility | Details |
|---|---|
| **Input** | API Gateway event OR Lex intent |
| **Processing** | 1. Validate request schema<br>2. Extract request ID / session ID<br>3. Invoke EntityExtractor<br>4. Orchestrate parallel validators<br>5. Aggregate results<br>6. Invoke AuditLogger |
| **Output** | JSON: {status, reason, request_id, timestamp} |
| **Dependencies** | EntityExtractor, RAGValidator, MCPValidator, AuditLogger |
| **Error Handling** | Catch and return 400/500 errors; log to CloudWatch |

### **Function 2: EntityExtractor**
**Boundary**: Parse natural language → standardized entities

| Responsibility | Details |
|---|---|
| **Input** | {raw_request: string, request_id: string} |
| **Processing** | 1. Split text by keywords<br>2. Match against patterns (regex or LLM)<br>3. Query RDS to verify entities exist<br>4. Standardize names (lowercase, trim)<br>5. Return entity IDs |
| **Output** | JSON: {user_id, app_id, role_id} OR error |
| **Dependencies** | RDS Aurora |
| **Error Handling** | Return 400 if entity not found; suggest similar names |

### **Function 3: RAGValidator**
**Boundary**: Knowledge-based validation using semantic search

| Responsibility | Details |
|---|---|
| **Input** | {user_id, app_id, role_id, request_id} |
| **Processing** | 1. Build search query from entities<br>2. Query OpenSearch Serverless<br>3. Call LLM to evaluate compliance<br>4. Return confidence score (0-1)<br>5. Include matching documents |
| **Output** | JSON: {is_valid, confidence, documents, reason} |
| **Dependencies** | OpenSearch Serverless, LLM API |
| **Error Handling** | Fallback to MCPValidator on timeout |

### **Function 4: MCPValidator**
**Boundary**: Database-driven validation using SQL

| Responsibility | Details |
|---|---|
| **Input** | {user_id, app_id, role_id, request_id} |
| **Processing** | 1. Execute SQL queries (parameterized)<br>2. Check user status (active/inactive)<br>3. Verify role exists in app<br>4. Check for conflicts (re-assignment)<br>5. Validate policies |
| **Output** | JSON: {is_valid, reason, queries_executed} |
| **Dependencies** | RDS Aurora (read-only) |
| **Error Handling** | SQL injection protection via parameterized queries |

### **Function 5: AuditLogger**
**Boundary**: Asynchronous logging of validation events

| Responsibility | Details |
|---|---|
| **Input** | {request_id, user_id, validation_result, context} |
| **Processing** | 1. Log to CloudWatch (structured JSON)<br>2. Insert into RDS audit_log table<br>3. Calculate metrics<br>4. X-Ray annotate<br>5. Optional: S3 archive |
| **Output** | Success status; side effects (DB writes) |
| **Dependencies** | RDS Aurora, CloudWatch, S3 (optional) |
| **Error Handling** | Retry logic for transient failures |

---

## 6. Security Architecture

### **6.1 Authentication & Authorization**

```
┌─────────────────────────────────────────────────────────┐
│ API AUTHENTICATION LAYERS                               │
├─────────────────────────────────────────────────────────┤
│ 1. API Key (API Gateway)                                │
│    ├─ Issued to external systems                        │
│    └─ Rate-limited per key                              │
│                                                         │
│ 2. IAM Roles (AWS Services to AWS Services)             │
│    ├─ Lambda → RDS (temporary credentials)              │
│    ├─ Lambda → OpenSearch (temporary credentials)       │
│    └─ Lambda → Secrets Manager (read-only)              │
│                                                         │
│ 3. JWT (for Web UI, if needed)                          │
│    ├─ Verified by Lambda authorizer                     │
│    └─ Stored in Secrets Manager                         │
└─────────────────────────────────────────────────────────┘
```

### **6.2 IAM Role Definitions**

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:region:account:log-group:/aws/lambda/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds-db:connect"
      ],
      "Resource": "arn:aws:rds-db:region:account:dbuser:resource-id/db_user"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAll"
      ],
      "Resource": "arn:aws:aoss:region:account:collection/ask-iam"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:region:account:secret:askiam/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:region:account:parameter/askiam/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

### **6.3 Data Encryption**

| Layer | Encryption | Details |
|-------|-----------|---------|
| **RDS Aurora** | KMS (AWS-managed) | Encryption at rest |
| **OpenSearch** | KMS (AWS-managed) | Encryption at rest |
| **Secrets Manager** | AWS KMS | Encryption at rest & transit |
| **API Gateway** | TLS 1.2+ | HTTPS only |
| **Lambda ↔ RDS** | VPC + TLS | Private subnet communication |
| **Logs** | CloudWatch native encryption | No additional config needed |

### **6.4 VPC & Network Isolation**

```
┌─────────────────────────────────────────────────────┐
│ VPC: ask-iam-prod                                   │
├─────────────────────────────────────────────────────┤
│ Private Subnet (10.0.1.0/24)                        │
│ ├─ Lambda functions (no ENI required with VPC NAT) │
│ ├─ RDS Aurora (db.serverless-v2)                   │
│ ├─ OpenSearch Serverless collection                │
│ └─ VPC NAT Gateway for external calls              │
│                                                     │
│ Public Subnet (API Gateway webhooks only)          │
└─────────────────────────────────────────────────────┘
```

---

## 7. Logging, Monitoring & Tracing

### **7.1 CloudWatch Logging Strategy**

**Log Groups:**
```
/aws/lambda/ask-iam/request-orchestrator
/aws/lambda/ask-iam/entity-extractor
/aws/lambda/ask-iam/rag-validator
/aws/lambda/ask-iam/mcp-validator
/aws/lambda/ask-iam/audit-logger
/aws/apigateway/ask-iam
```

**Structured Logging Format (JSON):**
```json
{
  "timestamp": "2024-01-21T10:30:45.123Z",
  "request_id": "req-abc123",
  "lambda_function": "RequestOrchestrator",
  "level": "INFO",
  "message": "Validation completed",
  "user_id": "john.doe",
  "validation_result": "VALID",
  "duration_ms": 250,
  "trace_id": "1-65a12345-abcdef1234567890",
  "context": {
    "ip_address": "203.0.113.42",
    "session_id": "sess-12345",
    "user_agent": "Mozilla/5.0..."
  }
}
```

### **7.2 X-Ray Tracing**

**Service Map:**
```
API Gateway → RequestOrchestrator → {EntityExtractor, RAGValidator, MCPValidator}
                  ↓                  ↓                    ↓
              CloudWatch     RDS Aurora        OpenSearch Serverless
              CloudWatch     Secrets Manager   LLM API
```

**Trace Annotations (key-value pairs for filtering):**
```
- request_id: "req-abc123"
- user_id: "john.doe"
- validation_status: "VALID"
- rag_confidence: 0.97
- mcp_result: "PASSED"
- environment: "production"
```

### **7.3 CloudWatch Metrics**

**Custom Metrics (emitted from Lambda):**

| Metric Name | Dimensions | Unit | Purpose |
|---|---|---|---|
| `AccessRequestCount` | Status (VALID/INVALID) | Count | Track request volume |
| `ValidationLatency` | Component (RAG/MCP) | Milliseconds | Monitor performance |
| `RAGConfidence` | None | None | Track model confidence |
| `ErrorCount` | Function, ErrorType | Count | Alert on failures |
| `ConcurrentRequests` | Function | Count | Understand load |

**CloudWatch Alarms:**
```
1. Lambda Error Rate > 1%
   → Trigger: SNS notification to ops team
   
2. API Latency > 5 seconds
   → Action: Auto-scale Lambda concurrency
   
3. RDS CPU > 80%
   → Action: Notify for capacity review
   
4. Audit Log Insertion Failures
   → Action: PagerDuty alert
```

### **7.4 Log Insights Queries**

```sql
-- Find slow requests
fields @timestamp, @duration, @message, user_id
| filter @duration > 3000
| stats count() by user_id

-- Error rate by function
fields @timestamp, @functionName, @message
| filter @message like /ERROR|FAILED/
| stats count() as error_count by @functionName

-- Top accessed roles
fields role_id, user_id
| filter validation_result = "VALID"
| stats count() as access_count by role_id
| sort access_count desc
```

---

## 8. Scalability & Performance

### **8.1 Auto-Scaling Strategy**

| Component | Scaling Mechanism | Config |
|---|---|---|
| **Lambda** | AWS Lambda scaling | Concurrent executions: 1000 (default) |
| **RDS Aurora** | Aurora Serverless v2 | Auto-scaling: 0.5 to 2 ACUs |
| **OpenSearch** | Serverless Collection | Auto-scaling: 4-16 OCUs |
| **API Gateway** | Automatic | No limits (soft limit: 10,000 RPS) |

### **8.2 Performance Optimization**

```yaml
RequestOrchestrator:
  memory: 512 MB
  timeout: 60 seconds
  provisioned_concurrency: 10  # Reduce cold starts
  ephemeral_storage: 512 MB
  
EntityExtractor:
  memory: 256 MB
  timeout: 30 seconds
  
RAGValidator:
  memory: 1024 MB  # LLM calls need memory
  timeout: 45 seconds
  
MCPValidator:
  memory: 256 MB
  timeout: 30 seconds
```

### **8.3 Cost Optimization**

```
Monthly Cost Estimate (1M requests):

1. Lambda: $0.20 / 1M requests + $0.0000166667 / GB-second
   Estimate: $200 + $83 = $283 /month

2. RDS Aurora Serverless v2: $0.84 /ACU-hour
   Estimate: ~100 ACU-hours /month = $84 /month

3. OpenSearch Serverless: $0.30 /OCU-hour
   Estimate: ~50 OCU-hours /month = $15 /month

4. API Gateway: $3.50 /M requests
   Estimate: $3.50 /month

5. CloudWatch Logs: $0.50 /GB ingested
   Estimate: 10 GB /month = $5 /month

TOTAL: ~$390 /month for 1M requests (0.39¢ per request)
vs. EC2-based: $1500+ /month
```

---

## 9. Disaster Recovery & Fault Tolerance

### **9.1 RTO/RPO Targets**
- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 15 minutes

### **9.2 Backup Strategy**

| Resource | Backup Frequency | Retention | Recovery |
|---|---|---|---|
| **RDS Aurora** | Automatic hourly snapshots | 30 days | Point-in-time restore |
| **OpenSearch** | Index snapshots (daily) | 7 days | Restore from snapshot |
| **Secrets Manager** | Automatic versioning | Last 10 versions | Restore from version |
| **Lambda Code** | CodeCommit Git | Unlimited | Redeploy from commit |

### **9.3 Failover & Redundancy**

```
┌─────────────────────────────────────────────┐
│ Active Region: us-east-1                    │
│ ├─ RDS Aurora (primary)                     │
│ ├─ OpenSearch Serverless                    │
│ └─ Lambda functions                         │
│                                             │
│ Standby Region: us-west-2 (manual failover) │
│ ├─ RDS Aurora (read replica)                │
│ ├─ Lambda functions (cold)                  │
│ └─ Manual promotion if needed               │
└─────────────────────────────────────────────┘
```

### **9.4 Resilience Patterns**

```python
# Retry logic with exponential backoff
import time
import random

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise

# Circuit breaker pattern (pseudocode)
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

---

## 10. Cost Analysis & Optimization

### **10.1 Serverless vs. Traditional EC2**

| Aspect | Serverless (Lambda) | EC2 Instance |
|---|---|---|
| **Instance Size** | 512 MB - 10 GB | t3.medium = 2GB + overhead |
| **Always Running Cost** | $0 when idle | $30-50 /month always |
| **Per-Request Cost** | $0.20 per 1M | Baked into instance |
| **Annual Cost (1M req/month)** | $3,900 | $18,000+ |
| **Scaling Time** | <100 ms | 2-5 minutes |

### **10.2 Cost Optimization Strategies**

1. **Reserved Capacity**
   - RDS: 1-year reserved = 50% discount
   - OpenSearch: Reserved OCUs = 30% discount

2. **Provisioned Concurrency** (if cold starts critical)
   - 10 concurrent: $3.50/month
   - Only for functions with SLA requirements

3. **Data Transfer Optimization**
   - Keep Lambda + RDS in same AZ (no data transfer cost)
   - Use VPC endpoints for AWS service calls

4. **Log Retention**
   - Set CloudWatch log retention to 7 days (vs. indefinite)
   - Archive older logs to S3 Glacier for compliance

5. **Unused Resources**
   - Delete idle OpenSearch indexes
   - Snapshot and delete old RDS backups

---

## 11. Deployment & Operations

### **11.1 Infrastructure as Code (AWS SAM)**
See: [aws-sam-template.yaml](./aws-sam-template.yaml)

### **11.2 Deployment Pipeline**
```
GitHub Push (main branch)
  ↓
CodePipeline triggered
  ↓
CodeBuild: Run unit tests & linting
  ↓
SAM Build & Package
  ↓
CloudFormation Stack Update
  ↓
Lambda functions updated
  ↓
Integration tests
  ↓
Canary deployment (5% traffic)
  ↓
Monitor for 1 hour
  ↓
Full rollout OR automatic rollback
```

### **11.3 Operational Runbooks**

**On-Call Escalation:**
```
1. CloudWatch Alarm triggers
2. SNS notification to Slack
3. On-call engineer reviews X-Ray trace
4. If resolved: close ticket
5. If not: escalate to platform team
```

---

## 12. Conclusion

This serverless architecture provides:

✅ **Cost Efficiency**: 60-70% cheaper than EC2  
✅ **High Availability**: Multi-AZ, auto-scaling  
✅ **Security**: Encryption, IAM, VPC isolation  
✅ **Observability**: X-Ray, CloudWatch, structured logging  
✅ **Scalability**: Handles 10x+ request volume growth  
✅ **Maintainability**: Infrastructure as Code, no servers to manage

**Next Steps:**
1. Review and approve architecture
2. Set up AWS account and VPC
3. Deploy infrastructure using SAM templates
4. Migrate existing code to Lambda functions
5. Establish monitoring and alerting
6. Conduct load testing and chaos engineering
