import time
from langchain_core.tools import tool
from toolbox_langchain import ToolboxClient

from core.config_loader import load_config
from core.tracer import get_tracer
from mcp.tools.sql_generator import generate_sql_tool
from mcp.tools.sql_validator import validate_sql_tool


@tool
def validate_entity_tool(
    *,
    table: str,
    id_column: str,
    name_column: str,
    value: str = None,
) -> str:
    """
    Generic IAM entity validation tool.

    Generates and executes:
    SELECT <id_column> FROM <table> WHERE <name_column> = ? LIMIT 1
    
    Returns: JSON list of matching records or error message
    
    Includes retry logic to handle transient connection issues with the toolbox.
    """
    
    # Handle None/empty values
    if value is None or value == "":
        return f"Error: Empty value provided for {name_column} in {table}"

    input_params = {
        "table": table,
        "id_column": id_column,
        "name_column": name_column,
        "value": value
    }

    sql = generate_sql_tool.invoke(
        {
            "instruction": (
                f"Generate a SQL query that selects {id_column} "
                f"from {table} where {name_column} equals '{value}'"
            )
        }
    )

    validate_sql_tool.invoke(
        {"sql": sql, "allowed_table": table}
    )

    cfg = load_config()
    
    # Retry logic for transient connection errors
    max_retries = 3
    retry_delay = 0.5  # seconds
    last_error = None
    
    for attempt in range(max_retries):
        try:
            with ToolboxClient(cfg["toolbox"]["url"]) as client:
                sql_tool = client.load_toolset("iam")[0]
                result = sql_tool.invoke({"sql": sql})
            
            # Trace tool invocation
            tracer = get_tracer()
            if tracer.is_enabled():
                tracer.trace_tool("validate_entity_tool", input_params, result)
            
            return result
            
        except (ConnectionError, ConnectionResetError, OSError, TimeoutError, BrokenPipeError) as e:
            # Handle connection errors with retry
            last_error = e
            error_msg = str(e)
            
            # Check for specific connection reset errors
            if "Connection reset" in error_msg or "104" in error_msg or "connection refused" in error_msg.lower():
                if attempt < max_retries - 1:
                    # Wait before retrying with exponential backoff
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
            
            # If it's the last attempt or not a retryable error, return the error
            return f"Error: {error_msg}"
        
        except Exception as e:
            # For non-connection errors, return immediately
            last_error = e
            return f"Error: {str(e)}"
    
    # If all retries exhausted
    if last_error:
        return f"Error: {str(last_error)} (after {max_retries} retries)"
