from __future__ import annotations

from backend.core.models import SourceRef


async def hybrid_retrieve(
    query: str,
    top_k: int,
    embedding_provider,
    vector_store,
    record_store,
    allowed_job_ids: set[str],
) -> list[SourceRef]:
    """
    Embed query → vector search → fetch full record text → return SourceRefs.
    allowed_job_ids: only records from these jobs are returned. Always a set —
    admin gets all existing job IDs so orphaned chunks from deleted jobs are excluded.
    """
    q_emb = embedding_provider.embed([query])[0]
    vector_results = await vector_store.search(q_emb, top_k, allowed_job_ids=allowed_job_ids)

    sources: list[SourceRef] = []
    for vr in vector_results:
        rec = await record_store.get(vr["record_id"])
        if not rec:
            continue
        if rec.get("job_id") not in allowed_job_ids:
            continue
        sources.append(
            SourceRef(
                record_id=rec["record_id"],
                source_ref=rec["source_ref"],
                text=rec["text"],
                score=float(vr["score"]),
                job_id=rec.get("job_id"),
                content_type=rec.get("content_type"),
                chunk_index=rec.get("chunk_index", 0),
            )
        )
    return sources
