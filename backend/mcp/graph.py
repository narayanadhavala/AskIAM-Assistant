from core.types import IAMState
from mcp.extract import extract_request
from mcp.validators import run_validations

def run_mcp(text: str) -> str:
    state: IAMState = {
        "raw_request": text,
        "user_name": None,
        "application_name": None,
        "role_name": None,
        "error": None,
        "final_response": None,
    }

    # Step 1: Extract Request
    state = extract_request(state)
    
    if state.get("error"):
        return f"INVALID: {state['error']}"

    # Step 2: Run Validations
    state = run_validations(state)
    
    if state.get("error"):
        return f"INVALID: {state['error']}"

    result = (
        "VALID: "
        f"{state['user_name']} can request {state['role_name']} "
        f"in {state['application_name']}"
    )
    
    return result
