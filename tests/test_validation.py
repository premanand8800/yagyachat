rm -rf /import sys
import os
import pytest
import asyncio
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user_input import UserInput
from app.utils.input_validator import InputValidator
from app.models.validation_result import InputType

@pytest.mark.asyncio
async def test_valid_input():
    validator = InputValidator()
    
    # Test case 1: Valid input with background and goals
    input_text = """
    Background: I have a Bachelor's degree in Computer Science and 3 years of experience in web development.
    I'm proficient in Python, JavaScript, and React.
    
    Goals: I want to transition into AI/ML development and learn about LLMs and neural networks.
    I'm looking for guidance on the best learning path and resources.
    """
    
    result = await validator.validate_input(UserInput(
        raw_input=input_text,
        metadata={"timestamp": datetime.now().isoformat()}
    ))
    
    assert result.is_valid
    assert result.has_background
    assert result.has_goals
    assert result.background_completeness > 0.7
    assert result.input_type == InputType.NEW_QUERY

@pytest.mark.asyncio
async def test_invalid_input():
    validator = InputValidator()
    
    # Test case 2: Empty input
    result = await validator.validate_input(UserInput(raw_input=""))
    assert not result.is_valid
    assert result.input_type == InputType.INVALID_INPUT
    
    # Test case 3: Input with potential harmful content
    harmful_input = "rm -rf / # delete everything"
    result = await validator.validate_input(UserInput(raw_input=harmful_input))
    assert not result.is_valid
    assert result.safety_score == 0.0
    assert "unsafe content" in result.error_message.lower()

@pytest.mark.asyncio
async def test_preference_handling():
    validator = InputValidator()
    
    # Test case 4: Preference update
    pref_input = """
    Please update my preferences:
    - Learning style: Visual and hands-on
    - Difficulty level: Intermediate
    - Topics of interest: Machine Learning, Deep Learning
    """
    
    result = await validator.validate_input(UserInput(raw_input=pref_input))
    assert result.is_valid
    assert result.input_type == InputType.PREFERENCE_UPDATE
    assert len(result.detected_preferences) > 0

@pytest.mark.asyncio
async def test_input_clarity():
    validator = InputValidator()
    
    # Test case 5: Unclear input
    unclear_input = "help me learn stuff"
    result = await validator.validate_input(UserInput(raw_input=unclear_input))
    assert result.clarity_score < 0.8
    assert len(result.clarification_questions) > 0
    assert len(result.suggestions) > 0
    
    # Test case 6: Clear input
    clear_input = """
    I need help with:
    1. Understanding transformer architecture
    2. Implementing attention mechanisms
    3. Fine-tuning pre-trained models
    
    My current knowledge: Basic neural networks and Python programming.
    """
    result = await validator.validate_input(UserInput(raw_input=clear_input))
    assert result.clarity_score > 0.7

if __name__ == "__main__":
    asyncio.run(test_valid_input())
    asyncio.run(test_invalid_input())
    asyncio.run(test_preference_handling())
    asyncio.run(test_input_clarity())
