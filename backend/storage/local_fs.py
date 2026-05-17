from __future__ import annotations

import os


class LocalFileStore:
    """Local filesystem object store for development (mirrors S3 layout)."""

    def __init__(self, base_path: str):
        self._base = base_path
        os.makedirs(base_path, exist_ok=True)

    def _full_path(self, key: str) -> str:
        path = os.path.join(self._base, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    async def put(self, key: str, data: bytes) -> None:
        with open(self._full_path(key), "wb") as f:
            f.write(data)

    async def get(self, key: str) -> bytes:
        with open(self._full_path(key), "rb") as f:
            return f.read()

    async def delete_prefix(self, prefix: str) -> None:
        import shutil
        target = os.path.join(self._base, prefix)
        if os.path.exists(target):
            shutil.rmtree(target)

    async def list_keys(self, prefix: str) -> list[str]:
        """Return all keys under prefix (filenames only, not subdirs)."""
        target = os.path.join(self._base, prefix)
        if not os.path.isdir(target):
            return []
        return [
            os.path.join(prefix, f)
            for f in sorted(os.listdir(target))
            if os.path.isfile(os.path.join(target, f))
        ]

    async def get_prefix(self, prefix: str) -> list[tuple[str, bytes]]:
        """Return all (key, data) pairs whose keys start with prefix."""
        results = []
        prefix_dir = os.path.join(self._base, prefix)
        if not os.path.isdir(prefix_dir):
            return results
        for fname in os.listdir(prefix_dir):
            fpath = os.path.join(prefix_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    results.append((os.path.join(prefix, fname), f.read()))
        return results
