from typing import TypedDict, List, Dict, Optional
from .user_input import UserInput
from .validation_result import ValidationResult

class GraphState(TypedDict):
    """Type definition for graph state"""
    user_input: UserInput
    validation_result: ValidationResult
    messages: List[Dict]
    next_step: str
    token: Optional[str]
