from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from backend.api.deps import get_job_store, get_object_store, get_record_store, get_vector_store
from backend.auth.deps import get_current_user, get_user_store, require_role
from backend.auth.jwt import create_access_token
from backend.auth.models import UserPublic, UserRole
from backend.core.config import Settings, get_settings
from backend.core.models import CreateUserRequest, TokenResponse, UserResponse
from backend.db.local_store import _now_iso

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
    user_store=Depends(get_user_store),
) -> TokenResponse:
    user = await user_store.get_by_username(form_data.username)
    if not user or not _pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user["username"], "user_id": user["user_id"], "role": user["role"]},
        secret=settings.JWT_SECRET,
        expire_hours=settings.JWT_EXPIRE_HOURS,
    )
    return TokenResponse(access_token=token)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: Annotated[UserPublic, Depends(require_role(UserRole.admin))],
    user_store=Depends(get_user_store),
) -> list[UserResponse]:
    users = await user_store.list_all()
    return [UserResponse(**u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: CreateUserRequest,
    _: Annotated[UserPublic, Depends(require_role(UserRole.admin))],
    user_store=Depends(get_user_store),
) -> UserResponse:
    if body.role not in ("admin", "contributor", "user"):
        raise HTTPException(status_code=400, detail="Invalid role")
    try:
        user = {
            "user_id": str(uuid.uuid4()),
            "username": body.username,
            "hashed_password": _pwd_context.hash(body.password),
            "role": body.role,
            "created_at": _now_iso(),
        }
        await user_store.create(user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return UserResponse(**user)


@router.delete("/users/{user_id}", status_code=204, response_class=Response)
async def delete_user(
    user_id: str,
    current_user: Annotated[UserPublic, Depends(require_role(UserRole.admin))],
    user_store=Depends(get_user_store),
    job_store=Depends(get_job_store),
    record_store=Depends(get_record_store),
    vector_store=Depends(get_vector_store),
    object_store=Depends(get_object_store),
) -> Response:
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await user_store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cascade: delete all jobs/records/files owned by this user.
    # Delete from job_store first so queries immediately stop including these jobs
    # in allowed_job_ids — even if vector cleanup fails later.
    all_jobs = await job_store.list_all()
    owned = [j["job_id"] for j in all_jobs if j.get("owner_id") == user_id]
    for jid in owned:
        try:
            await job_store.delete(jid)
            await record_store.delete_by_job(jid)
            await object_store.delete_prefix(f"raw/{jid}")
            await object_store.delete_prefix(f"normalized/{jid}")
        except Exception as exc:
            logger.warning("Cascade delete failed for job %s: %s", jid, exc)

        async def _cleanup_vectors(job_id: str = jid) -> None:
            try:
                await vector_store.delete_by_job(job_id)
            except Exception as exc:
                logger.warning("Vector cleanup failed for job %s: %s", job_id, exc)
        asyncio.ensure_future(_cleanup_vectors())

    await user_store.delete(user_id)
    return Response(status_code=204)
