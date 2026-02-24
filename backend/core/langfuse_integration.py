"""
Minimal Langfuse integration for IAM Assistant.
Provides observability and metrics with API.
"""

from typing import Optional, Dict, Any
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from langfuse import Langfuse
from pathlib import Path

# Load environment variables
load_dotenv()

# Global Langfuse instance
_langfuse_client: Optional[Langfuse] = None


def get_langfuse() -> Langfuse:
    """
    Get the global Langfuse client.
    Reads from environment variables:
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_HOST (or LANGFUSE_BASE_URL)
    
    Returns:
        Langfuse client instance
    """
    global _langfuse_client
    
    if _langfuse_client is None:
        # Ensure env vars are loaded with explicit path
        env_file = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_file, override=True)
        
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
        
        # Set OTEL endpoint to ensure OpenTelemetry uses the correct server
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = host
        
        # print(f"[Langfuse] Initializing...")
        # print(f"  Host: {host}")
        # print(f"  Public Key: {public_key[:15]}..." if public_key else "  Public Key: NOT SET")
        
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            base_url=host,
            debug=False
        )
    
    return _langfuse_client


def initialize_langfuse(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    base_url: Optional[str] = None,
    debug: bool = False
) -> Langfuse:
    """
    Initialize Langfuse client for observability.
    
    Args:
        public_key: Langfuse public key (defaults to LANGFUSE_PUBLIC_KEY env var)
        secret_key: Langfuse secret key (defaults to LANGFUSE_SECRET_KEY env var)
        base_url: Langfuse server URL (defaults to LANGFUSE_HOST or LANGFUSE_BASE_URL env var)
        debug: Enable debug logging
    
    Returns:
        Langfuse client instance
    """
    global _langfuse_client
    
    # Load environment from .env file explicitly
    env_file = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_file, override=True)
    
    # Use provided values or fall back to environment variables
    pk = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    url = base_url or os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
    
    # Set OTEL endpoint to ensure OpenTelemetry uses the correct server
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = url
    
    # print(f"[Langfuse] Initializing with:\n  Public Key: {pk[:20] if pk else 'NONE'}...\n  Base URL: {url}")
    
    _langfuse_client = Langfuse(
        public_key=pk,
        secret_key=sk,
        base_url=url,
        debug=debug
    )
    
    return _langfuse_client


