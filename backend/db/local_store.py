from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalJobStore:
    """Thread-safe in-memory job store for local development."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: dict) -> None:
        async with self._lock:
            self._jobs[job["job_id"]] = dict(job)

    async def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    async def update(self, job_id: str, **fields) -> None:
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(fields)

    async def update_status(self, job_id: str, status: str) -> None:
        await self.update(job_id, status=status)

    async def list_all(self) -> list[dict]:
        return sorted(self._jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)

    async def delete(self, job_id: str) -> None:
        async with self._lock:
            self._jobs.pop(job_id, None)


class LocalRecordStore:
    """Thread-safe in-memory record store for local development."""

    def __init__(self) -> None:
        self._records: dict[str, dict] = {}
        self._by_job: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()

    async def put(self, record: dict) -> None:
        async with self._lock:
            rid = record["record_id"]
            self._records[rid] = dict(record)
            job_id = record.get("job_id", "")
            self._by_job.setdefault(job_id, []).append(rid)

    async def get(self, record_id: str) -> dict | None:
        return self._records.get(record_id)

    async def list_by_job(self, job_id: str) -> list[dict]:
        ids = self._by_job.get(job_id, [])
        return [self._records[i] for i in ids if i in self._records]

    async def bulk_put(self, records: list[dict]) -> None:
        for r in records:
            await self.put(r)

    async def delete_by_job(self, job_id: str) -> None:
        async with self._lock:
            for rid in self._by_job.pop(job_id, []):
                self._records.pop(rid, None)


class LocalUICacheStore:
    """In-memory UI schema cache for local development."""

    def __init__(self) -> None:
        self._cache: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def get(self, pattern_hash: str) -> dict | None:
        return self._cache.get(pattern_hash)

    async def put(self, pattern_hash: str, ui_schema: dict, sample_query: str = "") -> None:
        async with self._lock:
            self._cache[pattern_hash] = {
                "query_pattern_hash": pattern_hash,
                "ui_schema": ui_schema,
                "hit_count": 0,
                "last_used_at": _now_iso(),
                "sample_query": sample_query,
            }

    async def increment_hit(self, pattern_hash: str) -> None:
        async with self._lock:
            if pattern_hash in self._cache:
                self._cache[pattern_hash]["hit_count"] += 1
                self._cache[pattern_hash]["last_used_at"] = _now_iso()


class LocalUserStore:
    """Thread-safe in-memory user store for local development."""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}        # user_id → user dict
        self._by_username: dict[str, str] = {}   # username → user_id
        self._lock = asyncio.Lock()

    async def create(self, user: dict) -> None:
        async with self._lock:
            if user["username"] in self._by_username:
                raise ValueError(f"Username '{user['username']}' already exists")
            self._users[user["user_id"]] = dict(user)
            self._by_username[user["username"]] = user["user_id"]

    async def get_by_id(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    async def get_by_username(self, username: str) -> dict | None:
        uid = self._by_username.get(username)
        return self._users.get(uid) if uid else None

    async def list_all(self) -> list[dict]:
        return sorted(self._users.values(), key=lambda u: u.get("created_at", ""))

    async def delete(self, user_id: str) -> None:
        async with self._lock:
            user = self._users.pop(user_id, None)
            if user:
                self._by_username.pop(user["username"], None)

    def _load_from_list(self, users: list[dict]) -> None:
        """Bulk-load from persisted data (called during startup restore)."""
        for u in users:
            self._users[u["user_id"]] = dict(u)
            self._by_username[u["username"]] = u["user_id"]


class LocalVectorRecord:
    __slots__ = ("record_id", "job_id", "text", "embedding")

    def __init__(self, record_id: str, job_id: str, text: str, embedding: list[float]):
        self.record_id = record_id
        self.job_id = job_id
        self.text = text
        self.embedding = embedding


class LocalVectorStore:
    """numpy cosine-similarity vector store for local development."""

    def __init__(self) -> None:
        self._records: list[LocalVectorRecord] = []
        self._lock = asyncio.Lock()

    async def bulk_index(self, records: list[dict]) -> None:
        import numpy as np
        async with self._lock:
            for r in records:
                emb = np.asarray(r["embedding"], dtype=np.float32)
                norm = float(np.linalg.norm(emb))
                if norm > 0:
                    emb = emb / norm
                self._records.append(
                    LocalVectorRecord(r["record_id"], r.get("job_id", ""), r["text"], emb.tolist())
                )

    async def count_by_job(self, job_id: str) -> int:
        async with self._lock:
            return sum(1 for r in self._records if r.job_id == job_id)

    async def delete_by_job(self, job_id: str) -> None:
        async with self._lock:
            self._records = [r for r in self._records if r.job_id != job_id]

    async def search(
        self, embedding: list[float], top_k: int, allowed_job_ids: set[str] | None = None
    ) -> list[dict]:
        import numpy as np
        candidates = (
            [r for r in self._records if r.job_id in allowed_job_ids]
            if allowed_job_ids is not None
            else list(self._records)
        )
        if not candidates:
            return []
        q = np.asarray(embedding, dtype=np.float32)
        norm = float(np.linalg.norm(q))
        if norm > 0:
            q = q / norm
        matrix = np.array([r.embedding for r in candidates], dtype=np.float32)
        scores = matrix @ q
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            {"record_id": candidates[i].record_id, "score": float(scores[i])}
            for i in top_indices
        ]
