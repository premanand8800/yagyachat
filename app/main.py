from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.middleware.auth import auth_middleware
from app.middleware.rate_limit import limiter, rate_limit_handler
from app.nodes.validation import create_validation_workflow
from app.models.graph_state import GraphState
from app.models.user_input import UserInput
from app.models.validation_result import ValidationResult
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize FastAPI app
app = FastAPI(title="Rishi API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

@app.post("/api/process_input")
@limiter.limit("5/minute")
async def process_input(request: Request, input_text: str):
    """
    Process user input through the validation node
    """
    # Authenticate user
    auth_middleware(request)
    
    try:
        # Create initial state
        initial_state = GraphState(
            user_input=UserInput(raw_input=input_text),
            validation_result=ValidationResult(),
            messages=[],
            next_step="",
            token=request.headers.get("Authorization")
        )
        
        # Create and run validation node
        validation_node = create_validation_workflow()
        final_state = await validation_node.ainvoke(initial_state)
        
        return JSONResponse({
            'is_valid': final_state['validation_result'].is_valid,
            'next_step': final_state['next_step'],
            'messages': final_state['messages'],
            'validation_result': final_state['validation_result'].dict()
        })
        
    except Exception as e:
        logging.error(f"Error processing input: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Rishi API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
