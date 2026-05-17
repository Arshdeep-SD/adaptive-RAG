from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


def handler(event, context):
    """
    S3 event trigger → ingest worker.
    Event format: S3 ObjectCreated event.
    Key format: raw/{job_id}/{filename}
    """
    from backend.core.config import get_settings
    from backend.pipeline.ingest_worker import process_job

    settings = get_settings()

    for record in event.get("Records", []):
        s3 = record.get("s3", {})
        key = s3.get("object", {}).get("key", "")

        parts = key.split("/")
        if len(parts) < 3 or parts[0] != "raw":
            logger.warning("Unexpected S3 key format: %s", key)
            continue

        job_id = parts[1]
        filename = "/".join(parts[2:])

        logger.info("Processing S3 event: job_id=%s filename=%s", job_id, filename)

        from backend.api.deps import (
            get_embedding_provider,
            get_job_store,
            get_object_store,
            get_record_store,
            get_vector_store,
        )

        # Build deps with AWS implementations (USE_LOCAL_STORE=False in Lambda)
        job_store = get_job_store(settings)
        object_store = get_object_store(settings)
        record_store = get_record_store(settings)
        vector_store = get_vector_store(settings)
        embedding_provider = get_embedding_provider(settings)

        asyncio.run(process_job(
            job_id=job_id,
            job_store=job_store,
            object_store=object_store,
            record_store=record_store,
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            filename=filename,
            raw_key=key,
        ))
