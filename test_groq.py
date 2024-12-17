import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from dataclasses import dataclass
from datetime import datetime

# Load environment variables
load_dotenv()

@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str]

def tavily_search(
    query: str,
    search_type: str = "comprehensive",
    max_results: int = 5,
    include_images: bool = False,
    include_answer: bool = True,
    search_depth: str = "advanced"
) -> Dict[str, Any]:
    """
    Advanced search function using Tavily API
    Args:
        query: Search query string
        search_type: Type of search ('comprehensive' or 'quick')
        max_results: Maximum number of results to return
        include_images: Whether to include image results
        include_answer: Whether to include AI-generated answer
        search_depth: Depth of search ('basic' or 'advanced')
    Returns:
        Dictionary containing search results and metadata
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is not set")

    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_images": include_images,
        "include_answer": include_answer,
        "search_type": search_type
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # Process and structure the results
        processed_results = {
            "query": query,
            "search_metadata": {
                "total_results": len(result.get("results", [])),
                "search_type": search_type,
                "search_depth": search_depth,
                "timestamp": datetime.now().isoformat()
            },
            "answer": result.get("answer", ""),
            "results": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date", "")
                }
                for item in result.get("results", [])
            ]
        }

        return processed_results

    except requests.exceptions.RequestException as e:
        return {
            "error": f"Search request failed: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }

def get_weather(location: str) -> Dict[str, Any]:
    """
    Dummy weather function that returns mock weather data
    Args:
        location: Name of the city
    Returns:
        Dictionary containing weather information
    """
    # Mock weather data
    weather_data = {
        "location": location,
        "temperature": 22,
        "condition": "sunny",
        "humidity": 65,
        "wind_speed": 10
    }
    return weather_data

def main():
    # Your Groq API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    # Define the search function schema
    search_function = {
        "name": "tavily_search",
        "description": "Perform an advanced web search using Tavily API",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["comprehensive", "quick"],
                    "description": "Type of search to perform"
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum number of results to return"
                },
                "include_images": {
                    "type": "boolean",
                    "description": "Whether to include image results"
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "Whether to include AI-generated answer"
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Depth of search to perform"
                }
            },
            "required": ["query"]
        }
    }

    # Define the weather function schema
    weather_function = {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city name to get weather for"
                }
            },
            "required": ["location"]
        }
    }

    # API endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"

    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Message payload
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that can perform advanced web searches and check weather information. When searching, consider using different search types and parameters based on the user's needs."
            },
            {
                "role": "user",
                "content": "Search for recent developments in quantum computing and summarize the key findings."
            }
        ],
        "functions": [search_function, weather_function],
        "function_call": {"name": "tavily_search"}
    }

    try:
        # Make the API call
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Extract function call details
        function_call = result['choices'][0]['message'].get('function_call')
        
        if function_call:
            # Parse the function arguments
            args = json.loads(function_call['arguments'])
            
            # Call the actual function
            if function_call['name'] == 'tavily_search':
                search_result = tavily_search(**args)
            elif function_call['name'] == 'get_weather':
                search_result = get_weather(**args)
            
            # Print results
            print("\nFunction Call Details:")
            print("=" * 50)
            print(f"Function: {function_call['name']}")
            print(f"Arguments: {json.dumps(args, indent=2)}")
            print("\nResults:")
            print("=" * 50)
            print(json.dumps(search_result, indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
