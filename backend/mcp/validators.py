from core.types import IAMState
from core.config_loader import load_config
from mcp.tools.entity_validator import validate_entity_tool
from mcp.tools.sql_generator import generate_sql_tool
from mcp.tools.sql_validator import validate_sql_tool
from toolbox_langchain import ToolboxClient


def _is_error_result(result: str) -> bool:
    """
    Check if a result string represents an error from the tool/database.
    
    Args:
        result: The result string from a tool invocation
        
    Returns:
        True if the result indicates an error, False otherwise
    """
    if not isinstance(result, str):
        return False
    
    result_lower = result.lower()
    error_indicators = [
        "error",
        "unable to execute",
        "exception",
        "invalid",
        "failed",
        "does not exist",
        "sqlstate"
    ]
    
    return any(indicator in result_lower for indicator in error_indicators)


def run_validations(state: IAMState) -> IAMState:
    cfg = load_config()
    entities = cfg["entities"]

    try:
        for key, entity in entities.items():
            value = state.get(f"{key}_name")
            
            # Skip validation if value is None (not extracted)
            if value is None:
                continue

            # Validate entity
            tool_input = {
                "table": entity["table"],
                "id_column": entity["id_column"],
                "name_column": entity["name_column"],
                "value": value,
            }

            result = validate_entity_tool.invoke(tool_input)

            # Check for errors in result
            if _is_error_result(result):
                state["error"] = f"{entity['error']}: {result}"
                return state
            
            # Check for empty/no results (entity not found)
            if not result or result == "[]" or result == "null" or (isinstance(result, str) and result.strip() == ""):
                state["error"] = entity["error"]
                return state

        # After individual entity validations, check relationships
        # Specifically: Role must belong to the requested Application
        if state.get("role_name") and state.get("application_name"):
            state = _validate_role_application_relationship(state)
            if state.get("error"):
                return state

    except Exception as e:
        state["error"] = str(e)

    return state


def _validate_role_application_relationship(state: IAMState) -> IAMState:
    """
    Validate that the requested Role actually belongs to the requested Application.
    
    This checks the foreign key relationship in the roles table where app_name
    must match the requested application_name.
    """
    cfg = load_config()
    
    role_name = state.get("role_name")
    app_name = state.get("application_name")
    
    # Build SQL to check if role belongs to the application
    sql_instruction = (
        f"Generate a SQL query that selects role_id from roles "
        f"where role_name = '{role_name}' and app_name = '{app_name}' LIMIT 1"
    )
    
    try:
        sql = generate_sql_tool.invoke({"instruction": sql_instruction})
        
        validate_sql_tool.invoke(
            {"sql": sql, "allowed_table": "roles"}
        )
        
        cfg = load_config()
        with ToolboxClient(cfg["toolbox"]["url"]) as client:
            sql_tool = client.load_toolset("iam")[0]
            result = sql_tool.invoke({"sql": sql})
        
        # Check for errors in result
        if _is_error_result(result):
            state["error"] = f"Database error during relationship validation: {result}"
            return state
        
        # Check if result is empty
        if result and result != "[]" and result != "null" and (isinstance(result, str) and result.strip() != ""):
            return state
        else:
            # Relationship invalid
            state["error"] = (
                f"Relationship invalid: {role_name} does not exist in {app_name}. "
                f"This role may belong to a different application."
            )
            return state
            
    except Exception as e:
        state["error"] = f"Relationship validation error: {str(e)}"
        return state
