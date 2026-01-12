from rag.rag_engine import validate_with_rag
from mcp.graph import run_mcp

def handle_request(text: str) -> str:
    """Handle IAM access requests with detailed tracing."""
    rag_result = validate_with_rag(text)

    if rag_result:
        return rag_result

    return run_mcp(text)
