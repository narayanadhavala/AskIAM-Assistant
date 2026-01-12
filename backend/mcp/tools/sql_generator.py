from langchain_core.tools import tool
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from core.model_factory import create_llm

@tool
def generate_sql_tool(instruction: str) -> str:
    """
    Generate exactly one MySQL SELECT statement.
    """

    model = create_llm()

    system = SystemMessagePromptTemplate.from_template(
        """
You generate MySQL SELECT statements.

SCHEMA:

Users(UserID, UserName, Email, Manager)
Applications(AppID, AppName, AppOwner)
Roles(RoleID, RoleName, AppName, Owner)

STRICT RULES:
- EXACTLY one SELECT statement
- SELECT only the ID column
- WHERE must use the correct Name column
- NO SELECT *
- NO JOIN, UNION, SUBQUERY
- NO INSERT, UPDATE, DELETE
- NO comments
- Return ONLY raw SQL
"""
    )

    human = HumanMessagePromptTemplate.from_template("{instruction}")
    prompt = ChatPromptTemplate.from_messages([system, human])

    result = model.invoke(
        prompt.format_messages(instruction=instruction)
    )

    return result.content.strip()
