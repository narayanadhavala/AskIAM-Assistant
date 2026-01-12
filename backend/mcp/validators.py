from core.types import IAMState
from core.config_loader import load_config
from mcp.tools.entity_validator import validate_entity_tool
from mcp.trace import get_trace_handler


def run_validations(state: IAMState) -> IAMState:
    cfg = load_config()
    entities = cfg["entities"]
    trace_handler = get_trace_handler()

    try:
        for key, entity in entities.items():
            value = state.get(f"{key}_name")
            
            # Skip validation if value is None (not extracted)
            if value is None:
                trace_handler.on_tool_start(
                    {"name": f"validate_entity_tool ({entity['table']})"},
                    f"Skipped: value is None"
                )
                trace_handler.on_tool_end(f"Skipped validation: {key}_name not extracted")
                continue

            # Log tool start
            tool_input = {
                "table": entity["table"],
                "id_column": entity["id_column"],
                "name_column": entity["name_column"],
                "value": value,
            }
            trace_handler.on_tool_start(
                {"name": f"validate_entity_tool ({entity['table']})"},
                str(tool_input)
            )

            result = validate_entity_tool.invoke(tool_input)
            
            # Log tool end
            trace_handler.on_tool_end(str(result))

            if not result:
                state["error"] = entity["error"]
                return state

    except Exception as e:
        state["error"] = str(e)
        trace_handler.on_tool_end(f"Error: {state['error']}")

    return state
