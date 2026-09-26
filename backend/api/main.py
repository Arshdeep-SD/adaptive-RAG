from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import Settings, get_settings
from backend.core.errors import register_error_handlers
from backend.api.routers import ingest, jobs, query, records, ui_schema
from backend.api.routers import auth as auth_router

logger = logging.getLogger(__name__)


async def _get_local_stores(settings: Settings) -> tuple:
    """Return local stores (SQLite or in-memory) based on settings."""
    if settings.USE_LOCAL_DB:
        # Use SQLite for persistence when USE_LOCAL_DB is True
        db_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(db_dir, "..", "..", "db", "ragsqlite.db")
        
        from backend.db.sqlite_store import (
            LocalJobStore,
            LocalRecordStore,
            LocalUserStore,
            LocalUICacheStore,
        )
        
        job_store = LocalJobStore(db_path)
        record_store = LocalRecordStore(db_path)
        user_store = LocalUserStore(db_path)
        ui_cache_store = LocalUICacheStore(db_path)
        
        logger.info(f"Using SQLite database: {db_path}")
    else:
        # Use in-memory stores when USE_LOCAL_DB is False
        from backend.db.local_store import (
            LocalJobStore,
            LocalRecordStore,
            LocalUserStore,
            LocalUICacheStore,
        )
        
        job_store = LocalJobStore()
        record_store = LocalRecordStore()
        user_store = LocalUserStore()
        ui_cache_store = LocalUICacheStore()
        
        logger.info("Using in-memory stores")
    
    return job_store, record_store, user_store, ui_cache_store


async def _seed_admin(settings: Settings) -> None:
    """Create the initial admin user if one doesn't already exist."""
    import uuid
    from passlib.context import CryptContext
    
    _, _, user_store, _ = await _get_local_stores(settings)

    existing = await user_store.get_by_username(settings.ADMIN_USERNAME)
    if existing:
        return

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = {
        "user_id": str(uuid.uuid4()),
        "username": settings.ADMIN_USERNAME,
        "hashed_password": pwd_context.hash(settings.ADMIN_PASSWORD),
        "role": "admin",
        "created_at": "",  # SQLite doesn't need this for users table
    }
    await user_store.create(user)
    logger.info("Seeded admin user: %s", settings.ADMIN_USERNAME)


async def _reset_stuck_jobs(settings: Settings) -> None:
    """Mark any PROCESSING or PENDING jobs as FAILED — they were interrupted by a server restart."""
    job_store, _, _, _ = await _get_local_stores(settings)
    
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
