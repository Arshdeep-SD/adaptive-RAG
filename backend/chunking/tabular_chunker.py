from __future__ import annotations

import csv
import io
import json


def chunk_tabular(content: bytes, window_size: int = 10) -> list[dict]:
    """
    Chunk a CSV/TSV/log file into overlapping row windows.
    Each chunk = header + window_size rows, serialized as a JSON array of dicts.
    """
    text = content.decode("utf-8", errors="replace")
    dialect = _sniff_dialect(text)

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = list(reader)
    if not rows:
        return []

    chunks: list[dict] = []
    for start in range(0, len(rows), window_size):
        window = rows[start : start + window_size]
        chunk_text = json.dumps(window, ensure_ascii=False, indent=2)
        chunks.append({
            "text": chunk_text,
            "chunk_index": len(chunks),
            "metadata": {"row_start": start, "row_end": start + len(window)},
        })
    return chunks


def _sniff_dialect(text: str) -> str:
    first_line = text.split("\n")[0]
    if "\t" in first_line:
        return "excel-tab"
    return "excel"
