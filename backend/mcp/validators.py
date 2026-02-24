from core.types import IAMState
from core.config_loader import load_config
from core.langfuse_integration import log_event
from mcp.tools.entity_validator import validate_entity_tool
from mcp.tools.sql_generator import generate_sql_tool
from mcp.tools.sql_validator import validate_sql_tool
from toolbox_langchain import ToolboxClient


def _is_error_result(result: str) -> bool:
    """
    Check if a result string represents a critical error from the tool/database.
    
    Args:
        result: The result string from a tool invocation
        
    Returns:
        True if the result indicates a critical error, False otherwise
    """
    if not isinstance(result, str):
        return False
    
    result_lower = result.lower()
    
    # Critical error indicators (not transient)
    critical_indicators = [
        "error",
        "unable to execute",
        "exception",
        "invalid",
        "failed",
        "does not exist",
        "sqlstate"
    ]
    
    return any(indicator in result_lower for indicator in critical_indicators)


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
            
            # Log MCP tool call
            log_event(
                "mcp_tool",
                tool_name="entity_validator",
                table=entity["table"],
                input_params=tool_input,
                result=result
            )

            # Check for transient errors (connection issues, timeouts)
            # These should not immediately fail validation
            if isinstance(result, str) and any(ind in result.lower() for ind in [
                "connection reset", "connection refused", "[errno 104]", 
                "timeout", "broken pipe", "after 3 retries"
            ]):
                # Log transient error but continue validation
                # This allows other entities to be checked
                if "mcp_errors" not in state:
                    state["mcp_errors"] = []
                state["mcp_errors"].append(f"{entity['error']}: {result}")
                log_event(
                    "validation",
                    step_name=f"{key}_existence",
                    entity_type=key,
                    entity_value=value,
                    is_valid=False,
                    details={"error_type": "transient", "error_message": result}
                )
                continue
            
            # Check for critical errors in result
            if _is_error_result(result):
                state["error"] = f"{entity['error']}: {result}"
                log_event(
                    "validation",
                    step_name=f"{key}_existence",
                    entity_type=key,
                    entity_value=value,
                    is_valid=False,
                    details={"error_type": "critical", "error_message": result}
                )
                return state
            
            # Check for empty/no results (entity not found)
            if not result or result == "[]" or result == "null" or (isinstance(result, str) and result.strip() == ""):
                state["error"] = entity["error"]
                log_event(
                    "validation",
                    step_name=f"{key}_existence",
                    entity_type=key,
                    entity_value=value,
                    is_valid=False,
                    details={"error_type": "not_found"}
                )
                return state
            
            # Entity found - log successful validation
            log_event(
                "validation",
                step_name=f"{key}_existence",
                entity_type=key,
                entity_value=value,
                is_valid=True,
                details={"result_summary": str(result)[:200]}
            )

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
        
        # Log SQL generation
        log_event(
            "sql",
            operation_type="generate",
            sql_query=sql
        )
        
        validate_sql_result = validate_sql_tool.invoke(
            {"sql": sql, "allowed_table": "roles"}
        )
        
        # Log SQL validation
        log_event(
            "sql",
            operation_type="validate",
            sql_query=sql,
            validation_result=str(validate_sql_result)
        )
        
        cfg = load_config()
        with ToolboxClient(cfg["toolbox"]["url"]) as client:
            sql_tool = client.load_toolset("iam")[0]
            result = sql_tool.invoke({"sql": sql})
        
        # Log SQL execution
        log_event(
            "mcp_tool",
            tool_name="sql_executor",
            table="roles",
            input_params={"sql": sql},
            result=result
        )
        
        # Check for errors in result
        if _is_error_result(result):
            state["error"] = f"Database error during relationship validation: {result}"
            log_event(
                "validation",
                step_name="role_application_relationship",
                entity_type="role_application",
                entity_value=f"{role_name}_in_{app_name}",
                is_valid=False,
                details={"error_type": "database_error", "error_message": result}
            )
            return state
        
        # Check if result is empty
        if result and result != "[]" and result != "null" and (isinstance(result, str) and result.strip() != ""):
            log_event(
                "validation",
                step_name="role_application_relationship",
                entity_type="role_application",
                entity_value=f"{role_name}_in_{app_name}",
                is_valid=True,
                details={"result_summary": str(result)[:200]}
            )
            return state
        else:
            # Relationship invalid
            state["error"] = (
                f"Relationship invalid: {role_name} does not exist in {app_name}. "
                f"This role may belong to a different application."
            )
            log_event(
                "validation",
                step_name="role_application_relationship",
                entity_type="role_application",
                entity_value=f"{role_name}_in_{app_name}",
                is_valid=False,
                details={"error_type": "relationship_not_found"}
            )
            return state
            
    except Exception as e:
        state["error"] = f"Relationship validation error: {str(e)}"
        log_event(
            "validation",
            step_name="role_application_relationship",
            entity_type="role_application",
            entity_value=f"{role_name}_in_{app_name}",
            is_valid=False,
            details={"error_type": "exception", "error_message": str(e)}
        )
        return state
