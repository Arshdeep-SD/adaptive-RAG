from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import (
    get_embedding_provider,
    get_job_store,
    get_record_store,
    get_ui_cache_store,
    get_vector_store,
)
from backend.auth.deps import get_current_user
from backend.auth.models import UserPublic, UserRole
from backend.core.config import Settings, get_settings
from backend.core.models import QueryRequest, QueryResponse, SourceRef

router = APIRouter(prefix="/query", tags=["query"])


async def _compute_allowed_job_ids(
    current_user: UserPublic,
    job_store,
) -> set[str]:
    """
    Return the set of job IDs this user may retrieve from.
    Admin gets all existing job IDs (not None) so that records from deleted jobs
    are filtered out — otherwise orphaned vector chunks pollute every query.
    """
    all_jobs = await job_store.list_all()
    if current_user.role == UserRole.admin:
        return {j["job_id"] for j in all_jobs}
    if current_user.role == UserRole.contributor:
        return {
            j["job_id"] for j in all_jobs
            if j.get("owner_id") == current_user.user_id or j.get("visibility") == "public"
        }
    # user role: public only
    return {j["job_id"] for j in all_jobs if j.get("visibility") == "public"}


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    vector_store=Depends(get_vector_store),
    record_store=Depends(get_record_store),
    job_store=Depends(get_job_store),
    ui_cache_store=Depends(get_ui_cache_store),
    embedding_provider=Depends(get_embedding_provider),
):
    from backend.rag.retriever import hybrid_retrieve
    from backend.rag.generator import generate_answer
    from backend.rag.ui_generator import generate_ui_schema

    # Compute which jobs this user is allowed to retrieve from
    allowed_job_ids = await _compute_allowed_job_ids(current_user, job_store)

    # 1. Retrieve relevant chunks (filtered by ownership/visibility)
    sources = await hybrid_retrieve(
        query=request.query,
        top_k=request.top_k,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        record_store=record_store,
        allowed_job_ids=allowed_job_ids,
    )

    # 2. Generate answer
    answer = await generate_answer(
        query=request.query,
        sources=sources,
        settings=settings,
    )

    # 3. Generate / retrieve cached UI schema
    ui_schema, cache_hit = await generate_ui_schema(
        query=request.query,
        answer=answer,
        sources=sources,
        ui_cache_store=ui_cache_store,
        settings=settings,
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        ui_schema=ui_schema,
        cache_hit=cache_hit,
    )
