from nemoguardrails import LLMRails, RailsConfig

def create_nemo_config() -> RailsConfig:
    """
    Creates and returns NeMo Guardrails configuration
    Returns:
        RailsConfig object with appropriate settings
    """
    config = {
        "models": {
            "main": {
                "engine": "langchain",
                "model": "langchain_groq.ChatGroq",
                "model_kwargs": {
                    "model_name": "mixtral-8x7b-32768",
                    "temperature": 0.3
                }
            }
        },
        "rails": {
            "input": [
                {
                    "name": "block_harmful_content",
                    "description": "Block harmful or inappropriate content"
                }
            ],
            "output": [
                {
                    "name": "ensure_safe_response",
                    "description": "Ensure responses are safe and appropriate"
                }
            ]
        }
    }
    
    return RailsConfig.from_content(config)
