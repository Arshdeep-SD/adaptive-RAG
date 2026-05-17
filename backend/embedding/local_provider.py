from __future__ import annotations

import numpy as np


class LocalEmbeddingProvider:
    """SentenceTransformer-based local embedding provider (384-dim)."""

    dim = 384
    _model = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vecs = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return np.asarray(vecs, dtype=np.float32).tolist()
