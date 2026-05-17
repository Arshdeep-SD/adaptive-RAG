from __future__ import annotations

import json
from typing import Literal


ContentType = Literal["prose", "json", "tabular", "pdf", "image", "audio"]

_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "tif"}
_AUDIO_EXTENSIONS = {"mp3", "wav", "flac", "ogg", "m4a", "aac", "wma", "opus", "aiff"}
_IMAGE_MAGIC = {
    b"\xff\xd8\xff",          # JPEG
    b"\x89PNG",               # PNG
    b"GIF8",                  # GIF
    b"RIFF",                  # WebP (starts RIFF....WEBP)
}
_AUDIO_MAGIC = [
    (b"\xff\xfb", "mp3"),     # MP3
    (b"\xff\xf3", "mp3"),
    (b"\xff\xf2", "mp3"),
    (b"ID3",      "mp3"),     # MP3 with ID3 tag
    (b"RIFF",     "wav"),     # WAV (also matches WebP — checked after image)
    (b"fLaC",     "flac"),    # FLAC
    (b"OggS",     "ogg"),     # OGG
]


def detect_type(filename: str, content: bytes) -> ContentType:
    """Detect content type from filename extension first, then content sniffing."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        return "pdf"
    if ext == "json":
        return "json"
    if ext in ("csv", "tsv", "log"):
        return "tabular"
    if ext in ("txt", "md", "rst"):
        return "prose"
    if ext in _IMAGE_EXTENSIONS:
        return "image"
    if ext in _AUDIO_EXTENSIONS:
        return "audio"

    # Content sniffing fallback
    sample = content[:4096]

    # Magic bytes for images (check before RIFF so WebP wins over WAV)
    for magic in _IMAGE_MAGIC:
        if sample.startswith(magic):
            # RIFF could be WAV — confirm WebP
            if magic == b"RIFF" and b"WEBP" not in sample[:12]:
                break
            return "image"

    # Magic bytes for audio
    for magic, _ in _AUDIO_MAGIC:
        if sample.startswith(magic):
            return "audio"

    # Try JSON
    try:
        text_sample = sample.decode("utf-8", errors="replace").strip()
        if text_sample.startswith(("{", "[")):
            json.loads(sample.decode("utf-8", errors="replace"))
            return "json"
    except (json.JSONDecodeError, ValueError):
        pass

    # Heuristic: lots of commas/tabs on first line → tabular
    try:
        first_line = sample.decode("utf-8", errors="replace").split("\n")[0]
        if first_line.count(",") >= 3 or first_line.count("\t") >= 2:
            return "tabular"
    except Exception:
        pass

    return "prose"
