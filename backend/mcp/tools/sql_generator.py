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
        """You generate PostgreSQL SELECT statements.

SCHEMA:

users(user_id, user_name, email, manager)
applications(app_id, app_name, app_owner)
roles(role_id, role_name, app_name, owner)

STRICT RULES - DO NOT BREAK:
- EXACTLY one SELECT statement on one line
- SELECT only the ID column (user_id, app_id, or role_id)
- WHERE must use the correct Name column (user_name, app_name, or role_name)
- ALWAYS quote table and column names with double quotes
- NO SELECT *, NO JOIN, UNION, SUBQUERY
- NO INSERT, UPDATE, DELETE, NO comments
- Return ONLY raw SQL, nothing else

EXAMPLES:
SELECT "user_id" FROM "users" WHERE "user_name" = 'John.Doe' LIMIT 1
SELECT "app_id" FROM "applications" WHERE "app_name" = 'Workday' LIMIT 1
SELECT "role_id" FROM "roles" WHERE "role_name" = 'HR Analyst' LIMIT 1
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
