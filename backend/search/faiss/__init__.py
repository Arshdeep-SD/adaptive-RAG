"""
FAISS (Facebook AI Similarity Search) - Local disk-based vector store.
Replaces AWS OpenSearch Serverless for local development and production deployment
without managed services.

Features:
- Disk-persistent index storage
- Cosine similarity search with HNSW
- No external dependencies beyond faiss-cpu/faiss-gpu
"""

from __future__ import annotations

import json
import os
from typing import Any


class FAISSVectorStore:
    """FAISS-based vector store with disk persistence."""

    dim = 384

    def __init__(self, index_path: str):
        self._index_path = index_path
        self._metadata_path = f"{index_path}.json"
        self._index = None
        self._dims = None