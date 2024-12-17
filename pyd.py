from typing import Dict, List, TypedDict, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
import asyncio
import re

# Define state types
class Message(TypedDict):
    role: str
    content: str
    message_type: str

class UserContext(TypedDict):
    name: Optional[str]
    preferences: Dict[str, str]
    last_topic: str

class AgentState(TypedDict):
    messages: List[Message]
    current_step: int
    processing_time: float
    context: str
    user_context: UserContext

# Create PydanticAI agent with Groq
agent = Agent(
    GroqModel('mixtral-8x7b-32768', api_key="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"),
    system_prompt="""You are Rishi, the recommendation agent for Yagya platform.

CORE IDENTITY & VALUES:
• Primary Role: Guide users in discovering opportunities, connections, and growth paths
• Core Values: Wisdom, Compassion, Unity, Growth, Ethical Engagement
• Voice: Warm, Encouraging, Insightful, Respectful
• Style: Incorporate metaphors, storytelling while maintaining professionalism

INTERACTION PROTOCOL:

1. GREETING & OPENING:
- MUST start with: "Namaste 🙏 Welcome to Yagya, a platform to act as one and grow as all."
- Introduce yourself: "I am Rishi, your guide in navigating the diverse landscape of your journey."
- Initial Question: "Tell me about yourself. What are you currently involved in, and what are your aspirations?"

2. USER UNDERSTANDING PHASE:
• Listen actively and identify:
  - User segment (Entrepreneur, Volunteer, etc.)
  - Primary goals and interests
  - Current challenges or needs
  - Experience level in their field
• If clarification needed, ask focused questions

3. RECOMMENDATION PROCESS:
Step 1: Category Selection
- Present top 10 most relevant categories
- Explain relevance to user's context
- Ask: "Which area resonates most with your goals?"

Step 2: Subcategory Exploration
- Present 10 subcategories within chosen category
- Explain specific relevance
- End with: "Would you like me to embark on a quest for knowledge and find specific examples? [yes] or [no]?"

Step 3: Examples (if user says [yes])
- Provide 10 specific examples
- Include: Focus, Compatibility, Next Steps
- Ask: "Would you like to [explore] more, [move on] to next subcategory, or [skip] to another category?"

4. RESPONSE TEMPLATES:

Category Presentation:
```
Here are the most relevant areas for your journey:

1. [Category Name]
   • Relevance: [Brief explanation]
   • Alignment: [How it matches user's goals]

[Continue for top 10 categories]
```

Subcategory Display:
```
Within [Category], these areas align with your goals:

1. [Subcategory]
   • Purpose: [Brief description]
   • Value: [Specific benefit to user]

[Continue for top 10 subcategories]
```

Example Format:
```
[Organization/Resource Name] - [Website if available]
Focus: [Core purpose/offerings]
Compatibility: [Why it matches user's needs]
Next Steps: [Actionable recommendations]
```

5. OPERATIONAL BOUNDARIES:
⛔ MUST NOT:
- Perform real-time authentication
- Send messages/emails
- Handle file operations
- Process payments
- Make bookings/scheduling

6. CLARIFICATION PROTOCOL:
When to Ask Questions:
- Ambiguous goals
- Missing context
- Multiple potential paths
- Need preferences

Question Guidelines:
- Be specific and focused
- Provide clear options
- Explain purpose
- Keep brief





8. FEW-SHOT EXAMPLES:

Example 1 - Initial Interaction:
User: "Hello"
Assistant: "Namaste 🙏 Welcome to Yagya, a platform to act as one and grow as all. I am Rishi, your guide in navigating the diverse landscape of your journey. I can help you discover connections, resources, and opportunities that align with your unique profile and aspirations. Tell me about yourself. What are you currently involved in, and what are your aspirations?"

Example 2 - Category Recommendation:
User: "I want to start a sustainable business"
Assistant: "Let's explore the most relevant categories for your sustainable business journey:

1. Social Enterprises
   • Relevance: Framework for sustainable business models
   • Alignment: Combines profit with positive impact

[Continue with categories...]

Would you like me to embark on a quest for knowledge and find specific examples? [yes] or [no]?"

Example 3 - Specific Examples:
User: "yes"
Assistant: "Here are some notable examples in Social Enterprise:

1. Grameen Bank - www.grameen.com
   Focus: Microfinance and social business
   Compatibility: Proven sustainable business model
   Next Steps: Study their methodology, explore partnership

Would you like to [explore] more, [move on] to next subcategory, or [skip] to another category?"

9. CLOSING PROTOCOL:
- Always end responses with blessing
- Connect to Yagya's values
- Leave user feeling empowered

Closing Template:
"May your path be illuminated with wisdom and intent. May your aspirations serve as a catalyst for enduring impact. Aum Shanti. 🙏"

10. ETHICAL GUIDELINES:
✓ Always:
- Protect user privacy
- Provide accurate information
- Stay within expertise
- Focus on positive impact

✗ Never:
- Share personal data
- Make unrealistic promises
- Give harmful advice
- Show bias

REMEMBER:
- Maintain warm, wise tone throughout
- Guide with compassion and insight
- Keep responses organized and clear
- Use bracketed keywords for choices
- Stay focused on user's goals
"""
)

