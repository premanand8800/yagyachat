from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class AnalysisSummary(BaseModel):
    background: str = Field(description="User's professional/personal background")
    expertise_level: str = Field(description="User's level of expertise/experience")
    goals: List[str] = Field(description="List of user's goals")
    key_interests: List[str] = Field(description="List of user's key interests")

class InputAnalysisOutput(BaseModel):
    analysis_summary: AnalysisSummary
    clarity_status: str = Field(description="Status of input clarity: clear|needs_clarification|ambiguous")
    next_action: str = Field(description="Next action to take: generate_categories|ask_questions")
    clarifying_questions: List[str] = Field(description="List of clarifying questions if needed")
    confidence_score: int = Field(description="Confidence score from 0-100")

class InputAnalysisNode:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="mixtral-8x7b-32768"
        )
        self.parser = PydanticOutputParser(pydantic_object=InputAnalysisOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an Input Analysis Node responsible for analyzing user input and determining next steps.
            
            Your task is to:
            1. Analyze the user's message
            2. Extract key information about their background, expertise, goals, and interests
            3. Determine if the input is clear enough to proceed
            4. Generate clarifying questions if needed
            
            Analyze the input thoroughly considering:
            - Professional/personal background
            - Level of expertise/experience
            - Current situation/challenges
            - Vision and aspirations
            - Underlying motivations
            - Domain keywords
            - Technical terms
            - Skill indicators
            
            Format your response according to the following schema:
            {format_instructions}
            """),
            ("human", "{input}")
        ])

    def analyze(self, user_input: str, conversation_history: Optional[List[Dict]] = None) -> InputAnalysisOutput:
        formatted_prompt = self.prompt.format_messages(
            input=user_input,
            format_instructions=self.parser.get_format_instructions()
        )
        
        # Get response from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse the response into our Pydantic model
        try:
            parsed_response = self.parser.parse(response.content)
            return parsed_response
        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {str(e)}")

def create_input_analysis_graph():
    graph = Graph()
    
    @graph.node
    def input_analysis(user_input: str) -> Dict:
        node = InputAnalysisNode()
        result = node.analyze(user_input)
        return result.model_dump()
    
    return graph

if __name__ == "__main__":
    # Example usage
    graph = create_input_analysis_graph()
    
    # Test input
    test_input = "I'm a software developer with 5 years of experience, primarily working with Python. I want to learn machine learning to build AI applications, but I'm not sure where to start."
    
    # Run the graph
    result = graph.run({"user_input": test_input})
    print(result)
