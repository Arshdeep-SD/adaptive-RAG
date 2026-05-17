from __future__ import annotations

import asyncio
import json
import logging
import traceback

from backend.chunking.detector import detect_type
from backend.pipeline.normalizer import build_record

logger = logging.getLogger(__name__)


async def process_job(
    job_id: str,
    *,
    job_store,
    object_store,
    record_store,
    vector_store,
    embedding_provider,
    filename: str,
    raw_key: str,
) -> None:
    """
    Core ingestion pipeline.
    1. Fetch raw bytes from object store
    2. Detect content type
    3. Chunk with type-aware chunker
    4. Batch embed chunks
    5. Write records + index vectors
    6. Update job status
    """
    try:
        await job_store.update_status(job_id, "PROCESSING")

        # 1. Fetch raw file
        raw_bytes = await object_store.get(raw_key)

        # 2. Detect type
        content_type = detect_type(filename, raw_bytes)

        # 3. Chunk — run in executor so CPU-bound work doesn't block the event loop
        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(None, _chunk, content_type, raw_bytes, filename)
        if not chunks:
            await job_store.update(job_id, status="FAILED", error="No chunks produced from input")
            return

        # 4. Embed in batch — also CPU/network-bound, keep event loop free
        texts = [c["text"] for c in chunks]
        embeddings = await loop.run_in_executor(None, embedding_provider.embed, texts)

        # 5. Build records + index
        records = []
        vector_docs = []
        for chunk, emb in zip(chunks, embeddings):
            rec = build_record(
                job_id=job_id,
                source_ref=filename,
                content_type=content_type,
                text=chunk["text"],
                chunk_index=chunk.get("chunk_index", len(records)),
                payload=chunk.get("metadata"),
                metadata=chunk.get("metadata"),
            )
            records.append(rec)
            vector_docs.append({
                "record_id": rec["record_id"],
                "job_id": job_id,
                "text": rec["text"],
                "embedding": emb,
            })

        await record_store.bulk_put(records)
        await vector_store.bulk_index(vector_docs)

        # Poll until OpenSearch Serverless makes the docs searchable (eventual consistency)
        expected = len(records)
        for _ in range(20):
            await asyncio.sleep(4)
            indexed = await vector_store.count_by_job(job_id)
            if indexed >= expected:
                break
        else:
            logger.warning("Job %s: only %d/%d docs indexed after timeout", job_id, indexed, expected)

        # 6. Write normalized JSONL + job metadata (for cross-restart persistence)
        jsonl = "\n".join(json.dumps(r) for r in records).encode()
        await object_store.put(f"normalized/{job_id}/records.jsonl", jsonl)

        await job_store.update(job_id, status="READY", record_count=len(records))

        job_meta = await job_store.get(job_id)
        if job_meta:
            await object_store.put(
                f"normalized/{job_id}/job.json",
                json.dumps(job_meta, default=str).encode(),
            )

        logger.info("Job %s completed: %d records indexed", job_id, len(records))

    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("Job %s failed: %s\n%s", job_id, exc, tb)
        try:
            err_payload = json.dumps({"error": str(exc), "traceback": tb}).encode()
            await object_store.put(f"dlq/{job_id}/error.json", err_payload)
        except Exception:
            pass
        await job_store.update(job_id, status="FAILED", error=str(exc))


def _chunk(content_type: str, raw_bytes: bytes, filename: str = "") -> list[dict]:
    if content_type == "pdf":
        from backend.chunking.prose_chunker import chunk_pdf
        return chunk_pdf(raw_bytes)
    if content_type == "json":
        import json as _json
        from backend.chunking.json_chunker import chunk_json
        try:
            data = _json.loads(raw_bytes.decode("utf-8"))
            return chunk_json(data)
        except Exception:
            pass
    if content_type == "tabular":
        from backend.chunking.tabular_chunker import chunk_tabular
        return chunk_tabular(raw_bytes)
    if content_type == "image":
        from backend.chunking.image_chunker import chunk_image
        return chunk_image(raw_bytes, filename)
    if content_type == "audio":
        from backend.chunking.audio_chunker import chunk_audio
        return chunk_audio(raw_bytes, filename)
    # Default: prose
    from backend.chunking.prose_chunker import chunk_prose
    return chunk_prose(raw_bytes.decode("utf-8", errors="replace"))
