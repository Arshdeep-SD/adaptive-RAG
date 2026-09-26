from __future__ import annotations
port os
from typing import Annotated

from fastapi import Depends

from backend.core.config import Settings, get_settings
from backend.db.sqlite_store import LocalJobStore, LocalRecordStore, LocalUICacheStore
# Helper to get db path

def _get_db_path():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(db_dir, "..", "..", "db", "ragsqlite.db")
@lru_cache

    db_path = _get_db_path() if settings.USE_LOCAL_DB else ":memory:"
def _get_job_store(settings):
    return LocalJobStore(db_path=db_path)

@lru_cache
def _get_record_store(settings):
    db_path = _get_db_path() if settings.USE_LOCAL_DB else ":memory:"
    return LocalRecordStore(db_path=db_path)
