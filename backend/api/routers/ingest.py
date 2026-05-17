from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from backend.api.deps import get_embedding_provider, get_job_store, get_object_store, get_record_store, get_vector_store
from backend.auth.deps import get_current_user, require_role
from backend.auth.models import UserPublic, UserRole
from backend.core.config import Settings, get_settings
from backend.core.models import IngestJsonRequest, IngestResponse, IngestUrlRequest, JobStatus

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run_ingest_worker(job_id: str, deps_kwargs: dict) -> None:
    """Run ingest pipeline as a background task (mirrors S3 event trigger in AWS)."""
    from backend.pipeline.ingest_worker import process_job
    await process_job(job_id, **deps_kwargs)


@router.post("", response_model=IngestResponse, status_code=202)
async def ingest_file(
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[UserPublic, Depends(require_role(UserRole.admin, UserRole.contributor))],
    job_store=Depends(get_job_store),
    object_store=Depends(get_object_store),
    record_store=Depends(get_record_store),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider),
    file: UploadFile | None = File(default=None),
):
    if file is None:
        raise HTTPException(status_code=400, detail="No file provided.")

    job_id = str(uuid.uuid4())
    filename = file.filename or "upload.bin"
    raw_key = f"raw/{job_id}/{filename}"

    data = await file.read()
    try:
        await object_store.put(raw_key, data)
        job = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "input_type": "file",
            "source_ref": filename,
            "file_size": len(data),
            "record_count": 0,
            "created_at": _now_iso(),
            "owner_id": current_user.user_id,
            "visibility": "private",
        }
        await job_store.create(job)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}")

    background_tasks.add_task(
        _run_ingest_worker,
        job_id,
        {
            "job_store": job_store,
            "object_store": object_store,
            "record_store": record_store,
            "vector_store": vector_store,
            "embedding_provider": embedding_provider,
            "filename": filename,
            "raw_key": raw_key,
        },
    )
    return IngestResponse(job_id=job_id, status=JobStatus.PENDING)


@router.post("/json", response_model=IngestResponse, status_code=202)
async def ingest_json(
    request: IngestJsonRequest,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[UserPublic, Depends(require_role(UserRole.admin, UserRole.contributor))],
    job_store=Depends(get_job_store),
    object_store=Depends(get_object_store),
    record_store=Depends(get_record_store),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider),
):
    import json as _json

    job_id = str(uuid.uuid4())
    filename = f"{request.source_label}.json"
    raw_key = f"raw/{job_id}/{filename}"

    data = _json.dumps(request.data).encode()
    try:
        await object_store.put(raw_key, data)
        job = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "input_type": "json",
            "source_ref": request.source_label,
            "file_size": len(data),
            "record_count": 0,
            "created_at": _now_iso(),
            "owner_id": current_user.user_id,
            "visibility": "private",
        }
        await job_store.create(job)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}")

    background_tasks.add_task(
        _run_ingest_worker,
        job_id,
        {
            "job_store": job_store,
            "object_store": object_store,
            "record_store": record_store,
            "vector_store": vector_store,
            "embedding_provider": embedding_provider,
            "filename": filename,
            "raw_key": raw_key,
        },
    )
    return IngestResponse(job_id=job_id, status=JobStatus.PENDING)


@router.post("/url", response_model=IngestResponse, status_code=202)
async def ingest_url(
    request: IngestUrlRequest,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[UserPublic, Depends(require_role(UserRole.admin, UserRole.contributor))],
    job_store=Depends(get_job_store),
    object_store=Depends(get_object_store),
    record_store=Depends(get_record_store),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider),
):
    import httpx

    url_path = request.url.split("?")[0].rstrip("/")
    url_filename = url_path.split("/")[-1] or "url-fetch"
    if "." not in url_filename:
        url_filename = f"{url_filename}.txt"
    label = request.source_label or url_filename
    filename = url_filename
    raw_key = f"raw/{uuid.uuid4()}/{filename}"

    job_id = str(uuid.uuid4())

    headers = {"User-Agent": "Mozilla/5.0 (compatible; AdaptiveRAG/1.0)"}
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(request.url, headers=headers)
            resp.raise_for_status()
            data = resp.content
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=f"Remote server returned {e.response.status_code}")
        except httpx.ConnectError:
            raise HTTPException(status_code=400, detail=f"Could not connect to {request.url}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=400, detail="Request timed out")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}")

    try:
        await object_store.put(raw_key, data)
        job = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "input_type": "url",
            "source_ref": request.url,
            "file_size": len(data),
            "record_count": 0,
            "created_at": _now_iso(),
            "owner_id": current_user.user_id,
            "visibility": "private",
        }
        await job_store.create(job)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}")

    background_tasks.add_task(
        _run_ingest_worker,
        job_id,
        {
            "job_store": job_store,
            "object_store": object_store,
            "record_store": record_store,
            "vector_store": vector_store,
            "embedding_provider": embedding_provider,
            "filename": filename,
            "raw_key": raw_key,
        },
    )
    return IngestResponse(job_id=job_id, status=JobStatus.PENDING)
