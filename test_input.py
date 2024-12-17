import asyncio
import json
import logging
from app.utils.input_validator import InputValidator
from app.models.user_input import UserInput

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_validation_result(result, user_input: str):
    """Print detailed validation results"""
    print("\n" + "="*50)
    print("INPUT VALIDATION DETAILS")
    print("="*50)
    
    print(f"\nUser Input: {user_input}")
    
    print("\n1. Basic Validation:")
    print(f"   Valid: {result.is_valid}")
    print(f"   Input Type: {result.input_type}")
    
    print("\n2. Content Analysis:")
    print(f"   Has Background Info: {result.has_background}")
    print(f"   Background Completeness: {result.background_completeness:.2f}/1.0")
    print(f"   Has Goals: {result.has_goals}")
    print(f"   Goals Clarity: {result.goals_clarity:.2f}/1.0")
    print(f"   Overall Clarity: {result.clarity_score:.2f}/1.0")
    
    print("\n3. Safety Assessment:")
    print(f"   Safety Score: {result.safety_score:.2f}/1.0")
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    if result.detected_preferences:
        print("\n4. Detected Preferences:")
        for key, value in result.detected_preferences.items():
            print(f"   {key}: {value}")
    
    if result.suggestions:
        print("\n5. Suggestions for Improvement:")
        for suggestion in result.suggestions:
            print(f"   {suggestion}")
    
    if result.clarification_questions:
        print("\n6. Clarification Needed:")
        for question in result.clarification_questions:
            print(f"   {question}")
            
    if result.validation_details:
        print("\n7. Additional Details:")
        for key, value in result.validation_details.items():
            print(f"   {key}: {value}")
    
    print("\n" + "="*50 + "\n")

async def main():
    validator = InputValidator()
    previous_input = None
    
    print("""
===========================================
    Input Validation Testing Console
===========================================
Commands:
- Type your input to validate
- Type 'exit' to quit
- Press Ctrl+C to force quit
===========================================
""")
    
    while True:
        try:
            user_text = input("> ").strip()
            if not user_text:
                continue
            
            if user_text.lower() == 'exit':
                print("\nExiting normally...")
                break
            
            logging.info(f"Processing input: {user_text}")
            logging.info(f"Previous context: {previous_input}")
            
            result = await validator.validate_input(
                UserInput(
                    raw_input=user_text,
                    metadata={"previous_input": previous_input} if previous_input else {}
                )
            )
            
            logging.info(f"Validation complete: {result.model_dump_json()}")
            print_validation_result(result, user_text)
            
            previous_input = user_text
            
        except EOFError:
            print("\nExiting due to EOF...")
            break
        except KeyboardInterrupt:
            print("\nExiting due to user interrupt...")
            break
        except Exception as e:
            logging.error(f"Error during validation: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
            print("Please try again.")
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
        print(f"\nApplication error: {str(e)}")
    finally:
        print("\nGoodbye!")
