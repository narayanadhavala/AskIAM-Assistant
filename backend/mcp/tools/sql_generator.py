from langchain_core.tools import tool
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from core.model_factory import create_llm
from core.tracer import get_tracer

@tool
def generate_sql_tool(instruction: str) -> str:
    """
    Generate exactly one MySQL SELECT statement.
    """

    model = create_llm()

    system = SystemMessagePromptTemplate.from_template(
        """
You generate PostgreSQL SELECT statements.

SCHEMA:

Users(UserID, UserName, Email, Manager)
Applications(AppID, AppName, AppOwner)
Roles(RoleID, RoleName, AppName, Owner)

STRICT RULES:
- EXACTLY one SELECT statement
- SELECT only the ID column
- WHERE must use the correct Name column
- ALWAYS quote table names with double quotes: "TableName"
- ALWAYS quote column names with double quotes: "ColumnName"
- NO SELECT *
- NO JOIN, UNION, SUBQUERY
- NO INSERT, UPDATE, DELETE
- NO comments
- Return ONLY raw SQL

EXAMPLES:
SELECT "UserID" FROM "Users" WHERE "UserName" = 'John.Doe' LIMIT 1
SELECT "AppID" FROM "Applications" WHERE "AppName" = 'Workday' LIMIT 1
SELECT "RoleID" FROM "Roles" WHERE "RoleName" = 'HR Analyst' LIMIT 1
"""
    )

    human = HumanMessagePromptTemplate.from_template("{instruction}")
    prompt = ChatPromptTemplate.from_messages([system, human])

    result = model.invoke(
        prompt.format_messages(instruction=instruction)
    )

    sql_result = result.content.strip()
    
    # Trace tool invocation
    tracer = get_tracer()
    if tracer.is_enabled():
        tracer.trace_tool("generate_sql_tool", {"instruction": instruction}, sql_result)
    
    return sql_result
