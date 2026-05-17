from __future__ import annotations

import json


def chunk_json(data: dict | list, max_array_window: int = 20) -> list[dict]:
    """
    Walk a JSON tree and emit leaf objects as chunks.
    Arrays larger than max_array_window are split into windows.
    Each chunk carries a json_path for retrieval context.
    """
    chunks: list[dict] = []
    _walk(data, "$", chunks, max_array_window)
    for idx, chunk in enumerate(chunks):
        chunk["chunk_index"] = idx
    return chunks


def _walk(node, path: str, out: list[dict], max_window: int) -> None:
    if isinstance(node, list):
        if len(node) <= max_window:
            for i, item in enumerate(node):
                _walk(item, f"{path}[{i}]", out, max_window)
        else:
            for start in range(0, len(node), max_window):
                window = node[start : start + max_window]
                text = json.dumps(window, ensure_ascii=False, indent=2)
                out.append({
                    "text": text,
                    "json_path": f"{path}[{start}:{start + len(window)}]",
                    "metadata": {"json_path": f"{path}[{start}:{start + len(window)}]"},
                })
    elif isinstance(node, dict):
        # Check if it's a leaf (no nested dicts/lists)
        has_nested = any(isinstance(v, (dict, list)) for v in node.values())
        if not has_nested:
            text = json.dumps(node, ensure_ascii=False, indent=2)
            out.append({
                "text": text,
                "json_path": path,
                "metadata": {"json_path": path},
            })
        else:
            for key, value in node.items():
                _walk(value, f"{path}.{key}", out, max_window)
    else:
        # Primitive at root level — emit as-is
        out.append({
            "text": str(node),
            "json_path": path,
            "metadata": {"json_path": path},
        })