@contextmanager
def trace_request(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating a root trace for a request.
    All operations inside this context will be nested under this trace.
    
    Usage:
        with trace_request("process_request", {"user_id": "123"}) as trace:
            # do work
            trace.update(output={"status": "complete"})
    
    Args:
        name: Name of the request/trace
        metadata: Optional metadata (user_id, session_id, etc.)
    """
    client = get_langfuse()
    
    # Create root span for the trace
    with client.start_as_current_span(
        name=name,
        metadata=metadata or {}
    ) as span:
        yield span


@contextmanager
def trace_span(name: str, input_data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating a nested span within the current trace.
    Automatically becomes a child of the current observation context.
    
    Usage:
        with trace_span("validate_user", {"user_id": "123"}) as span:
            # validation logic
            span.update(output={"valid": True})
    
    Args:
        name: Name of the span
        input_data: Input data for the span
        metadata: Optional additional metadata
    """
    client = get_langfuse()
    
    with client.start_as_current_observation(
        as_type="span",
        name=name,
        input=input_data or {},
        metadata=metadata or {}
    ) as span:
        yield span


def log_event(event_type: str, **data) -> None:
    """
    Unified event logging function for Langfuse observability.
    Routes events based on type and logs with appropriate structure.
    
    Args:
        event_type: Type of event - one of:
            - "node": Pipeline node execution
            - "tool": Generic tool invocation
            - "rag": RAG document retrieval
            - "mcp_tool": MCP tool invocation (entity_validator, sql_generator, etc)
            - "extraction": Entity extraction from LLM
            - "sql": SQL generation/validation/execution
            - "validation": Validation steps and checks
        
        **data: Type-specific keyword arguments (varies by event_type)
        
    Examples:
        # Node execution
        log_event("node", node_name="extract_entities", 
                 input_data={...}, output_data={...})
        
        # RAG operation
        log_event("rag", operation_name="similarity_search", 
                 query="...", filters={...}, results=[...])
        
        # MCP tool
        log_event("mcp_tool", tool_name="entity_validator", 
                 table="users", input_params={...}, result=...)
        
        # Entity extraction
        log_event("extraction", extraction_type="user", 
                 raw_request="...", context_used="...", 
                 extracted_value="...", confidence=0.95)
        
        # SQL operation
        log_event("sql", operation_type="generate", 
                 sql_query="SELECT...", validation_result="Safe")
        
        # Validation step
        log_event("validation", step_name="user_existence", 
                 entity_type="user", entity_value="john@...", 
                 is_valid=True, details={...})
    """
    client = get_langfuse()
    metadata = data.get('metadata', {})
    
    match event_type:
        case "node":
            # Node: initialize_request, extract_entities, etc.
            client.create_event(
                name=f"node_{data['node_name']}",
                input=data.get('input_data'),
                output=data.get('output_data'),
                metadata={**metadata, "type": "node", "node": data['node_name']}
            )
        
        case "tool":
            # Generic tool call
            client.create_event(
                name=data['tool_name'],
                input=data.get('input_params'),
                output=data.get('result'),
                metadata={**metadata, "type": "tool"}
            )
        
        case "rag":
            # RAG: similarity_search, entity_context_retrieval
            results = data.get('results', [])
            client.create_event(
                name=f"rag_{data['operation_name']}",
                input={"query": data.get('query'), "filters": data.get('filters')},
                output={
                    "result_count": data.get('result_count', len(results)),
                    "results_summary": [
                        {
                            "content": r.page_content[:200] if hasattr(r, 'page_content') else str(r)[:200],
                            "metadata": r.metadata if hasattr(r, 'metadata') else {}
                        }
                        for r in results
                    ]
                },
                metadata={**metadata, "type": "rag", "operation": data['operation_name']}
            )
        
        case "mcp_tool":
            # MCP: entity_validator, sql_generator, sql_executor
            client.create_event(
                name=f"mcp_tool_{data['tool_name']}",
                input={**data.get('input_params', {}), "table": data.get('table')},
                output=data.get('result'),
                metadata={**metadata, "type": "mcp_tool", "tool": data['tool_name'], "table": data.get('table')}
            )
        
        case "extraction":
            # Entity extraction: user, application, role
            client.create_event(
                name=f"extract_{data['extraction_type']}",
                input={"request": data.get('raw_request'), "context": (data.get('context_used', '')[:300])},
                output={"extracted": data.get('extracted_value'), "confidence": data.get('confidence')},
                metadata={**metadata, "type": "extraction", "extraction_type": data['extraction_type']}
            )
        
        case "sql":
            # SQL: generate, validate, execute
            output_data = {}
            if data.get('sql_query'):
                output_data["query"] = data.get('sql_query')
            if data.get('validation_result'):
                output_data["validation"] = data.get('validation_result')
            if data.get('error'):
                output_data["error"] = data.get('error')
            
            client.create_event(
                name=f"sql_{data['operation_type']}",
                input={"operation": data['operation_type']},
                output=output_data,
                metadata={**metadata, "type": "sql", "operation": data['operation_type']}
            )
        
        case "validation":
            # Validation: entity_existence, role_app_relationship, etc.
            client.create_event(
                name=f"validate_{data['step_name']}",
                input={"entity_type": data.get('entity_type'), "entity_value": data.get('entity_value')},
                output={"is_valid": data.get('is_valid'), "details": data.get('details', {})},
                metadata={**metadata, "type": "validation", "step": data['step_name'], "entity_type": data.get('entity_type')}
            )
        
        case _:
            raise ValueError(f"Unknown event_type: {event_type}. Must be one of: node, tool, rag, mcp_tool, extraction, sql, validation")


def flush() -> None:
    """Flush any pending traces to Langfuse."""
    client = get_langfuse()
    client.flush()
