from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def chunk_audio(data: bytes, filename: str) -> list[dict]:
    """
    Produce a single indexable text chunk for an audio file.
    Uses mutagen to extract real metadata; falls back to filename + size.
    Never indexes raw binary bytes.
    """
    text = _extract_metadata(data, filename)
    return [{"text": text, "chunk_index": 0, "metadata": {"filename": filename, "source": "audio"}}]


def _extract_metadata(data: bytes, filename: str) -> str:
    lines = [f"Audio file: {filename}"]

    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(io.BytesIO(data), easy=True)
        if audio is not None:
            if audio.info:
                duration = getattr(audio.info, "length", None)
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    lines.append(f"Duration: {mins}:{secs:02d}")
                bitrate = getattr(audio.info, "bitrate", None)
                if bitrate:
                    lines.append(f"Bitrate: {bitrate // 1000} kbps")
                sample_rate = getattr(audio.info, "sample_rate", None)
                if sample_rate:
                    lines.append(f"Sample rate: {sample_rate} Hz")

            for tag in ("title", "artist", "album", "date", "genre"):
                val = audio.get(tag)
                if val:
                    lines.append(f"{tag.capitalize()}: {val[0]}")
    except Exception as exc:
        logger.debug("mutagen metadata extraction failed (%s)", exc)

    lines.append(f"File size: {len(data) // 1024} KB")
    return "\n".join(lines)
