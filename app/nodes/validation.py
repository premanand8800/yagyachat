from typing import Dict, List, Optional
from datetime import datetime
import json
import logging
from langgraph.graph import StateGraph
from app.models.validation_result import ValidationResult, InputType
from app.models.preference import PreferenceValue, PreferenceUpdate, PreferenceOperation
from app.models.graph_state import GraphState
from app.utils.input_validator import InputValidator

class ValidationScope:
    """Enhanced scope including preference validation"""
    def __init__(self):
        self.max_length = 2000
        self.min_length = 50
        self.required_elements = ["background", "goals"]
        self.min_background_score = 0.7
        self.min_goals_score = 0.7
        self.max_preferences_per_category = 5

class ValidationNode:
    """Enhanced validation node with preference handling"""
    def __init__(self):
        self.validator = InputValidator()

    async def __call__(self, state: GraphState) -> GraphState:
        """Process the validation node"""
        try:
            # Basic length validation
            input_length = len(state.user_input.raw_input)
            if input_length < 1:
                state.validation_result = ValidationResult(
                    is_valid=False,
                    input_type=InputType.INVALID_INPUT,
                    error_message="Input cannot be empty",
                    has_background=False,
                    has_goals=False,
                    background_completeness=0.0,
                    clarity_score=0.0,
                    safety_score=0.0
                )
                state.next_step = "error"
                return state

            # Perform validation using our custom validator
            validation_result = await self.validator.validate_input(state.user_input)
            state.validation_result = validation_result

            # Determine next step based on validation result
            if not validation_result.is_valid:
                state.next_step = "error"
                state.messages.append({
                    "role": "system",
                    "content": f"Validation failed: {validation_result.error_message}"
                })
            elif validation_result.input_type == InputType.PREFERENCE_UPDATE:
                state.next_step = "update_preferences"
            elif validation_result.input_type == InputType.PREFERENCE_REMOVAL:
                state.next_step = "remove_preferences"
            elif validation_result.input_type == InputType.PREFERENCE_QUERY:
                state.next_step = "query_preferences"
            else:
                state.next_step = "process"
                
            return state

        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            state.validation_result = ValidationResult(
                is_valid=False,
                input_type=InputType.INVALID_INPUT,
                error_message=f"Validation error: {str(e)}",
                has_background=False,
                has_goals=False,
                background_completeness=0.0,
                clarity_score=0.0,
                safety_score=0.0
            )
            state.next_step = "error"
            return state

def create_validation_workflow() -> StateGraph:
    """Creates the complete validation workflow"""
    # Create workflow graph
    workflow = StateGraph(GraphState)
    
    # Add validation node
    validation_node = ValidationNode()
    workflow.add_node("validate", validation_node)
    
    # Define edges
    workflow.set_entry_point("validate")
    
    # Add conditional edges based on next_step
    workflow.add_edge("validate", "process", lambda x: x["next_step"] == "process")
    workflow.add_edge("validate", "error", lambda x: x["next_step"] == "error")
    workflow.add_edge("validate", "update_preferences", lambda x: x["next_step"] == "update_preferences")
    workflow.add_edge("validate", "remove_preferences", lambda x: x["next_step"] == "remove_preferences")
    workflow.add_edge("validate", "query_preferences", lambda x: x["next_step"] == "query_preferences")
    
    return workflow
