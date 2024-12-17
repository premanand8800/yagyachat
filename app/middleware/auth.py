import os
import jwt
import logging
from fastapi import Request, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

def auth_middleware(req: Request):
    """Authentication middleware for validating JWT tokens"""
    auth_header = req.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logging.warning("Authorization header missing or invalid")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized: Token missing"
        )

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token, 
            os.getenv("JWT_SECRET"), 
            algorithms=["HS256"]
        )
        req.state.user = payload
        logging.info(f"Authenticated user: {payload['user_id']}")
    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized: Token has expired"
        )
    except jwt.InvalidTokenError:
        logging.warning("Invalid token")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized: Invalid token"
        )
