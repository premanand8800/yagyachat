from typing import Sequence, Annotated, Dict, List, Optional, Type
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import json
import os
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import tool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Initialize environment variables
os.environ["LANGCHAIN_PROJECT"] = "Chatbot_testing"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "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"

memory = MemorySaver()

# Define System Instructions
SYSTEM_INSTRUCTION = """You are Rishi, the recommendation agent for Yagya platform.

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

TOOL USAGE GUIDELINES:

🔍 Search Tool Usage:
- When specific, factual examples or up-to-date information is needed
- If you require current organizational or resource details
- When verifying recent developments in a field
- To provide concrete, real-world examples for user's context

WHEN TO USE SEARCH TOOL:
1. During Example Generation
- If no pre-existing example fits perfectly
- When needing recent, specific instances
- To validate or expand current knowledge

2. Example Scenarios for Tool Usage:
- Finding recent social enterprises
- Identifying current opportunities in a specific domain
- Verifying latest developments in an organization
- Gathering concrete examples for subcategories

3. SEARCH PROTOCOL:
- Use focused, precise search queries
- Prioritize relevance to user's specific context
- Select most recent and impactful results
- Always cite source of information

4. TOOL USAGE INSTRUCTION:
- If you determine a search would provide valuable context
- Use search_organizations tool with clear, specific query
- Integrate search results seamlessly into response
- Explain why the search was necessary




🔬 RESEARCH ARTICLE RETRIEVAL GUIDELINES

arix_tool TOOL USAGE:

PURPOSE:
- Retrieve scholarly articles for academic and research-based queries
- Provide up-to-date scientific information
- Support evidence-based recommendations

TOOL CAPABILITIES:
✓ Retrieve scientific articles from ArXiv
✓ Access key article details:
  - Publishing Date
  - Title
  - Authors
  - Summary

WHEN TO USE ARXIV TOOL:
1. User requires academic or scientific information
2. Need for latest research in a specific domain
3. Seeking scholarly context for recommendations
4. Verifying scientific claims or developments

QUERY GUIDELINES:
- Craft precise, focused queries
- Limit query to 300 characters
- Use academic and technical terminology
- Target specific research domains or topics

EXAMPLE USAGE SCENARIOS:
1. Technology Trends
2. Scientific Innovations
3. Academic Research Insights
4. Emerging Field Explorations

TOOL USAGE PROTOCOL:
1. Identify need for scholarly research
2. Formulate precise 300-character query
3. Use ArxivAPIWrapper to retrieve articles
4. Synthesize and contextualize results
5. Present findings with academic rigor

PRESENTATION FORMAT:
🔍 Research Insights: [Topic]
Article Details:

Title: [Article Title]
Authors: [Author Names]
Publication Date: [Date]
Key Findings: [Concise Summary]

Relevance to User:

[Direct connection to user's context]
[Potential applications]
[Learning opportunities]

Actionable Insights:

[Recommendation 1]
[Recommendation 2]


🌐 WEB SCRAPER TOOL GUIDELINES

PURPOSE:
- Extract information from websites
- Gather current, real-time information
- Support research and recommendation processes

TOOL CAPABILITIES:
✓ Scrape entire webpage content
✓ Extract specific elements using CSS selectors
✓ Handle various website structures

WHEN TO USE WEB SCRAPER:
1. Need current information not in existing knowledge
2. Verify recent developments
3. Gather specific details from websites
4. Support recommendation with live data

USAGE PROTOCOLS:
- Use only reputable, public websites
- Respect website terms of service
- Avoid personal or sensitive information sites
- Prioritize ethical information gathering

QUERY CONSTRUCTION:
- Provide full, valid URL
- Optional: Use precise CSS selectors
- Focus on informational, public sources

EXAMPLE USAGE:

Web Scraping Request:

URL: [Full website URL]
Selector (optional): [CSS selector]

Extracted Information Presentation:

Source Verification
Key Insights
Relevance to User Context

<DO DONT MENTION THE USER WHAT TOOLS YOU HAVE YOU NEED TO STAY GROUND PROVIDE THE INFORMATION WHILE USING TOOLS BUT DO NOT MENTION THE USER YOU HAVE USE THIS TOOLS AND THAT BE GROUNDED/>
<WHEN USER START WITH HI , HELLO OR GREETING MESSAGE THEN ONLY GREET USER WITH --><1. GREETING & OPENING:
- MUST start with: "Namaste 🙏 Welcome to Yagya, a platform to act as one and grow as all."
- Introduce yourself: "I am Rishi, your guide in navigating the diverse landscape of your journey."
- Initial Question: "Tell me about yourself. What are you currently involved in, and what are your aspirations?"><INSISIT USER TO TELL ABOUT THEMSELVES ONLY THEN EXPLORE RECOMMANDATION>



"""
# Chat Session Management Classes
class ChatSession:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid4())
        self.start_time = datetime.now().isoformat()
        self.messages = []
        self.metadata = {
            "user_context": {},
            "preferences": {},
            "last_active": self.start_time
        }

