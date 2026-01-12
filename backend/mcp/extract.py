import json
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from core.model_factory import create_llm
from core.types import IAMState
from mcp.trace import get_trace_handler

def extract_request(state: IAMState) -> IAMState:
    llm = create_llm()
    trace_handler = get_trace_handler()

    system = SystemMessagePromptTemplate.from_template(
        """
        Extract IAM access request parameters.

        Return ONLY valid JSON.
        No markdown.
        No explanation.
        No extra text.

        Keys must be exactly:
        - user_name
        - app_name
        - role_name

        Use null if missing.

        Example:
        {{
          "user_name": "Aaron.Nichols",
          "app_name": "Workday",
          "role_name": "HR Analyst"
        }}
        """
    )

    human = HumanMessagePromptTemplate.from_template("{text}")
    prompt = ChatPromptTemplate.from_messages([system, human])

    try:
        # Log tool start
        trace_handler.on_tool_start({"name": "extract_request"}, state["raw_request"])
        
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
        
        # Log tool end
        trace_handler.on_tool_end(str(data))
    except json.JSONDecodeError as e:
        state["error"] = f"Extraction failed: Invalid JSON response from LLM"
        trace_handler.on_tool_end(f"Error: {state['error']}")
    except Exception as e:
        state["error"] = f"Extraction failed: {str(e)}"
        trace_handler.on_tool_end(f"Error: {state['error']}")

    return state
