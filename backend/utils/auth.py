from fastapi import Request

async def verify_jwt_token(request: Request) -> dict:
    """Mock JWT verification for merged backend."""
    return {"user": "admin", "role": "admin"}

async def verify_api_key(request: Request) -> bool:
    """Mock API key verification for merged backend."""
    return True
