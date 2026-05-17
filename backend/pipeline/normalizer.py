from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def build_record(
    job_id: str,
    source_ref: str,
    content_type: str,
    text: str,
    chunk_index: int,
    payload: Any = None,
    metadata: dict | None = None,
) -> dict:
    return {
        "record_id": str(uuid.uuid4()),
        "job_id": job_id,
        "source_ref": source_ref,
        "content_type": content_type,
        "text": text,
        "payload": payload,
        "chunk_index": chunk_index,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
