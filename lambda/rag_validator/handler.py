"""
RAGValidator Lambda Function
Validates IAM access using semantic search and LLM evaluation.
"""

import json
import logging
import os
from typing import Any, Dict, List
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.connection.base import Connection

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# AWS clients
ssm_client = boto3.client('ssm')
secrets_client = boto3.client('secretsmanager')


class RAGValidator:
    """Validates access using semantic search and LLM evaluation."""
    
    def __init__(self):
        self.opensearch_endpoint = os.getenv('OPENSEARCH_ENDPOINT')
        self.opensearch_client = self._create_opensearch_client()
        self.rag_threshold = self._load_rag_threshold()
    
    def _load_rag_threshold(self) -> float:
        """Load RAG confidence threshold from Parameter Store."""
        try:
            response = ssm_client.get_parameter(
                Name=f"/askiam/{os.getenv('ENVIRONMENT')}/app/rag-threshold"
            )
            return float(response['Parameter']['Value'])
        except Exception as e:
            logger.warning(f"Failed to load RAG threshold: {e}, using default 0.95")
            return 0.95
    
    def _create_opensearch_client(self) -> OpenSearch:
        """Create OpenSearch Serverless client with IAM authentication."""
        try:
            # For serverless, use port 443 and IAM auth
            client = OpenSearch(
                hosts=[{'host': self.opensearch_endpoint, 'port': 443}],
                http_auth=None,  # Use IAM auth
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=10
            )
            logger.info("OpenSearch Serverless client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client: {e}")
            raise
    
    def search_iam_metadata(self, user_id: str, app_id: str, role_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search OpenSearch for similar IAM access patterns.
        
        Args:
            user_id: User identifier
            app_id: Application identifier
            role_id: Role identifier
            k: Number of documents to retrieve
            
        Returns:
            List of matching documents from knowledge base
        """
        try:
            # Build search query for semantic similarity
            query = {
                "size": k,
                "query": {
                    "multi_match": {
                        "query": f"{user_id} {app_id} {role_id}",
                        "fields": ["user_name^2", "app_name^2", "role_name", "policy_json"]
                    }
                },
                "_source": ["user_name", "app_name", "role_name", "compliance_level", "policy_json", "timestamp"]
            }
            
            response = self.opensearch_client.search(
                body=query,
                index="iam_metadata"
            )
            
            documents = []
            for hit in response['hits']['hits']:
                documents.append({
                    'score': hit['_score'],
                    'source': hit['_source']
                })
            
            logger.info(f"Found {len(documents)} matching documents in OpenSearch")
            return documents
        
        except Exception as e:
            logger.warning(f"OpenSearch search failed: {e}")
            return []
    
    def search_access_patterns(self, user_id: str, app_id: str, role_id: str) -> Dict[str, Any]:
        """
        Search historical access patterns for approval likelihood.
        
        Args:
            user_id: User identifier
            app_id: Application identifier
            role_id: Role identifier
            
        Returns:
            Pattern analysis results
        """
        try:
            # Aggregation query for access patterns
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"user_id": user_id}},
                            {"match": {"app_id": app_id}},
                            {"match": {"role_id": role_id}},
                            {"match": {"status": "approved"}}
                        ]
                    }
                },
                "aggs": {
                    "approval_rate": {
                        "cardinality": {"field": "user_id"}
                    },
                    "recent_approvals": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "30d"
                        }
                    }
                }
            }
            
            response = self.opensearch_client.search(
                body=query,
                index="access_patterns"
            )
            
            total_hits = response['hits']['total']['value']
            
            return {
                'total_approvals': total_hits,
                'recent_pattern': 'yes' if total_hits > 0 else 'no',
                'aggs': response.get('aggregations', {})
            }
        
        except Exception as e:
            logger.warning(f"Access pattern search failed: {e}")
            return {'total_approvals': 0}
    
    def evaluate_with_llm(self, metadata: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to evaluate access compliance.
        
        Args:
            metadata: IAM metadata from OpenSearch
            patterns: Historical access patterns
            
        Returns:
            Compliance evaluation with confidence score
        """
        try:
            # In production, this would call a real LLM API
            # For now, use heuristic scoring based on retrieved documents
            
            compliance_score = 0.0
            reasons = []
            
            # Score based on metadata matches
            if metadata.get('documents'):
                doc_count = len(metadata['documents'])
                avg_score = sum(d.get('score', 0) for d in metadata['documents']) / doc_count
                compliance_score += avg_score * 0.5
                reasons.append(f"Found {doc_count} similar access patterns (avg match: {avg_score:.2f})")
            
            # Score based on historical patterns
            if patterns.get('total_approvals', 0) > 0:
                pattern_score = min(0.5, patterns['total_approvals'] * 0.05)  # Cap at 0.5
                compliance_score += pattern_score
                reasons.append(f"Historical approval pattern: {patterns['total_approvals']} similar approvals")
            
            # Score based on recency
            if patterns.get('recent_pattern') == 'yes':
                compliance_score += 0.1
                reasons.append("Recent similar access approved")
            
            # Normalize to 0-1
            confidence = min(1.0, compliance_score)
            
            return {
                'confidence': confidence,
                'is_valid': confidence >= self.rag_threshold,
                'reasons': reasons,
                'evaluation_method': 'semantic_matching'
            }
        
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return {
                'confidence': 0.0,
                'is_valid': False,
                'reasons': [f'Evaluation error: {str(e)}'],
                'evaluation_method': 'error'
            }


def lambda_handler(event, context):
    """
    Lambda handler for RAG validation.
    
    Args:
        event: {
            'user_id': int,
            'app_id': int,
            'role_id': int,
            'request_id': str,
            'raw_request': str,
            'context': {...}
        }
        
    Returns:
        {
            'is_valid': bool,
            'confidence': float,
            'documents': [...]
        }
    """
    validator = RAGValidator()
    
    try:
        user_id = event.get('user_id')
        app_id = event.get('app_id')
        role_id = event.get('role_id')
        
        if not all([user_id, app_id, role_id]):
            raise ValueError("Missing required parameters: user_id, app_id, role_id")
        
        logger.info(f"RAG validation: user={user_id}, app={app_id}, role={role_id}")
        
        # 1. Search for IAM metadata
        metadata_results = validator.search_iam_metadata(str(user_id), str(app_id), str(role_id), k=5)
        
        # 2. Search for access patterns
        pattern_results = validator.search_access_patterns(str(user_id), str(app_id), str(role_id))
        
        # 3. Evaluate with LLM/heuristics
        evaluation = validator.evaluate_with_llm(
            {'documents': metadata_results},
            pattern_results
        )
        
        result = {
            'request_id': event.get('request_id'),
            'is_valid': evaluation['is_valid'],
            'confidence': evaluation['confidence'],
            'evaluation_method': evaluation['evaluation_method'],
            'reason': ' | '.join(evaluation['reasons']),
            'documents': [
                {
                    'score': doc.get('score'),
                    'user_name': doc.get('source', {}).get('user_name'),
                    'app_name': doc.get('source', {}).get('app_name'),
                    'role_name': doc.get('source', {}).get('role_name'),
                    'compliance_level': doc.get('source', {}).get('compliance_level')
                }
                for doc in metadata_results
            ]
        }
        
        logger.info(f"RAG validation result: confidence={result['confidence']}, valid={result['is_valid']}")
        return result
    
    except Exception as e:
        logger.error(f"RAG validation error: {e}", exc_info=True)
        return {
            'is_valid': False,
            'confidence': 0.0,
            'reason': f'RAG validation error: {str(e)}',
            'request_id': event.get('request_id'),
            'documents': []
        }
