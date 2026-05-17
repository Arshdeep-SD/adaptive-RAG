from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    admin = "admin"
    contributor = "contributor"
    user = "user"


class UserInDB(BaseModel):
    user_id: str
    username: str
    hashed_password: str
    role: UserRole
    created_at: str


class UserPublic(BaseModel):
    user_id: str
    username: str
    role: UserRole
    created_at: str
