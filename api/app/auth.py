from fastapi import Header, HTTPException, status

from app.config import settings


async def require_token(authorization: str = Header(default="")) -> None:
    """Single-user bearer-token auth. Designed to slot in proper auth later."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
