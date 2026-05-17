from __future__ import annotations

import asyncio
import logging
import mimetypes
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

logger = logging.getLogger(__name__)

from backend.api.deps import get_job_store, get_record_store, get_vector_store, get_object_store
from backend.auth.deps import get_current_user, get_current_user_for_file, require_role
from backend.auth.models import UserPublic, UserRole
from backend.core.models import JobResponse, VisibilityRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    job_store=Depends(get_job_store),
):
    all_jobs = await job_store.list_all()
    if current_user.role == UserRole.admin:
        return [JobResponse(**j) for j in all_jobs]
    if current_user.role == UserRole.contributor:
        return [JobResponse(**j) for j in all_jobs if j.get("owner_id") == current_user.user_id]
    # user role has no Files tab
    raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    job_store=Depends(get_job_store),
):
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    # Users can poll job status only if they own it or it's public
    if current_user.role == UserRole.contributor and job.get("owner_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if current_user.role == UserRole.user:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return JobResponse(**job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    job_store=Depends(get_job_store),
    record_store=Depends(get_record_store),
    vector_store=Depends(get_vector_store),
    object_store=Depends(get_object_store),
):
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    if current_user.role == UserRole.user:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if current_user.role == UserRole.contributor and job.get("owner_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's file")

    try:
        # Delete from job_store FIRST — immediately removes this job from
        # allowed_job_ids so its vectors are excluded from all future queries
        # even if the OpenSearch cleanup below fails.
        await job_store.delete(job_id)
        await record_store.delete_by_job(job_id)
        await object_store.delete_prefix(f"raw/{job_id}")
        await object_store.delete_prefix(f"normalized/{job_id}")
    except Exception as exc:
        logger.error("Delete failed for job %s: %s", job_id, exc)
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}")

    # Vector cleanup is best-effort — a failure here never blocks the 204.
    # Residual vectors are harmless: the knn pre-filter in vector_store.search
    # excludes any job_id not in the current allowed set.
    async def _cleanup_vectors() -> None:
        try:
            await vector_store.delete_by_job(job_id)
        except Exception as exc:
            logger.warning("Vector cleanup failed for job %s (residual vectors are query-filtered): %s", job_id, exc)
    asyncio.ensure_future(_cleanup_vectors())

    return Response(status_code=204)


@router.patch("/{job_id}/visibility", response_model=JobResponse)
async def set_visibility(
    job_id: str,
    body: VisibilityRequest,
    _: Annotated[UserPublic, Depends(require_role(UserRole.admin))],
    job_store=Depends(get_job_store),
):
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    await job_store.update(job_id, visibility=body.visibility)
    updated = await job_store.get(job_id)
    return JobResponse(**updated)


@router.get("/{job_id}/file")
async def get_job_file(
    job_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user_for_file)],
    job_store=Depends(get_job_store),
    object_store=Depends(get_object_store),
):
    """Serve the original raw file for a job (image, audio, etc.)."""
    job = await job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")

    # Access check
    if current_user.role == UserRole.user:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if current_user.role == UserRole.contributor and job.get("owner_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Derive the S3 key directly from job metadata — requires only s3:GetObject,
    # not s3:ListBucket (which many IAM roles omit).
    source_ref = job.get("source_ref", "")
    if source_ref.startswith(("http://", "https://")):
        filename = source_ref.split("?")[0].rstrip("/").split("/")[-1] or "file"
    else:
        filename = source_ref or "file"
    raw_key = f"raw/{job_id}/{filename}"

    try:
        data = await object_store.get(raw_key)
    except Exception as primary_exc:
        # Fallback: scan the prefix (requires s3:ListBucket; may also fail)
        try:
            keys = await object_store.list_keys(f"raw/{job_id}")
            raw_keys = [k for k in keys if not k.endswith((".json", ".jsonl"))]
            if not raw_keys and not keys:
                raise HTTPException(status_code=404, detail="No raw file found for this job")
            key = (raw_keys or keys)[0]
            filename = key.split("/")[-1]
            data = await object_store.get(key)
        except HTTPException:
            raise
        except Exception:
            logger.error("Failed to fetch file for job %s: %s", job_id, primary_exc)
            raise HTTPException(status_code=500, detail="File storage error — check S3 permissions")

    mime = mimetypes.guess_type(filename.lower())[0] or "application/octet-stream"

    safe_ascii = filename.encode("ascii", errors="replace").decode("ascii")
    encoded = urllib.parse.quote(filename, safe="")
    disposition = f'inline; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'

    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": disposition},
    )
