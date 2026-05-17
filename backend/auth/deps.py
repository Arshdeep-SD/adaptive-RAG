from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from backend.auth.jwt import verify_token
from backend.auth.models import UserPublic, UserRole
from backend.auth.store import _local_user_store
from backend.core.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_user_store(settings: Annotated[Settings, Depends(get_settings)]):
    """Return the appropriate user store based on config."""
    if settings.USE_LOCAL_STORE:
        return _local_user_store()
    from backend.db.dynamo import DynamoUserStore  # noqa: F401 — implemented for AWS path
    return DynamoUserStore(
        table_name=settings.USERS_TABLE,
        region=settings.AWS_REGION,
        endpoint_url=settings.DYNAMO_ENDPOINT,
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    user_store=Depends(get_user_store),
) -> UserPublic:
    payload = verify_token(token, settings.JWT_SECRET)
    user_id: str | None = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await user_store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return UserPublic(**user)


async def get_current_user_for_file(
    token_param: Annotated[str | None, Query(alias="token")] = None,
    bearer: Annotated[str | None, Depends(_oauth2_optional)] = None,
    settings: Annotated[Settings, Depends(get_settings)] = ...,
    user_store=Depends(get_user_store),
) -> UserPublic:
    """Like get_current_user but also accepts JWT via ?token= query parameter for media serving."""
    raw = token_param or bearer
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(raw, settings.JWT_SECRET)
    user_id: str | None = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await user_store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return UserPublic(**user)


def require_role(*roles: UserRole):
    """Dependency factory — raises 403 if the current user's role is not in roles."""
    async def _check(
        current_user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> UserPublic:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _check
