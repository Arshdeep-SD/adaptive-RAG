from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import Settings, get_settings
from backend.core.errors import register_error_handlers
from backend.api.routers import ingest, jobs, query, records, ui_schema
from backend.api.routers import auth as auth_router

logger = logging.getLogger(__name__)


async def _seed_admin(settings: Settings) -> None:
    """Create the initial admin user if one doesn't already exist."""
    import uuid
    from passlib.context import CryptContext
    from backend.db.local_store import _now_iso

    if settings.USE_LOCAL_STORE:
        from backend.auth.store import _local_user_store
        store = _local_user_store()
    else:
        from backend.db.dynamo import DynamoUserStore
        store = DynamoUserStore(
            table_name=settings.USERS_TABLE,
            region=settings.AWS_REGION,
            endpoint_url=settings.DYNAMO_ENDPOINT,
        )

    existing = await store.get_by_username(settings.ADMIN_USERNAME)
    if existing:
        return

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = {
        "user_id": str(uuid.uuid4()),
        "username": settings.ADMIN_USERNAME,
        "hashed_password": pwd_context.hash(settings.ADMIN_PASSWORD),
        "role": "admin",
        "created_at": _now_iso(),
    }
    await store.create(user)
    logger.info("Seeded admin user: %s", settings.ADMIN_USERNAME)


async def _reset_stuck_jobs(settings: Settings) -> None:
    """Mark any PROCESSING or PENDING jobs as FAILED — they were interrupted by a server restart."""
    if settings.USE_LOCAL_STORE:
        from backend.db.local_store import LocalJobStore
        from backend.api.deps import _local_job_store
        job_store = _local_job_store()
    else:
        from backend.db.dynamo import DynamoJobStore
        job_store = DynamoJobStore(
            table_name=settings.JOBS_TABLE,
            region=settings.AWS_REGION,
            endpoint_url=settings.DYNAMO_ENDPOINT,
        )
    all_jobs = await job_store.list_all()
    stuck = [j for j in all_jobs if j.get("status") in ("PROCESSING", "PENDING")]
    for job in stuck:
        await job_store.update(
            job["job_id"],
            status="FAILED",
            error="Server restarted during processing — please re-ingest.",
        )
    if stuck:
        logger.warning("Reset %d stuck job(s) to FAILED on startup", len(stuck))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.USE_LOCAL_STORE:
        logger.info("Restoring persisted jobs from disk…")
        from backend.pipeline.reload import reload_all_jobs
        await reload_all_jobs(settings)
    await _reset_stuck_jobs(settings)
    await _seed_admin(settings)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive RAG Data Platform",
        version="1.0.0",
        description="Heterogeneous data ingestion + retrieval-grounded QA with dynamic UI generation",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(auth_router.router)
    app.include_router(ingest.router)
    app.include_router(jobs.router)
    app.include_router(query.router)
    app.include_router(records.router)
    app.include_router(ui_schema.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
