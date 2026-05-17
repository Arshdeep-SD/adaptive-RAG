from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt


def create_access_token(data: dict, secret: str, expire_hours: int = 24) -> str:
    payload = dict(data)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
