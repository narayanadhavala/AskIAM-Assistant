"""
Orchestrator module for IAM access validation.
Now uses the LangGraph pipeline for enhanced processing with MCP and RAG nodes.
"""

from langgraph_pipeline import invoke_pipeline

def handle_request(text: str) -> str:
    """
    Handle IAM access requests using the LangGraph pipeline.
    
    The pipeline combines:
    - MCP (Model Context Protocol) for entity extraction and validation
    - RAG (Retrieval Augmented Generation) for knowledge base validation
    
    Args:
        text: The user's IAM access request
        
    Returns:
        The validation result (VALID or INVALID with details)
    """
    return invoke_pipeline(text)

