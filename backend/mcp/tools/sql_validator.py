import re
from langchain_core.tools import tool

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

    table_pattern = rf"\bfrom\s+{allowed_table.lower()}\b"
    if not re.search(table_pattern, sql_clean):
        raise ValueError("Unauthorized table access")

    return "ok"
