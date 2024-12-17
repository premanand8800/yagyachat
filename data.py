from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel

@dataclass
class SharedContext:
    text: str
    task_result: str = ""
    user_preferences: dict = None  # Optional for later user-specific tasks


# Initialize the GroqModel
model = GroqModel('llama-3.3-70b-versatile', api_key="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")

# Define the primary agent
primary_agent = Agent(
    model,
    deps_type=SharedContext,
    system_prompt=(
        "You are a task manager. Based on the given text, decide whether to: "
        "1. Summarize the text. "
        "2. Analyze the sentiment of the text. "
        "Use the appropriate tool for the task. Provide meaningful output."
    ),
)

# Define Agent A: Summarizer
summarizer_agent = Agent(
    model,
    deps_type=SharedContext,
    system_prompt="You are a summarizer. Summarize the following input text concisely."
)

# Define Agent B: Sentiment Analyzer
sentiment_agent = Agent(
    model,
    deps_type=SharedContext,
    system_prompt="You are a sentiment analyzer. Analyze the sentiment of the following input text."
)

# Define tools for the primary agent
@primary_agent.tool
async def summarize_text(ctx: RunContext[SharedContext]) -> str:
    print(f"[DEBUG] Summarizing text: {ctx.deps.text}")  # Debugging
    result = await summarizer_agent.run(ctx.deps.text, deps=ctx.deps)
    ctx.deps.task_result = result.data
    return ctx.deps.task_result

@primary_agent.tool
async def analyze_sentiment(ctx: RunContext[SharedContext]) -> str:
    print(f"[DEBUG] Analyzing sentiment: {ctx.deps.text}")  # Debugging
    result = await sentiment_agent.run(ctx.deps.text, deps=ctx.deps)
    ctx.deps.task_result = result.data
    return ctx.deps.task_result

# Main workflow
async def main():
    shared_context = SharedContext(text="I love basketball and I want to learn it.")
    
    print(f"[DEBUG] Initial shared context: {shared_context}")  # Debugging

    # Primary agent dynamically delegates tasks
    try:
        result = await primary_agent.run("Delegate the task based on the input.", deps=shared_context)
        print(f"Final Result: {result.data}")
    except Exception as e:
        print(f"[ERROR] {e}")

import asyncio
asyncio.run(main())
