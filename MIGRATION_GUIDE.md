# AskIAM Assistant: Migration Guide from Local to AWS

## Overview

This guide provides step-by-step instructions for migrating the AskIAM Assistant from a local Docker-based setup to the AWS CloudFormation infrastructure.

## Change Summary

| Component | Local Setup | AWS Setup | Migration Effort |
|-----------|--------------|-----------|------------------|
| PostgreSQL | Docker container | RDS PostgreSQL | Low - same database |
| ChromaDB | Docker container | OpenSearch Serverless | Medium - API changes |
| Ollama | Local installation | AWS Bedrock | High - model API changes |
| Python backend | Gradio web app | Lambda functions | High - architecture change |
| MCP tools | Docker/local server | Lambda handlers | Medium - wrapper code |
| Configuration | config.yaml | Environment variables | Low - mostly mapping |

## Phase 1: Prerequisites & Planning

### 1.1 AWS Account Setup

```bash
# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity

# Enable necessary services (already available):
# - CloudFormation
# - Lambda
# - RDS
# - OpenSearch
# - DynamoDB
# - S3
# - Bedrock (ensure enabled in your region)
```

### 1.2 Enable Bedrock Models

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Enable specific models if needed
# (Usually available immediately, but may need to be requested)
```

### 1.3 Calculate Costs

```bash
# Use AWS Pricing Calculator
# https://calculator.aws/#/

# Estimate based on:
# - RDS PostgreSQL usage (compute hours)
# - OpenSearch Serverless usage (OCU hours)
# - Lambda invocations and duration
# - DynamoDB requests
# - Data transfer
```

## Phase 2: Prepare Local Data & Code

### 2.1 Export PostgreSQL Data

```bash
# Backup current database
docker exec iam-postgres pg_dump -U postgres iamdb > backup.sql

# Verify backup
gunzip < backup.sql | head -20

# Keep this backup safe - will be used for RDS initialization
cp backup.sql database/iam_sample_data.sql
```

### 2.2 Export ChromaDB Data

```bash
# ChromaDB doesn't have direct export, so we'll:
# 1. Export raw data from source systems
# 2. Re-ingest into OpenSearch during setup

# If you have the source files that were ingested:
ls database/chromaDB/chroma_data/
```

### 2.3 Review and Update Configuration

```yaml
# Local config.yaml
ollama:
  base_url: http://localhost:11434    # Will become Bedrock API calls
  llm_model: llama3.1:8b              # Will become claude-3-sonnet
  embedding_model: nomic-embed-text   # Will become titan-embed-text

# These will be handled via environment variables in Lambda
```

### 2.4 Modularize Python Code

The local monolithic app needs to be split into Lambda-compatible modules:

```python
# Local: Single app.py with Gradio interface
# AWS: Multiple Lambda functions

# Create these modules:
# - lambda_handlers/request_processor.py     (extract entities)
# - lambda_handlers/entity_validator.py      (validate entities)
# - lambda_handlers/rag_query.py             (RAG search + LLM)
# - lambda_handlers/orchestrator.py          (coordinate flow)
```

## Phase 3: Deploy AWS Infrastructure

### 3.1 Create S3 Bucket for Lambda Code

```bash
# Create bucket for Lambda ZIP files
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://askiam-lambda-code-${ACCOUNT_ID} --region us-east-1

# Verify bucket
aws s3 ls | grep askiam-lambda-code
```

### 3.2 Package Lambda Functions

```bash
# Create packages for each function
cd lambda_handlers/

# Request Processor
mkdir -p packages/request-processor
cp request_processor.py packages/request-processor/index.py
cd packages/request-processor
pip install -r requirements.txt -t .
zip -r ../request-processor.zip .
cd ../..

# Entity Validator
mkdir -p packages/entity-validator
cp entity_validator.py packages/entity-validator/index.py
cd packages/entity-validator
pip install -r requirements.txt -t .
zip -r ../entity-validator.zip .
cd ../..

# RAG Query
mkdir -p packages/rag-query
cp rag_query.py packages/rag-query/index.py
cd packages/rag-query
pip install -r requirements.txt -t .
zip -r ../rag-query.zip .
cd ../..

# Upload to S3
aws s3 cp packages/request-processor.zip s3://askiam-lambda-code-${ACCOUNT_ID}/
aws s3 cp packages/entity-validator.zip s3://askiam-lambda-code-${ACCOUNT_ID}/
aws s3 cp packages/rag-query.zip s3://askiam-lambda-code-${ACCOUNT_ID}/
```

### 3.3 Update CloudFormation Template

Update the Lambda function CodeUri in the template:

```yaml
RequestProcessorFunction:
  Properties:
    CodeUri: s3://askiam-lambda-code-${ACCOUNT_ID}/request-processor.zip
    # ... rest of config
```

### 3.4 Deploy Stack

```bash
# Validate template
aws cloudformation validate-template \
  --template-body file://cloudformation_template.yaml

