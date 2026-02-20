# Lambda Function Patterns & Code Adaptation Guide

## Quick Reference for Converting Local Code to Lambda

### Pattern 1: HTTP Request/Response

```python
# Local (Gradio/Flask)
@app.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message')
    result = process_message(message)
    return jsonify({'result': result})

# Lambda
def handler(event, context):
    # Parse request
    body = json.loads(event.get('body', '{}'))
    message = body.get('message')
    
    # Process
    result = process_message(message)
    
    # Return response
    return {
        'statusCode': 200,
        'body': json.dumps({'result': result}),
        'headers': {'Content-Type': 'application/json'}
    }
```

### Pattern 2: Environment Configuration

```python
# Local (config.yaml)
db:
  host: localhost
  port: 5432
  user: postgres
  database: iamdb

# Lambda (environment variables)
import os
DB_HOST = os.environ['DB_HOST']  # Set in CloudFormation
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_NAME = os.environ.get('DB_NAME', 'iamdb')

# Or use AWS Secrets Manager
import boto3
secrets = boto3.client('secretsmanager')
db_creds = json.loads(
    secrets.get_secret_value(SecretId=os.environ['DB_SECRET_ARN'])['SecretString']
)
```

### Pattern 3: Database Connection

```python
# Local (persistent connection)
db = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='password',
    database='iamdb'
)

# Lambda (connection per invocation, use secrets)
def get_db_connection():
    creds = get_secret_value(os.environ['DB_SECRET_ARN'])
    return psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        user=creds['username'],
        password=creds['password'],
        database=creds['dbname']
    )

# Handler
def handler(event, context):
    conn = get_db_connection()
    try:
        # Use connection
        pass
    finally:
        conn.close()  # Always close
```

### Pattern 4: LLM Integration

```python
# Local (Ollama)
from langchain import Ollama
llm = Ollama(base_url="http://localhost:11434", model="llama3.1:8b")
response = llm.invoke(prompt)

# Lambda (Bedrock)
import boto3
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock.invoke_model(
    modelId=os.environ['BEDROCK_MODEL_ID'],
    messages=[{
        'role': 'user',
        'content': prompt
    }],
    max_tokens=500
)
result = json.loads(response['body'].read())
```

### Pattern 5: Vector Store Operations

```python
# Local (ChromaDB)
from langchain.vectorstores import Chroma
vector_store = Chroma(client=chroma_client)
docs = vector_store.similarity_search(query, k=5)

# Lambda (OpenSearch)
from opensearchpy import OpenSearch, AWSV4SignerAuth
import boto3

def get_opensearch_client():
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(
        credentials,
        region='us-east-1',
        service='aoss'
    )
    client = OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True
    )
    return client

client = get_opensearch_client()
response = client.search(
    index='iam-vector-index',
    body={'query': {'match': {'text': query}}}
)
```

### Pattern 6: Logging

```python
# Local (print statements)
print(f"Processing message: {message}")
print(f"Error: {error}")

# Lambda (CloudWatch)
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f"Processing message: {message}")
logger.error(f"Error: {error}")

# Automatic CloudWatch integration
# Logs available at: /aws/lambda/<function-name>
```

### Pattern 7: Long-Running Operations

```python
# Local (synchronous)
result = expensive_operation(data)
return result

# Lambda (limited to 15 minutes, use async if needed)
# Option A: Optimize to run within timeout
@timeout_decorator(seconds=300)
def expensive_operation(data):
    # Keep under 15 minutes
    pass

# Option B: Use Step Functions for longer operations
import boto3
stepfunctions = boto3.client('stepfunctions')

# Handler kicks off async job
stepfunctions.start_execution(
    stateMachineArn=STATE_MACHINE_ARN,
    input=json.dumps(data)
)
```

### Pattern 8: Inter-Lambda Communication

```python
# Local (function calls)
result = validate_entity(entity)

# Lambda (invoke another Lambda)
import boto3
lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='askiam-entity-validator-dev',
    InvocationType='RequestResponse',  # Sync
    Payload=json.dumps({'entity_id': entity_id})
)

result = json.loads(response['Payload'].read())
```

### Pattern 9: Error Handling

```python
# Local
try:
    result = process()
except ValueError as e:
    return {'error': str(e)}, 400
except Exception as e:
    return {'error': 'Internal error'}, 500

# Lambda
try:
    result = process()
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
except ValueError as e:
    logger.error(f"Validation error: {e}")
    return {
        'statusCode': 400,
        'body': json.dumps({'error': str(e)})
    }
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    return {
        'statusCode': 500,
        'body': json.dumps({'error': 'Internal error'})
    }
```

### Pattern 10: State Management

```python
# Local (in-memory session)
session_data = {'user_id': user_id}
history = []

# Lambda (stateless, use DynamoDB for state)
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('askiam-request-state-dev')

# Store state
table.put_item(Item={
    'request_id': request_id,
    'user_id': user_id,
    'history': history,
    'ttl': int(time.time()) + 3600
})

# Retrieve state
response = table.get_item(Key={'request_id': request_id})
state = response.get('Item', {})
```

## Common Dependencies for Lambda

