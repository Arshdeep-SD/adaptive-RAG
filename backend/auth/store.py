from __future__ import annotations

from functools import lru_cache

from backend.db.local_store import LocalUserStore


@lru_cache
def _local_user_store() -> LocalUserStore:
    return LocalUserStore()
