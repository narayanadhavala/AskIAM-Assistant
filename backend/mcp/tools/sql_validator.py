import re
from langchain_core.tools import tool
from core.tracer import get_tracer

@tool
def validate_sql_tool(sql: str, allowed_table: str) -> str:
    """
    Validate SQL for safety, structure, and schema correctness.
    """

    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        raise ValueError("Only SELECT statements are allowed")

    if ";" in sql_clean[:-1]:
        raise ValueError("Multiple SQL statements detected")

    if not re.search(r"\bfrom\b", sql_clean):
        raise ValueError("SELECT must contain FROM clause")

    forbidden = ["insert", "update", "delete", "drop", "alter", "join", "union"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", sql_clean):
            raise ValueError(f"Forbidden SQL keyword: {word}")

    # Check table access: allow both quoted and unquoted identifiers
    # Since sql_clean is lowercased, also lowercase the table name in pattern
    # Pattern handles: FROM table_name or FROM "table_name"
    # Word boundary \b only applies to unquoted identifiers (quoted ones end with ")
    table_lower = allowed_table.lower()
    table_pattern = rf'\bfrom\s+(?:"{table_lower}"|{table_lower}\b)'
    if not re.search(table_pattern, sql_clean):
        raise ValueError("Unauthorized table access")

    result = "ok"
    
    # Trace tool invocation
    tracer = get_tracer()
    if tracer.is_enabled():
        tracer.trace_tool("validate_sql_tool", {"sql": sql, "allowed_table": allowed_table}, result)
    
    return result
