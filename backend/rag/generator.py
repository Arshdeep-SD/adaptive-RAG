from __future__ import annotations

import json
import logging
import re

from backend.core.config import Settings
from backend.core.models import SourceRef

logger = logging.getLogger(__name__)

ANSWER_SYSTEM_PROMPT = (
    "You are a retrieval-grounded assistant. Answer the user's question using ONLY the provided "
    "context passages. The passages are always plain text — some may be text descriptions of images, "
    "screenshots, charts, or other media that were automatically transcribed. Treat all passage content "
    "as readable text you can reason about. If the context is insufficient, say so explicitly — do not "
    "speculate. "
    "Cite every fact with an inline reference in this EXACT format: [ref:<id>] "
    "where <id> is the id= attribute of the passage (copy it verbatim, do not shorten it). "
    "Example: 'The model achieved 94% accuracy [ref:3f8a1b2c-0001-0002-0003-000400050006].' "
    "Always include the 'ref:' prefix. Never use a different bracket format. "
    "Keep answers concise and factual. Output plain text only; UI structure is generated separately."
)


def _normalize_citations(text: str) -> str:
    """Add missing ref: prefix to bare hex/UUID inline citations."""
    return re.sub(
        r'\[(?!ref:)([0-9a-f]{8}[0-9a-f\-]*[0-9a-f])\]',
        lambda m: f'[ref:{m.group(1)}]',
        text,
        flags=re.IGNORECASE,
    )


def _build_context_block(sources: list[SourceRef]) -> str:
    passages = "\n".join(
        f'  <passage id="{s.record_id}" source="{s.source_ref}">{s.text}</passage>'
        for s in sources
    )
    return f"<context>\n{passages}\n</context>"


async def generate_answer(
    query: str,
    sources: list[SourceRef],
    settings: Settings,
) -> str:
    if not sources:
        return "No relevant context found in the indexed data."

    if settings.USE_LOCAL_STORE:
        return await _call_ollama(query, sources, settings)

    return await _call_bedrock(query, sources, settings)


async def _call_ollama(query: str, sources: list[SourceRef], settings: Settings) -> str:
    import httpx

    prompt = f"{_build_context_block(sources)}\n<question>{query}</question>"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            return _normalize_citations(resp.json()["message"]["content"])
    except httpx.ConnectError:
        logger.warning("Ollama not running at %s — falling back to stub", settings.OLLAMA_BASE_URL)
        return _stub_answer(sources)
    except Exception as exc:
        logger.error("Ollama call failed: %s", exc)
        return f"Unable to generate answer: {exc}"


async def _call_bedrock(query: str, sources: list[SourceRef], settings: Settings) -> str:
    import boto3

    client = boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)
    prompt = f"{_build_context_block(sources)}\n<question>{query}</question>"
    try:
        resp = client.converse(
            modelId=settings.BEDROCK_ANSWER_MODEL,
            system=[{"text": ANSWER_SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1024},
        )
        return _normalize_citations(resp["output"]["message"]["content"][0]["text"])
    except Exception as exc:
        logger.error("Bedrock answer generation failed: %s", exc)
        return f"Unable to generate answer: {exc}"


def _stub_answer(sources: list[SourceRef]) -> str:
    """Plain-text fallback when no LLM is reachable."""
    parts = [f"[ref:{s.record_id[:8]}] {_readable_text(s.text)}" for s in sources[:3]]
    return "Retrieved context: " + " | ".join(parts)


def _readable_text(raw: str) -> str:
    stripped = raw.strip()
    try:
        data = json.loads(stripped)
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                cols = list(data[0].keys())
                sample = ", ".join(f"{k}: {data[0][k]}" for k in cols[:4])
                return f"{len(data)} rows — e.g. {sample}"
            return f"{len(data)} items"
        elif isinstance(data, dict):
            return ", ".join(f"{k}: {v}" for k, v in list(data.items())[:4])
    except (json.JSONDecodeError, ValueError):
        pass
    sentence_end = stripped.find(". ")
    if 0 < sentence_end < 120:
        return stripped[: sentence_end + 1]
    return stripped[:100] + ("…" if len(stripped) > 100 else "")