# Create stack
aws cloudformation create-stack \
  --stack-name askiam-migration-stack \
  --template-body file://cloudformation_template.yaml \
  --parameters \
    ParameterKey=EnvironmentName,ParameterValue=migration \
    ParameterKey=DBPassword,ParameterValue=YourSecurePassword123 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1

# Monitor creation
aws cloudformation wait stack-create-complete \
  --stack-name askiam-migration-stack \
  --region us-east-1

echo "Stack creation complete!"
```

### 3.5 Retrieve Outputs

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name askiam-migration-stack \
  --query 'Stacks[0].Outputs' \
  --region us-east-1 \
  | jq -r '.[] | "\(.OutputKey)=\(.OutputValue)"'

# Save for later use
aws cloudformation describe-stacks \
  --stack-name askiam-migration-stack \
  --query 'Stacks[0].Outputs' \
  --region us-east-1 > stack-outputs.json
```

## Phase 4: Migrate Data

### 4.1 Initialize PostgreSQL RDS

```bash
# Get RDS endpoint
DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name askiam-migration-stack \
  --query "Stacks[0].Outputs[?OutputKey=='DBEndpoint'].OutputValue" \
  --output text)

echo "DB Endpoint: $DB_ENDPOINT"

# Load sample data
PGPASSWORD=YourSecurePassword123 psql \
  -h $DB_ENDPOINT \
  -U postgres \
  -d iamdb \
  -f database/iam_sample_data.sql

# Verify data loaded
PGPASSWORD=YourSecurePassword123 psql \
  -h $DB_ENDPOINT \
  -U postgres \
  -d iamdb \
  -c "SELECT COUNT(*) as user_count FROM users;"
```

### 4.2 Create OpenSearch Vector Index

```python
# Create a Python script to setup OpenSearch
# setup_opensearch.py

import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

def setup_opensearch_index():
    # Get collection endpoint from CloudFormation output
    # Create index with proper mappings
    # Configuration preserved from CloudFormation template
    pass

if __name__ == '__main__':
    setup_opensearch_index()
```

### 4.3 Ingest Data into Vector Store

```python
# Create ingestion script
# ingest_to_opensearch.py

import boto3
import psycopg2
from opensearchpy import OpenSearch
import json

def fetch_iam_metadata(db_host, db_user, db_password):
    """Fetch IAM entities from PostgreSQL"""
    conn = psycopg2.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database='iamdb'
    )
    # Query users, roles, applications
    # Convert to embeddings
    return documents

def ingest_to_opensearch(documents, opensearch_client):
    """Ingest documents into OpenSearch as vectors"""
    bedrock = boto3.client('bedrock-runtime')
    
    for doc in documents:
        # Get embedding via Bedrock
        embedding = bedrock_embed(doc['text'])
        
        # Index in OpenSearch
        opensearch_client.index(
            index='iam-vector-index',
            body={
                'vector': embedding,
                'text': doc['text'],
                'metadata': doc['metadata']
            }
        )

if __name__ == '__main__':
    # Execute ingestion process
    pass
```

Run the ingestion script:

```bash
# Set environment variables
export OPENSEARCH_COLLECTION="iam-collection"
export OPENSEARCH_INDEX="iam-vector-index"
export DB_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name askiam-migration-stack \
  --query "Stacks[0].Outputs[?OutputKey=='DBEndpoint'].OutputValue" \
  --output text)
export DB_PASSWORD="YourSecurePassword123"

# Run ingestion
python ingest_to_opensearch.py
```

## Phase 5: Update Application Code

### 5.1 Code Migration Priorities

**High Priority** (affects functionality):
- [ ] Replace Ollama calls with Bedrock API
- [ ] Replace ChromaDB calls with OpenSearch Serverless
- [ ] Update PostgreSQL connection strings (env vars)
- [ ] Implement Lambda event handlers

**Medium Priority** (affects performance):
- [ ] Add proper error handling
- [ ] Implement logging to CloudWatch
- [ ] Add metrics/alarms
- [ ] Optimize for Lambda cold starts

**Low Priority** (nice to have):
- [ ] Add caching layer
- [ ] Implement request compression
- [ ] Add API authentication
- [ ] Create monitoring dashboards

### 5.2 Update Config Loading

```python
# Old: Load from config.yaml
from core.config_loader import load_config
cfg = load_config()

# New: Use environment variables
import os
CONFIG = {
    'db': {
        'host': os.environ['DB_HOST'],
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ['DB_PASSWORD'],
        'database': os.environ.get('DB_NAME', 'iamdb')
    },
    'bedrock': {
        'llm_model': os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
        'embedding_model': os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
    },
    'opensearch': {
        'collection': os.environ['OPENSEARCH_COLLECTION'],
        'index': os.environ['OPENSEARCH_INDEX']
    }
}
```

### 5.3 Update LLM Calls

```python
# Old: Ollama
response = ollama_client.generate(
    model="llama3.1:8b",
    prompt=prompt
)

# New: Bedrock
import boto3
bedrock = boto3.client('bedrock-runtime')

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    messages=[{
        'role': 'user',
        'content': prompt
    }]
)
```

