import json
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from core.model_factory import create_llm
from core.types import IAMState

def extract_request(state: IAMState) -> IAMState:
    llm = create_llm()

    system = SystemMessagePromptTemplate.from_template(
        """
        Extract IAM access request parameters from user input.

        Return ONLY valid JSON. No markdown. No explanation. No extra text.

        Keys must be exactly:
        - user_name: The person's name (e.g., "John.Doe", "Aaron.Nichols")
        - application_name: The application name (e.g., "Workday", "NetSuite", "Azure AD")
        - role_name: The role or access level (e.g., "HR Analyst", "Admin", "Developer")

        Use null if unable to extract. Only use null when information is not provided.

        Examples:
        Input: "Aaron.Nichols needs HR Analyst access in Workday"
        Output: {{"user_name": "Aaron.Nichols", "application_name": "Workday", "role_name": "HR Analyst"}}

        Input: "Can I get admin access?"
        Output: {{"user_name": null, "application_name": null, "role_name": "Admin"}}

        Input: "Can I get access for Azure Admin in Azure AD"
        Output: {{"user_name": null, "application_name": "Azure AD", "role_name": "Azure Admin"}}

        Input: "I'm Venkata Dhavala and I need access for Developer role for GitHub"
        Output: {{"user_name": "Venkata.Dhavala", "application_name": "GitHub", "role_name": "Developer"}}
        """
    )

    human = HumanMessagePromptTemplate.from_template("{text}")
    prompt = ChatPromptTemplate.from_messages([system, human])

    try:
        out = llm.invoke(prompt.format_messages(text=state["raw_request"])).content
        # Clean up response: remove markdown code blocks if present
        out = out.strip()
        if out.startswith("```"):
            out = out.split("```")[1]
            if out.startswith("json"):
                out = out[4:]
            out = out.strip()
        
        data = json.loads(out)
        state.update(data)
    except json.JSONDecodeError as e:
        state["error"] = f"Extraction failed: Invalid JSON response from LLM"
    except Exception as e:
        state["error"] = f"Extraction failed: {str(e)}"

    return state
