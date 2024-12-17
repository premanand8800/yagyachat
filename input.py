from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from pydantic_ai import Agent, RunContext

# 1. Input Analysis Models
class InputAnalysis(BaseModel):
    """Analysis results of user input"""
    user_summary: Dict[str, str] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    needs_assessment: Dict[str, List[str]] = Field(default_factory=dict)
    segment_understanding: Dict[str, str] = Field(default_factory=dict)
    context_synthesis: Dict[str, List[str]] = Field(default_factory=dict)

class InputState(BaseModel):
    """State for input processing"""
    raw_input: str
    char_count: int
    is_processed: bool = False
    analysis: Optional[InputAnalysis] = None
    processing_status: str = "pending"
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None

# 2. Input Analysis Node
async def input_analysis_node(state: Dict) -> Dict:
    """
    Input Processing Node that:
    1. Receives raw user input
    2. Handles rewrite and enhance requests
    3. Processes text using LLM
    4. Performs internal analysis
    """
    try:
        # Extract input from state
        raw_input = state.get('raw_input', '')
        
        # Validate input length
        if len(raw_input) > 500:
            raise ValueError("Input exceeds 500 character limit")

        # Initialize analysis components
        analysis = await analyze_input(raw_input)
        
        # Update state with analysis results
        return {
            **state,
            'input': {
                'raw_input': raw_input,
                'char_count': len(raw_input),
                'is_processed': True,
                'analysis': analysis.dict(),
                'processing_status': 'completed',
                'timestamp': datetime.now(),
            }
        }

    except Exception as e:
        # Update state with error
        return {
            **state,
            'input': {
                'raw_input': raw_input,
                'char_count': len(raw_input),
                'is_processed': False,
                'processing_status': 'failed',
                'error_message': str(e),
                'timestamp': datetime.now(),
            }
        }

async def analyze_input(input_text: str) -> InputAnalysis:
    """
    Performs comprehensive analysis of user input:
    1. User Summary
    2. Keywords Analysis
    3. Needs Assessment
    4. Segment Understanding
    5. Context Synthesis
    """
    # Create analysis agent
    agent = Agent(
        'groq:mixtral-8x7b-32768',
        system_prompt="""You are an input analysis expert. Analyze the user input for:
        1. User background and expertise level
        2. Key domain terms and technical language
        3. Explicit and implicit needs
        4. Professional category and experience level
        5. Opportunity alignment and potential pathways
        
        Provide structured analysis with clear categorization."""
    )

    # Run analysis
    result = await agent.run(f"""
    Please analyze this user input:
    "{input_text}"
    
    Provide analysis in the following format:
    1. User Summary: background, expertise, goals
    2. Keywords: domain terms, technical terms, skill indicators
    3. Needs Assessment: explicit needs, implicit needs, resource requirements
    4. Segment Understanding: professional category, experience level
    5. Context Synthesis: opportunity alignment, potential pathways
    """)

    # Process and structure the analysis
    analysis_text = result.data
    
    # Parse agent's response into structured format
    structured_analysis = parse_analysis_response(analysis_text)
    
    return InputAnalysis(
        user_summary=structured_analysis.get('user_summary', {}),
        keywords=structured_analysis.get('keywords', []),
        needs_assessment=structured_analysis.get('needs_assessment', {}),
        segment_understanding=structured_analysis.get('segment_understanding', {}),
        context_synthesis=structured_analysis.get('context_synthesis', {})
    )

def parse_analysis_response(analysis_text: str) -> Dict:
    """Parse the LLM response into structured format"""
    # Initialize sections
    sections = {
        'user_summary': {},
        'keywords': [],
        'needs_assessment': {},
        'segment_understanding': {},
        'context_synthesis': {}
    }
    
    # Simple parsing logic (can be enhanced for more robust parsing)
    current_section = None
    for line in analysis_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Detect sections
        if line.startswith('1. User Summary'):
            current_section = 'user_summary'
        elif line.startswith('2. Keywords'):
            current_section = 'keywords'
        elif line.startswith('3. Needs Assessment'):
            current_section = 'needs_assessment'
        elif line.startswith('4. Segment Understanding'):
            current_section = 'segment_understanding'
        elif line.startswith('5. Context Synthesis'):
            current_section = 'context_synthesis'
        # Process content based on section
        elif current_section and ':' in line:
            key, value = line.split(':', 1)
            if current_section == 'keywords':
                sections[current_section].extend([k.strip() for k in value.split(',')])
            else:
                sections[current_section][key.strip()] = value.strip()

    return sections

# Example usage
async def test_input_analysis():
    # Initial state
    initial_state = {
        'raw_input': "I'm a software developer with 5 years experience looking to transition into AI and machine learning. I have basic Python knowledge and want to focus on practical applications.",
        'current_step': 'input_analysis'
    }
    
    # Run input analysis
    result_state = await input_analysis_node(initial_state)
    
    # Print results
    print("\nInput Analysis Results:")
    print("=" * 50)
    if result_state['input']['is_processed']:
        analysis = result_state['input']['analysis']
        print(f"User Summary: {analysis['user_summary']}")
        print(f"Keywords: {analysis['keywords']}")
        print(f"Needs Assessment: {analysis['needs_assessment']}")
        print(f"Processing Status: {result_state['input']['processing_status']}")
    else:
        print(f"Error: {result_state['input']['error_message']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_input_analysis())