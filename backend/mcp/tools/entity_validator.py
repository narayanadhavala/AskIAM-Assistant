from langchain_core.tools import tool
from toolbox_langchain import ToolboxClient

from core.config_loader import load_config
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
    """
    
    # Handle None/empty values
    if value is None or value == "":
        return f"Error: Empty value provided for {name_column} in {table}"

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
    with ToolboxClient(cfg["toolbox"]["url"]) as client:
        sql_tool = client.load_toolset("iam")[0]
        return sql_tool.invoke({"sql": sql})
