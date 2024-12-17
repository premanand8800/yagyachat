import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel

# Define Shared Context
@dataclass
class SharedContext:
    user_input: str
    conversation_history: List[dict] = field(default_factory=list)
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    categories: Optional[List[str]] = None
    subcategories: Optional[List[str]] = None
    examples: Optional[List[str]] = None

# Result Models
class AnalysisResult(BaseModel):
    keywords: List[str]
    summary: str
    sentiment: str

class ClarificationResult(BaseModel):
    questions: List[str]

class ContentResult(BaseModel):
    categories: List[str]
    subcategories: List[str]
    examples: List[str]

# Initialize models with Llama 3.3 70B
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class SharedContext:
    text: str
    task_result: str = ""
    user_preferences: dict = None

# Define the primary agent
primary_agent = Agent(
    "openai:gpt-4o",
    deps_type=SharedContext,
    system_prompt="You are a task manager. Based on the input, decide which task to delegate."
)

# Define Agent A: Summarizer
summarizer_agent = Agent(
    "openai:gpt-4o",
    deps_type=SharedContext,
    system_prompt="You are a summarizer. Summarize the given input text concisely."
)

# Define Agent B: Sentiment Analyzer
sentiment_agent = Agent(
    "openai:gpt-4o",
    deps_type=SharedContext,
    system_prompt="You are a sentiment analyzer. Analyze the sentiment of the text."
)

# Define tools for primary agent
@primary_agent.tool
async def summarize_text(ctx: RunContext[SharedContext]) -> str:
    result = await summarizer_agent.run("Summarize this text", deps=ctx.deps)
    ctx.deps.task_result = result.data
    return ctx.deps.task_result

@primary_agent.tool
async def analyze_sentiment(ctx: RunContext[SharedContext]) -> str:
    result = await sentiment_agent.run("Analyze the sentiment of this text", deps=ctx.deps)
    ctx.deps.task_result = result.data
    return ctx.deps.task_result

# Main workflow
async def main():
    shared_context = SharedContext(text="The product was amazing! It exceeded my expectations.")
    
    # Primary agent dynamically delegates tasks
    result = await primary_agent.run("Process user input dynamically", deps=shared_context)
    print(result.data)

import asyncio
asyncio.run(main())


# Initialize the Manager Agent
manager_agent = Agent(
    MODEL,
    deps_type=SharedContext,
    system_prompt=(
        "You are a manager agent responsible for delegating tasks. "
        "For each user input, call the process_input function to handle the request. "
        "Be concise but informative in your responses."
    )
)

# Specialized Agents
input_analysis_agent = Agent(
    MODEL,
    deps_type=SharedContext,
    result_type=AnalysisResult,
    system_prompt=(
        "Analyze user input and return keywords, summary, and sentiment. "
        "Format each response as a list of keywords, a concise summary, and sentiment (positive, negative, or neutral). "
        "Focus on extracting key information and intentions."
    )
)

clarification_agent = Agent(
    MODEL,
    deps_type=SharedContext,
    result_type=ClarificationResult,
    system_prompt=(
        "Generate clarifying questions when input is unclear. "
        "Return a list of 2-3 specific questions to better understand the user's needs. "
        "Make questions direct and focused."
    )
)

content_generation_agent = Agent(
    MODEL,
    deps_type=SharedContext,
    result_type=ContentResult,
    system_prompt=(
        "Generate relevant categories, subcategories, and examples based on the input. "
        "Provide specific, actionable examples in each category. "
        "Focus on practical and useful information."
    )
)

@manager_agent.tool
async def process_input(ctx: RunContext[SharedContext], action_type: str = "analyze") -> str:
    """Process user input based on the specified action type.
    
    Args:
        ctx: The run context with shared context
        action_type: Type of processing to perform (analyze, clarify, or generate)
    """
    input_text = ctx.deps.user_input.lower()
    response = ""

    try:
        # Determine which agent to use based on input characteristics
        if "category" in input_text or "example" in input_text or action_type == "generate":
            # Use content generation agent
            result = await content_generation_agent.run(input_text, deps=ctx.deps)
            response = (
                f"Here are relevant categories and examples:\n\n"
                f"Categories: {', '.join(result.data.categories)}\n"
                f"Subcategories: {', '.join(result.data.subcategories)}\n"
                f"Examples: {', '.join(result.data.examples)}"
            )
            
        elif "?" in input_text or len(input_text.split()) < 3 or action_type == "clarify":
            # Use clarification agent
            result = await clarification_agent.run(input_text, deps=ctx.deps)
            response = (
                f"To better assist you, please answer these questions:\n\n" +
                "\n".join(f"- {q}" for q in result.data.questions)
            )
            
        else:
            # Default to input analysis
            result = await input_analysis_agent.run(input_text, deps=ctx.deps)
            response = (
                f"Analysis of your request:\n\n"
                f"Keywords: {', '.join(result.data.keywords)}\n"
                f"Summary: {result.data.summary}\n"
                f"Sentiment: {result.data.sentiment}"
            )

        # Update conversation history
        ctx.deps.conversation_history.append({
            "role": "user",
            "content": input_text
        })
        ctx.deps.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response

    except Exception as e:
        error_msg = f"Error processing your request: {str(e)}"
        ctx.deps.conversation_history.append({
            "role": "assistant",
            "content": error_msg
        })
        return error_msg

async def chat():
    # Initialize shared context
    shared_context = SharedContext(
        user_input="",
        conversation_history=[]
    )

    print("\nWelcome to the Llama 3.3 Assistant! 👋")
    print("I can help you with various topics. Type 'exit' to end our conversation.")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit command
            if user_input.lower() == "exit":
                print("\nGoodbye! Have a great day! 👋")
                break
                
            # Validate input
            if not user_input:
                print("Please enter a valid input.")
                continue

            # Update shared context
            shared_context.user_input = user_input
            
            # Process input through manager agent
            result = await manager_agent.run(
                "Process the user's input and provide an appropriate response.", 
                deps=shared_context
            )
            
            # Display response
            print("\nAssistant:", result.data)

        except Exception as e:
            print(f"\nI apologize, but I encountered an error: {str(e)}")
            print("Please try rephrasing your input.")

if __name__ == "__main__":
    asyncio.run(chat())