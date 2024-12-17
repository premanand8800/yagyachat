"""Custom exceptions for the application"""
from typing import Optional, Dict, Any

class ValidationError(Exception):
    """Base class for validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class LLMError(ValidationError):
    """Raised when there's an error with LLM operations"""
    pass

class PreferenceError(ValidationError):
    """Raised when there's an error processing preferences"""
    pass

class InputTypeError(ValidationError):
    """Raised when input type cannot be determined"""
    pass

class GuardrailsError(ValidationError):
    """Raised when there's an error with content safety checks"""
    pass

class ConversationMemoryError(ValidationError):
    """Raised when there's an error with conversation memory operations"""
    pass

class ParsingError(ValidationError):
    """Raised when there's an error parsing responses or data"""
    pass