### 5.4 Update Vector Store Calls

```python
# Old: ChromaDB
from langchain.vectorstores import Chroma
vector_store = Chroma(
    client=chroma_client,
    collection_name='iam-metadata'
)

# New: OpenSearch
from opensearchpy import OpenSearch
docs = os_client.search(
    index='iam-vector-index',
    body={'query': {...}}
)
```

## Phase 6: Test & Validate

### 6.1 Unit Test Lambda Functions

```bash
# Test request processor locally
python -m pytest lambda_handlers/test_request_processor.py

# Test entity validator locally
python -m pytest lambda_handlers/test_entity_validator.py

# Test RAG query locally
python -m pytest lambda_handlers/test_rag_query.py
```

### 6.2 Integration Tests

```bash
# Test API endpoint
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/migration/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need access to HR Analyst role"}'

# Check CloudWatch logs
aws logs tail /aws/lambda/askiam-request-processor-migration --follow
```

### 6.3 Load Testing

```bash
# Use Apache Bench or similar
ab -n 100 -c 10 https://<api-id>.execute-api.us-east-1.amazonaws.com/migration/chat

# Monitor with CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 60 \
  --statistics Average
```

### 6.4 Data Validation

```bash
# Verify data in RDS
PGPASSWORD=pwd psql -h $DB_ENDPOINT -U postgres -d iamdb \
  -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM roles;"

# Verify vector index
curl -X GET https://$OPENSEARCH_ENDPOINT/iam-vector-index/_stats

# Verify chat logs
aws dynamodb scan --table-name askiam-chat-logs-migration --max-items 5
```

## Phase 7: Monitor & Optimize

### 7.1 Setup CloudWatch Monitoring

```bash
# View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# View RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=askiam-db-migration \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### 7.2 Optimize Performance

**Lambda Cold Starts:**
```yaml
MemorySize: 512    # Minimum 256, increase for faster CPU
Timeout: 60        # Match your actual processing time
EphemeralStorage: 512  # For packages larger than default
```

**RDS Performance:**
```sql
-- Check slow queries
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
```

**OpenSearch:**
- Monitor OCU usage
- Optimize vector dimension size
- Implement caching for frequent queries

### 7.3 Cost Optimization

```bash
# Review CloudFormation costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Identify expensive operations
# Adjust instance sizes/scaling accordingly
```

## Phase 8: Decommission Local Setup

### 8.1 Archive Local Data

```bash
# Create final backup
docker exec iam-postgres pg_dump -U postgres iamdb > final_backup.sql

# Archive locally
tar -czf askiam-local-backup-$(date +%Y%m%d).tar.gz \
  final_backup.sql \
  database/chromadb/chroma_data/
```

### 8.2 Shut Down Local Services

```bash
# Stop all services
docker-compose down

# Remove images if no longer needed
docker-compose down --remove-orphans --rmi all

# Verify services are stopped
docker ps
```

### 8.3 Update DNS/URLs

- Update API endpoints in client applications
- Update internal API documentation
- Update CI/CD pipelines
- Notify users of new endpoints

## Troubleshooting

### Issue: Lambda Cannot Connect to RDS

**Solution:**
```bash
# Check security group
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --query SecurityGroups[0].IpPermissions

# Check Lambda VPC config
aws lambda get-function-concurrency --function-name askiam-request-processor-migration
```

### Issue: OpenSearch Authorization Failed

**Solution:**
```bash
# Verify IAM role permissions
aws iam get-role-policy --role-name askiam-lambda-execution-role --policy-name OpenSearchAccess

# Check access policy
aws opensearchserverless get-access-policy --name=default --type=data
```

### Issue: Bedrock Model Not Available

**Solution:**
```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Request access if needed (console)
# aws bedrock create-model-access-request (if available)
```

## Rollback Plan

If issues arise, you can:

```bash
# Keep local services running during transition
# Monitor both systems in parallel
# Gradually shift traffic to AWS
# Maintain local backup for 30 days
# Document all issues for post-mortem

# To rollback: Switch DNS back to local services
# Keep AWS stack for reference
# Archive CloudFormation template for future re-deployment
```

## Success Criteria

- ✅ All data migrated to RDS and verified
- ✅ All vectors ingested to OpenSearch
- ✅ Lambda functions passing unit tests
- ✅ API endpoints responding within SLA
- ✅ Chat logs being recorded in DynamoDB
- ✅ CloudWatch monitoring showing healthy metrics
- ✅ Cost within budget estimates
- ✅ Local Docker services decommissioned
- ✅ Team trained on AWS infrastructure

## Next Steps

1. Implement automated backups to S3
2. Setup CI/CD for Lambda updates
3. Configure custom domain for API Gateway
4. Implement authentication layer
5. Create disaster recovery procedures
6. Setup budget alerts in AWS Cost Explorer

---

*This migration guide ensures a smooth transition from local Docker development to production AWS infrastructure.*