```txt
# requirements.txt for Lambda functions
boto3>=1.28.0              # AWS SDK
psycopg2-binary>=2.9.0     # PostgreSQL
opensearch-py>=2.0.0       # OpenSearch client
requests-aws4auth>=1.2.0   # AWS request signing
python-dateutil>=2.8.0     # Date utilities
```

## Lambda Layer for Shared Dependencies

Create a Lambda layer for shared packages:

```bash
# Create layer structure
mkdir -p python/lib/python3.11/site-packages

# Install packages
pip install -r requirements.txt -t python/lib/python3.11/site-packages/

# Create layer zip
zip -r lambda-layer.zip python/

# Upload to S3
aws s3 cp lambda-layer.zip s3://your-bucket/

# Reference in CloudFormation
Layers:
  - arn:aws:lambda:us-east-1:123456789012:layer:askiam-dependencies:1
```

## Function Template Structure

```python
"""
Module: {function_name}
Description: {what the function does}
Inputs: {describe event structure}
Outputs: {describe response structure}
"""

import json
import boto3
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']
BUCKET_NAME = os.environ['BUCKET_NAME']

def helper_function_1(input_data):
    """Helper function for shared logic"""
    try:
        logger.info(f"Helper 1 processing: {input_data}")
        # Logic here
        return result
    except Exception as e:
        logger.error(f"Error in helper 1: {e}")
        raise

def helper_function_2(input_data):
    """Another helper function"""
    try:
        logger.info(f"Helper 2 processing: {input_data}")
        # Logic here
        return result
    except Exception as e:
        logger.error(f"Error in helper 2: {e}")
        raise

def handler(event, context):
    """
    Main Lambda handler
    
    Event format:
    {
        "field1": "value1",
        "field2": "value2"
    }
    
    Response format:
    {
        "statusCode": 200,
        "body": {...}
    }
    """
    start_time = datetime.utcnow()
    
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        logger.info(f"Handling request: {context.request_id}")
        
        # Validate input
        required_fields = ['field1', 'field2']
        missing = [f for f in required_fields if f not in body]
        if missing:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing fields: {missing}'})
            }
        
        # Process request
        result = helper_function_1(body['field1'])
        result = helper_function_2(result)
        
        # Log to DynamoDB if needed
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'request_id': context.request_id,
            'timestamp': int(datetime.utcnow().timestamp()),
            'status': 'SUCCESS',
            'duration_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000)
        })
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'data': result,
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'requestId': context.request_id
            })
        }
```

## Testing Patterns

```python
# Unit test pattern
import pytest
from moto import mock_dynamodb, mock_s3

@mock_dynamodb
def test_handler_success():
    # Setup
    os.environ['TABLE_NAME'] = 'test-table'
    
    # Create test table
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(...)
    
    # Call handler
    event = {'body': json.dumps({'field1': 'value1'})}
    context = MockContext()
    
    # Assert
    response = handler(event, context)
    assert response['statusCode'] == 200

# Local testing with SAM
# sam local start-api
# curl -X POST http://localhost:3000/chat -d '{"message": "test"}'
```

## Performance Optimization

```python
# 1. Reuse boto3 clients (outside handler)
# Instead of creating inside handler
s3_client = boto3.client('s3')  # Created once, reused

# 2. Connection pooling
# boto3 handles this automatically

# 3. Minimize cold start time
# - Remove unnecessary imports
# - Use smaller dependencies
# - Create Lambda layer for heavy packages

# 4. Memory optimization
# Lambda CPU scales with memory
# 512 MB = fast CPU, but higher cost
# 128 MB = slow CPU, but cheaper
# Find optimal balance for your workload

# 5. Timeout tuning
# Set timeout to realistic value
# Too high = wasted credits on failures
# Too low = legitimate timeouts

# 6. Caching
# Use ElastiCache for hot data
# Use Lambda environment for constants

# Example: Connection pooling
import psycopg2
from psycopg2 import pool

# Create pool once
db_pool = None

def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 3,  # min and max connections
            host=creds['host'],
            # other params
        )
    return db_pool

def handler(event, context):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        # Use connection
        pass
    finally:
        pool.putconn(conn)
```

## Monitoring & Debugging

```python
# Using CloudWatch X-Ray
import aws_xray_sdk.core

@aws_xray_sdk.core.xray_recorder.capture('operation_name')
def expensive_operation():
    pass

# Structured logging for better queries
logger.info(json.dumps({
    'timestamp': datetime.utcnow().isoformat(),
    'request_id': request_id,
    'user_id': user_id,
    'action': 'process_message',
    'status': 'completed',
    'duration_ms': duration
}))

# CloudWatch insights query
fields @timestamp, @message, duration_ms
| stats avg(duration_ms) as avg_duration by action
```

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Creating clients inside handler | Create outside, reuse |
| Not closing DB connections | Use try/finally blocks |
| Hardcoding secrets | Use Secrets Manager |
| Ignoring cold starts | Optimize imports, use layers |
| No error handling | Wrap everything in try/except |
| Not logging enough | Use structured logging |
| Resource limits ignored | Check Lambda limits (15 min, 10GB) |
| No monitoring setup | Add CloudWatch alarms from start |

---

This guide provides patterns for converting your local AskIAM code to AWS Lambda functions.
