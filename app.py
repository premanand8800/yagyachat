import os
import uuid
import json
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from groq import Groq
from dotenv import load_dotenv  # Added for .env file support

# Load environment variables from .env file
load_dotenv()

@dataclass()
class Message:
    content: str
    sender: str
    timestamp: str

@dataclass()
class Session:
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    messages: List[Message]

class SessionManager:
    def __init__(self, storage_path: str = "sessions.json"):
        self.storage_path = storage_path
        self.active_sessions: Dict[str, Session] = {}
        self.load_sessions()

    def load_sessions(self):
        """Load all sessions from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                sessions_data = json.load(f)
                for session_id, data in sessions_data.items():
                    messages = [Message(**msg) for msg in data['messages']]
                    session = Session(
                        session_id=data['session_id'],
                        user_id=data['user_id'],
                        created_at=data['created_at'],
                        last_active=data['last_active'],
                        messages=messages
                    )
                    self.active_sessions[session_id] = session
        except FileNotFoundError:
            self.active_sessions = {}

    def save_sessions(self):
        """Persist all sessions to storage"""
        sessions_dict = {
            session_id: asdict(session)
            for session_id, session in self.active_sessions.items()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(sessions_dict, f, indent=2)

    def create_session(self, user_id: str) -> str:
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_active=now,
            messages=[]
        )
        self.active_sessions[session_id] = session
        self.save_sessions()
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID"""
        return self.active_sessions.get(session_id)

    def add_message(self, session_id: str, content: str, sender: str):
        """Add a message to a session"""
        if session := self.active_sessions.get(session_id):
            now = datetime.datetime.now().isoformat()
            message = Message(
                content=content,
                sender=sender,
                timestamp=now
            )
            session.messages.append(message)
            session.last_active = now
            self.save_sessions()

class ChatbotWithSessions:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chatbot with an optional API key.
        If no API key is provided, it attempts to load from environment variables.
        """
        # Try to get API key from parameter or environment variable
        if api_key is None:
            api_key = os.getenv('GROQ_API_KEY')
        
        # Validate API key
        if not api_key:
            raise ValueError("No Groq API key provided. Set GROQ_API_KEY in .env or pass directly.")
        
        self.client = Groq(api_key=api_key)
        self.session_manager = SessionManager()
    
    def start_session(self, user_id: str) -> str:
        """Start a new chat session"""
        return self.session_manager.create_session(user_id)
    
    def resume_session(self, session_id: str) -> Optional[List[Message]]:
        """Resume an existing session"""
        if session := self.session_manager.get_session(session_id):
            return session.messages
        return None
    
    def chat(self, session_id: str, message: str) -> str:
        """Process a chat message within a session"""
        # Add user message to session
        self.session_manager.add_message(session_id, message, "user")
        
        # Get session history
        session = self.session_manager.get_session(session_id)
        if not session:
            return "Session not found"
        
        # Format conversation history for Groq
        conversation = self._format_history_for_groq(session.messages)
        
        try:
            # Call Groq API with conversation history
            completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=conversation,
                temperature=0.7,
                max_tokens=1024
            )
            
            response = completion.choices[0].message.content
            
            # Save bot response to session
            self.session_manager.add_message(session_id, response, "assistant")
            
            return response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.session_manager.add_message(session_id, error_msg, "assistant")
            return error_msg
    
    def _format_history_for_groq(self, messages: List[Message]) -> List[Dict]:
        """Format message history for Groq API"""
        return [
            {
                "role": msg.sender,
                "content": msg.content
            }
            for msg in messages
        ]

# Example usage
def main():
    # Attempt to create chatbot using environment variable
    try:
        chatbot = ChatbotWithSessions()
        
        print("Chatbot Session Manager")
        print("1. Start new session")
        print("2. Resume existing session")
        choice = input("Choose an option: ")
        
        if choice == "1":
            user_id = input("Enter user ID: ")
            session_id = chatbot.start_session(user_id)
            print(f"New session created: {session_id}")
        else:
            session_id = input("Enter session ID: ")
            history = chatbot.resume_session(session_id)
            if history:
                print("\nChat History:")
                for msg in history:
                    print(f"{msg.sender} ({msg.timestamp}): {msg.content}")
            else:
                print("Session not found")
                return
        
        print("\nChat started (type 'quit' to exit)")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                break
            
            response = chatbot.chat(session_id, user_input)
            print(f"Bot: {response}")
    
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please set your GROQ_API_KEY in a .env file or pass it directly to the constructor.")

if __name__ == "__main__":
    main()