class ChatHistory:
    def __init__(self, storage_dir: str = "chat_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.sessions: Dict[str, ChatSession] = {}
        self.load_sessions()

    def create_session(self) -> str:
        session = ChatSession()
        self.sessions[session.session_id] = session
        self.save_session(session.session_id)
        return session.session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        if session_id not in self.sessions:
            self._load_session(session_id)
        return self.sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session.messages.append(message)
        session.metadata["last_active"] = datetime.now().isoformat()
        self.save_session(session_id)
        return True

    def update_user_context(self, session_id: str, context: dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.metadata["user_context"].update(context)
        self.save_session(session_id)
        return True

    def get_chat_history(self, session_id: str, limit: Optional[int] = None) -> List[dict]:
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        return messages

    def save_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if not session:
            return

        session_data = {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "messages": session.messages,
            "metadata": session.metadata
        }

        file_path = self.storage_dir / f"{session_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

    def _load_session(self, session_id: str) -> Optional[ChatSession]:
        file_path = self.storage_dir / f"{session_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = ChatSession(session_id)
            session.start_time = data["start_time"]
            session.messages = data["messages"]
            session.metadata = data["metadata"]
            self.sessions[session_id] = session
            return session
        except Exception as e:
            print(f"Error loading session {session_id}: {str(e)}")
            return None

    def load_sessions(self):
        for file_path in self.storage_dir.glob("*.json"):
            session_id = file_path.stem
            self._load_session(session_id)

# Modified State Definition
class RishiState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    chat_history: ChatHistory

# Tools Definition
class WebScraperInput(BaseModel):
    url: str = Field(description="The full URL to scrape")
    selector: Optional[str] = Field(
        default=None, 
        description="Optional CSS selector to extract specific content"
    )

class WebScraperTool(BaseTool):
    name: str = "web_scraper"
    description: str = "Scrape content from a given website"
    args_schema: Type[BaseModel] = WebScraperInput

    def _run(self, url: str, selector: Optional[str] = None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if selector:
                elements = soup.select(selector)
                content = [elem.get_text(strip=True) for elem in elements]
                return "\n".join(content) if content else "No content found with the given selector"
            
            return soup.get_text(separator='\n', strip=True)[:2000]
        
        except requests.RequestException as e:
            return f"Error scraping {url}: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

@tool
def arxiv_search(query: str) -> str:
    """Search for scientific articles on ArXiv."""
    arxiv = ArxivAPIWrapper()
    try:
        query = query[:300]
        results = arxiv.run(query)
        return results
    except Exception as e:
        return f"Error in ArXiv search: {str(e)}"

def create_rishi_bot():
    # Initialize tools
    search_tool = TavilySearchResults(max_results=2)
    web_scraper_tool = WebScraperTool()
    tools = [search_tool, arxiv_search, web_scraper_tool]

    # Initialize Groq model with tools
    model = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="mixtral-8x7b-32768"
    ).bind_tools(tools)
    
    # Create prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_INSTRUCTION),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # Initialize chat history
    chat_history = ChatHistory()
    
    # Create workflow
    workflow = StateGraph(state_schema=RishiState)
    
    def call_model(state: RishiState):
        # Get recent chat history
        session = state["chat_history"].get_session(state["session_id"])
        if session:
            session.metadata["last_active"] = datetime.now().isoformat()
            state["chat_history"].save_session(state["session_id"])

        prompt_value = prompt_template.invoke(state)
        response = model.invoke(prompt_value)
        
        # Save the interaction
        if session:
            state["chat_history"].add_message(
                state["session_id"],
                "user",
                prompt_value.messages[-1].content
            )
            state["chat_history"].add_message(
                state["session_id"],
                "assistant",
                response.content
            )
        
        return {"messages": [response]}
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    # Add nodes
    workflow.add_node("model", call_model)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.add_edge(START, "model")
    workflow.add_conditional_edges(
        "model",
        tools_condition,
    )
    workflow.add_edge("tools", "model")
    
    return workflow.compile(checkpointer=memory)

def main():
    print("\n" + "="*50)
    print("Welcome to Rishi - Your Wise Guide on Yagya")
    print("="*50)
    print("\nType 'exit' to end the conversation")
    print("-" * 50)
    
    try:
        # Initialize bot and chat history
        rishi_bot = create_rishi_bot()
        chat_history = ChatHistory()
        
        # Create new session
        session_id = chat_history.create_session()
        config = {"configurable": {"thread_id": session_id}}
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nMay your path be illuminated with wisdom and intent. "
                          "May your aspirations serve as a catalyst for enduring impact. "
                          "Aum Shanti. 🙏")
                    break
                
                messages = [HumanMessage(content=user_input)]
                
                print("\nRishi: ", end="", flush=True)
                for chunk, metadata in rishi_bot.stream(
                    {
                        "messages": messages,
                        "session_id": session_id,
                        "chat_history": chat_history
                    },
                    config,
                    stream_mode="messages"
                ):
                    if isinstance(chunk, AIMessage):
                        print(chunk.content, end="", flush=True)
                print()
                
            except KeyboardInterrupt:
                print("\n\nConversation ended by user. Aum Shanti. 🙏")
                break
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                print("Please try again.")
    
    except Exception as e:
        print(f"\nFailed to initialize Rishi: {str(e)}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()