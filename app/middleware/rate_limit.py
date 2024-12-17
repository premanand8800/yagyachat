from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler for rate limit exceeded exceptions"""
    return JSONResponse(
        {
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Please try again in {exc.retry_after} seconds."
        },
        status_code=429
    )
