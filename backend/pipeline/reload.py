from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


async def reload_all_jobs(settings) -> None:
    """
    Re-populate in-memory stores from persisted normalized records on startup.
    Only runs when USE_LOCAL_STORE=True. Skips jobs whose job.json is missing
    (i.e. jobs that failed or were created before persistence was added).
    """
    if not settings.USE_LOCAL_STORE:
        return

    normalized_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "normalized")
    if not os.path.isdir(normalized_dir):
        return

    from backend.api.deps import (
        _local_job_store,
        _local_record_store,
        _local_vector_store,
    )
    from backend.embedding.local_provider import LocalEmbeddingProvider

    job_store = _local_job_store()
    record_store = _local_record_store()
    vector_store = _local_vector_store()
    embedding_provider = LocalEmbeddingProvider()

    total_jobs = 0
    total_records = 0

    for job_id in os.listdir(normalized_dir):
        job_dir = os.path.join(normalized_dir, job_id)
        if not os.path.isdir(job_dir):
            continue

        job_meta_path = os.path.join(job_dir, "job.json")
        records_path = os.path.join(job_dir, "records.jsonl")

        if not os.path.exists(job_meta_path) or not os.path.exists(records_path):
            continue

        # Don't double-load (e.g. if reload is called twice)
        if await job_store.get(job_id):
            continue

        try:
            with open(job_meta_path) as f:
                job_meta = json.load(f)
            await job_store.create(job_meta)

            records: list[dict] = []
            with open(records_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))

            await record_store.bulk_put(records)

            if records:
                texts = [r["text"] for r in records]
                embeddings = embedding_provider.embed(texts)
                vector_docs = [
                    {
                        "record_id": r["record_id"],
                        "job_id": r["job_id"],
                        "text": r["text"],
                        "embedding": emb,
                    }
                    for r, emb in zip(records, embeddings)
                ]
                await vector_store.bulk_index(vector_docs)

            total_jobs += 1
            total_records += len(records)
            logger.info("Reloaded job %s: %d records", job_id, len(records))

        except Exception as exc:
            logger.warning("Failed to reload job %s: %s", job_id, exc)

    if total_jobs > 0:
        logger.info(
            "Startup reload complete: %d job(s), %d records restored",
            total_jobs,
            total_records,
        )
