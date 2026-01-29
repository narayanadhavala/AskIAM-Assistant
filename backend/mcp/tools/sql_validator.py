import re
from langchain_core.tools import tool
from core.tracer import get_tracer

@tool
def validate_sql_tool(sql: str, allowed_table: str) -> str:
    """
    Validate SQL for safety, structure, and schema correctness.
    """
    
    # Clean and normalize SQL
    sql_clean = sql.strip()
    
    # Remove markdown code blocks if present
    if "```" in sql_clean:
        parts = sql_clean.split("```")
        if len(parts) >= 2:
            sql_clean = parts[1]
        if sql_clean.startswith("sql"):
            sql_clean = sql_clean[3:]
    
    # Extract only the SELECT statement, removing explanatory text
    select_match = re.search(r'SELECT\s+.*?(?:LIMIT\s+\d+|;|$)', sql_clean, re.IGNORECASE | re.DOTALL)
    if select_match:
        sql_clean = select_match.group(0)
    
    sql_clean = sql_clean.strip()
    sql_lower = sql_clean.lower()

    if not sql_lower.startswith("select"):
        raise ValueError("Only SELECT statements are allowed")

    if not re.search(r"\bfrom\b", sql_lower):
        raise ValueError("SELECT must contain FROM clause")

    forbidden = ["insert", "update", "delete", "drop", "alter", "join", "union"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", sql_lower):
            raise ValueError(f"Forbidden SQL keyword: {word}")

    # Check table access: allow both quoted and unquoted identifiers
    # Pattern handles: FROM table_name or FROM "table_name"
    table_pattern = rf'\bfrom\s+(?:"{allowed_table}"|{allowed_table}\b)'
    if not re.search(table_pattern, sql_clean, re.IGNORECASE):
        raise ValueError("Unauthorized table access")

    result = "ok"
    
    # Trace tool invocation
    tracer = get_tracer()
    if tracer.is_enabled():
        tracer.trace_tool("validate_sql_tool", {"sql": sql, "allowed_table": allowed_table}, result)
    
    return result
