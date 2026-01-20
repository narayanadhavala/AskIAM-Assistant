from typing import TypedDict, Optional, List

class IAMState(TypedDict):
    # Input
    raw_request: str
    
    # Extracted entities
    user_name: Optional[str]
    application_name: Optional[str]
    role_name: Optional[str]
    
    # RAG validation
    rag_validation: Optional[str]
    rag_documents: Optional[List[dict]]
    
    # MCP validation
    mcp_validation: Optional[str]
    mcp_errors: Optional[List[str]]
    
    # Final result
    is_valid: Optional[bool]
    error: Optional[str]
    final_response: Optional[str]
    
    # Pipeline metadata
    processing_steps: Optional[List[str]]
