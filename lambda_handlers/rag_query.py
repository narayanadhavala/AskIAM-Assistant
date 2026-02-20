"""
RAG Query Lambda Function Handler
Performs vector search using OpenSearch and queries Bedrock LLM
"""

import json
import boto3
import os
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Environment variables
OPENSEARCH_COLLECTION = os.environ.get('OPENSEARCH_COLLECTION')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
BEDROCK_EMBEDDING_MODEL = os.environ.get('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')

# AWS clients
aoss = boto3.client('opensearchserverless')
bedrock_runtime = boto3.client('bedrock-runtime')
bedrock = boto3.client('bedrock')

def get_opensearch_connection():
    """Create OpenSearch Serverless connection with AWS authentication"""
    try:
        # Get collection endpoint
        collection = aoss.describe_collection(name=OPENSEARCH_COLLECTION)
        endpoint = collection['collectionDetail']['collectionEndpoint']
        
        # Parse endpoint
        endpoint_url = f"https://{endpoint.split('://')[1]}" if '://' in endpoint else f"https://{endpoint}"
        
        # Create auth
        service = 'aoss'
        region = os.environ.get('AWS_REGION', 'us-east-1')
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, region, service)
        
        # Create client
        client = OpenSearch(
            hosts=[{'host': endpoint_url.replace('https://', ''), 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_connections=1
        )
        
        return client
    except Exception as e:
        print(f"Error connecting to OpenSearch: {str(e)}")
        raise

def get_embedding(text):
    """Get embedding from Bedrock"""
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_EMBEDDING_MODEL,
            body=json.dumps({
                'inputText': text
            })
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise

def search_vector_store(query_text, top_k=5):
    """Search OpenSearch for relevant documents"""
    try:
        # Get embedding for query
        query_embedding = get_embedding(query_text)
        
        # Connect to OpenSearch
        os_client = get_opensearch_connection()
        
        # Build search query
        search_query = {
            'size': top_k,
            'query': {
                'knn': {
                    'vector': {
                        'vector': query_embedding,
                        'k': top_k
                    }
                }
            }
        }
        
        # Execute search
        results = os_client.search(index=OPENSEARCH_INDEX, body=search_query)
        
        # Extract relevant documents
        documents = []
        for hit in results['hits']['hits']:
            documents.append({
                'id': hit['_id'],
                'score': hit['_score'],
                'content': hit['_source'].get('text', ''),
                'metadata': hit['_source'].get('metadata', {})
            })
        
        return documents
    except Exception as e:
        print(f"Error searching vector store: {str(e)}")
        return []

def invoke_bedrock_model(query, context_documents):
    """Query Bedrock LLM with context from vector search"""
    try:
        # Build context from retrieved documents
        context = "\n".join([
            f"[Document {i+1}]\n{doc['content']}\nMetadata: {doc['metadata']}"
            for i, doc in enumerate(context_documents[:3])  # Use top 3 docs
        ])
        
        # Build prompt
        system_prompt = """You are an IAM (Identity and Access Management) assistant. 
Your role is to help users with access requests and validations. 
Based on the provided context and user query, provide helpful and accurate responses.
Be concise and professional in your responses."""
        
        user_message = f"""Context from IAM knowledge base:
{context}

User Query: {query}

Please provide a helpful response to the user's query based on the context provided."""
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            messages=[
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            system=system_prompt,
            max_tokens=500
        )
        
        # Parse response
        result = json.loads(response['body'].read())
        
        # Extract text from response
        if 'content' in result and len(result['content']) > 0:
            response_text = result['content'][0]['text']
        else:
            response_text = "Unable to generate response"
        
        return response_text
        
    except Exception as e:
        print(f"Error invoking Bedrock model: {str(e)}")
        raise

def handler(event, context):
    """
    RAG Query handler
    
    Expected event structure:
    {
        "query": "I need access to HR Analyst role",
        "use_context": true,
        "top_k": 5
    }
    """
    
    try:
        # Parse request
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        query = body.get('query', '')
        use_context = body.get('use_context', True)
        top_k = int(body.get('top_k', 5))
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: query'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        print(f"Processing RAG query: {query}")
        
        # Search vector store for relevant documents
        start_time = datetime.utcnow()
        retrieved_docs = search_vector_store(query, top_k)
        search_time = (datetime.utcnow() - start_time).total_seconds()
        
        print(f"Retrieved {len(retrieved_docs)} documents in {search_time:.2f}s")
        
        # Invoke Bedrock model with context
        start_time = datetime.utcnow()
        response_text = invoke_bedrock_model(query, retrieved_docs) if use_context else query
        inference_time = (datetime.utcnow() - start_time).total_seconds()
        
        print(f"Generated response in {inference_time:.2f}s")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'query': query,
                'response': response_text,
                'context': {
                    'retrieved_documents': retrieved_docs,
                    'document_count': len(retrieved_docs)
                },
                'metrics': {
                    'search_time_seconds': search_time,
                    'inference_time_seconds': inference_time,
                    'total_time_seconds': search_time + inference_time
                },
                'timestamp': datetime.utcnow().isoformat(),
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(f"Error in RAG query handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'RAG query failed',
                'message': str(e),
                'requestId': context.request_id
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
