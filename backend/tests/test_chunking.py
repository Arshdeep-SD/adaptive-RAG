"""Unit tests for type-aware chunkers."""
import json
import pytest

from backend.chunking.detector import detect_type
from backend.chunking.prose_chunker import chunk_prose
from backend.chunking.json_chunker import chunk_json
from backend.chunking.tabular_chunker import chunk_tabular


class TestDetector:
    def test_detects_pdf_by_extension(self):
        assert detect_type("report.pdf", b"%PDF-1.4") == "pdf"

    def test_detects_csv_by_extension(self):
        assert detect_type("data.csv", b"id,name\n1,Alice") == "tabular"

    def test_detects_json_by_extension(self):
        assert detect_type("config.json", b'{"key": "val"}') == "json"

    def test_detects_txt_as_prose(self):
        assert detect_type("readme.txt", b"Hello world") == "prose"

    def test_sniffs_json_content(self):
        assert detect_type("unknown", b'{"key": "value"}') == "json"

    def test_sniffs_csv_content(self):
        assert detect_type("unknown", b"a,b,c,d\n1,2,3,4\n5,6,7,8") == "tabular"

    def test_defaults_to_prose(self):
        assert detect_type("mystery", b"just some words here") == "prose"


class TestProseChunker:
    def test_returns_list_of_dicts(self):
        chunks = chunk_prose("Hello world. This is a test.")
        assert isinstance(chunks, list)
        assert all("text" in c and "chunk_index" in c for c in chunks)

    def test_empty_string(self):
        assert chunk_prose("") == []

    def test_chunks_have_sequential_indices(self):
        text = " ".join(["word"] * 200)
        chunks = chunk_prose(text)
        for i, c in enumerate(chunks):
            assert c["chunk_index"] == i


class TestJsonChunker:
    def test_flat_dict_is_single_chunk(self):
        data = {"name": "Alice", "age": 30}
        chunks = chunk_json(data)
        assert len(chunks) == 1
        assert "Alice" in chunks[0]["text"]

    def test_list_of_small_objects(self):
        data = [{"id": i, "val": i * 2} for i in range(5)]
        chunks = chunk_json(data)
        assert len(chunks) == 5

    def test_large_array_splits(self):
        data = [{"id": i} for i in range(50)]
        chunks = chunk_json(data, max_array_window=10)
        assert len(chunks) == 5

    def test_json_path_preserved(self):
        data = {"users": [{"name": "Bob"}]}
        chunks = chunk_json(data)
        assert any("users" in c.get("json_path", "") for c in chunks)


class TestTabularChunker:
    CSV = b"id,name,dept\n1,Alice,Eng\n2,Bob,Sales\n3,Carol,HR\n"

    def test_returns_chunks(self):
        chunks = chunk_tabular(self.CSV, window_size=2)
        assert len(chunks) >= 1

    def test_chunk_contains_all_rows(self):
        chunks = chunk_tabular(self.CSV, window_size=10)
        assert len(chunks) == 1
        data = json.loads(chunks[0]["text"])
        assert len(data) == 3

    def test_empty_csv(self):
        assert chunk_tabular(b"", window_size=5) == []
