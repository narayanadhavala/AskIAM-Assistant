from typing import TypedDict, Optional

class IAMState(TypedDict):
    raw_request: str

    user_name: Optional[str]
    app_name: Optional[str]
    role_name: Optional[str]

    error: Optional[str]
    final_response: Optional[str]