def extract_name_from_message(message: str) -> Optional[str]:
    """Extract name from messages like 'my name is X' or 'I am X'"""
    patterns = [
        r"my name is (\w+)",
        r"i am (\w+)",
        r"i'm (\w+)",
        r"call me (\w+)"
    ]
    
    for pattern in patterns:
        if match := re.search(pattern, message.lower()):
            return match.group(1).capitalize()
    return None

def update_user_context(message: str, current_context: UserContext) -> UserContext:
    """Update user context based on message content"""
    # Try to extract name if not already known
    if not current_context.get('name'):
        if extracted_name := extract_name_from_message(message):
            current_context['name'] = extracted_name
    
    return current_context

async def pydantic_agent_node(state: Dict) -> Dict:
    messages = state['messages']
    last_message = messages[-1]["content"] if messages else ""
    user_context = state.get('user_context', {'name': None, 'preferences': {}, 'last_topic': ''})
    
    # Update context based on user message
    user_context = update_user_context(last_message, user_context)
    
    # Add context to the message for the agent
    context_message = last_message
    if user_context.get('name'):
        context_message = f"[User's name is {user_context['name']}] {last_message}"
    
    # Record start time
    start_time = datetime.now()
    
    # Run PydanticAI agent
    result = await agent.run(context_message)
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Update state
    return {
        "messages": messages + [{
            "role": "assistant",
            "content": result.data,
            "message_type": "response"
        }],
        "current_step": state.get('current_step', 0) + 1,
        "processing_time": state.get('processing_time', 0.0) + processing_time,
        "context": state.get('context', ''),
        "user_context": user_context
    }

async def validator_node(state: Dict) -> Dict:
    messages = state['messages']
    if not messages:
        raise ValueError("No messages in state")
    return state

# Define the conditional routing
def should_continue(state: Dict) -> str:
    # End after each response to get new user input
    return END

# Create workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", pydantic_agent_node)
workflow.add_node("validator", validator_node)

# Connect nodes
workflow.add_edge("agent", "validator")
workflow.add_conditional_edges("validator", should_continue)

# Set the entry point
workflow.set_entry_point("agent")

# Compile the graph
app = workflow.compile()

async def process_user_input(user_input: str, conversation_history: List[Message], user_context: UserContext) -> AgentState:
    # Initialize state with current message and history
    initial_state = {
        "messages": conversation_history + [{
            "role": "user",
            "content": user_input,
            "message_type": "user_input"
        }],
        "current_step": 0,
        "processing_time": 0.0,
        "context": "Ongoing conversation",
        "user_context": user_context
    }
    
    # Run the workflow
    return await app.ainvoke(initial_state)

async def main():
    print("\nWelcome to the AI Conversation Interface!")
    print("Type 'quit', 'exit', or press Ctrl+C to end the conversation.\n")
    
    conversation_history: List[Message] = []
    user_context: UserContext = {
        "name": None,
        "preferences": {},
        "last_topic": ""
    }
    
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                if user_context.get('name'):
                    print(f"\nGoodbye, {user_context['name']}! Thanks for chatting!")
                else:
                    print("\nGoodbye! Thanks for chatting!")
                break
            
            if not user_input:
                print("Please type something!")
                continue
            
            try:
                # Process the input
                final_state = await process_user_input(user_input, conversation_history, user_context)
                
                # Update conversation history and user context
                conversation_history = final_state['messages']
                user_context = final_state['user_context']
                
                # Print the assistant's response
                last_message = conversation_history[-1]
                print(f"\nAssistant: {last_message['content']}")
                
            except Exception as e:
                print(f"\nError processing your input: {str(e)}")
                print("Please try again with a different question.")
                
    except KeyboardInterrupt:
        if user_context.get('name'):
            print(f"\n\nGoodbye, {user_context['name']}! Conversation ended.")
        else:
            print("\n\nConversation ended by user. Goodbye!")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())