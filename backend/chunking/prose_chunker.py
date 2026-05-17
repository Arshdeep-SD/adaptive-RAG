from __future__ import annotations

import io


def chunk_prose(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """
    Split prose text into overlapping token-aware chunks.
    Uses langchain RecursiveCharacterTextSplitter with tiktoken.
    Falls back to simple word-based split if langchain/tiktoken unavailable.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        pieces = splitter.split_text(text)
    except Exception:
        # Fallback: simple word-window split
        words = text.split()
        pieces = []
        step = max(1, chunk_size - chunk_overlap)
        for i in range(0, len(words), step):
            pieces.append(" ".join(words[i : i + chunk_size]))

    return [
        {"text": piece.strip(), "chunk_index": idx, "metadata": {}}
        for idx, piece in enumerate(pieces)
        if piece.strip()
    ]


def chunk_pdf(data: bytes, chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """Extract text from a PDF and chunk it."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n\n".join(pages_text)
    except Exception:
        full_text = data.decode("utf-8", errors="replace")
    return chunk_prose(full_text, chunk_size, chunk_overlap)
