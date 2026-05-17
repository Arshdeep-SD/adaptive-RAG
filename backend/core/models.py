from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class InputType(str, Enum):
    FILE = "file"
    JSON = "json"
    URL = "url"


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

class IngestJsonRequest(BaseModel):
    data: dict | list
    source_label: str = "paste"


class IngestUrlRequest(BaseModel):
    url: str
    source_label: str | None = None


class IngestResponse(BaseModel):
    job_id: str
    status: JobStatus


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    input_type: str | None = None
    source_ref: str | None = None
    record_count: int = 0
    file_size: int | None = None
    error: str | None = None
    created_at: str | None = None
    owner_id: str | None = None
    visibility: Literal["private", "public"] = "private"


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SourceRef(BaseModel):
    record_id: str
    source_ref: str
    text: str
    score: float
    job_id: str | None = None
    content_type: str | None = None
    chunk_index: int = 0


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    ui_schema: dict[str, Any]
    cache_hit: bool


# ---------------------------------------------------------------------------
# UI Schema
# ---------------------------------------------------------------------------

class UISchemaRequest(BaseModel):
    data: dict | list
    intent: str | None = None


class UISchemaResponse(BaseModel):
    ui_schema: dict[str, Any]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str  # "admin" | "contributor" | "user"


class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    created_at: str


class VisibilityRequest(BaseModel):
    visibility: Literal["private", "public"]


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

class RecordResponse(BaseModel):
    record_id: str
    job_id: str
    source_ref: str
    content_type: str
    text: str
    payload: Any | None = None
    chunk_index: int
    created_at: str
