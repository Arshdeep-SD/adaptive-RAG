from __future__ import annotations

import base64
import io
import logging

logger = logging.getLogger(__name__)


def chunk_image(data: bytes, filename: str) -> list[dict]:
    from backend.core.config import get_settings
    settings = get_settings()

    meta = _image_metadata(data, filename)

    if settings.USE_LOCAL_STORE:
        description = _describe_with_ollama(data, settings.OLLAMA_BASE_URL, settings.OLLAMA_VISION_MODEL)
    else:
        description = _describe_with_bedrock(data, filename, settings.BEDROCK_VISION_MODEL, settings.BEDROCK_REGION)

    text = f"{meta}\n\n{description}" if description else meta
    return [{"text": text, "chunk_index": 0, "metadata": {"filename": filename, "source": "image"}}]


def _image_metadata(data: bytes, filename: str) -> str:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        return (
            f"Image file: {filename} | "
            f"Format: {img.format} | "
            f"Dimensions: {img.size[0]}x{img.size[1]}px | "
            f"Mode: {img.mode}"
        )
    except Exception:
        return f"Image file: {filename}"


def _describe_with_bedrock(data: bytes, filename: str, model_id: str, region: str) -> str | None:
    import boto3

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpeg"
    fmt_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}
    fmt = fmt_map.get(ext, "jpeg")

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        resp = client.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [
                    {"image": {"format": fmt, "source": {"bytes": data}}},
                    {"text": "Describe this image in detail. Include any text, charts, diagrams, or data visible."},
                ],
            }],
            inferenceConfig={"maxTokens": 512},
        )
        return resp["output"]["message"]["content"][0]["text"]
    except Exception as exc:
        logger.warning("Bedrock vision failed (%s) — using metadata only", exc)
        return None


def _describe_with_ollama(data: bytes, base_url: str, vision_model: str) -> str | None:
    import httpx

    b64 = base64.standard_b64encode(data).decode()
    payload = {
        "model": vision_model,
        "messages": [
            {
                "role": "user",
                "content": "Describe this image in detail. Include any text, charts, diagrams, or data visible.",
                "images": [b64],
            }
        ],
        "stream": False,
    }

    try:
        resp = httpx.post(f"{base_url}/api/chat", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except httpx.ConnectError:
        logger.info("Ollama not running — image stored with metadata only")
        return None
    except Exception as exc:
        logger.warning("Ollama vision failed (%s) — using metadata only", exc)
        return None
