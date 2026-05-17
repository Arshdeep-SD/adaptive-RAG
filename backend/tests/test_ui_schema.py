"""Tests for UI schema validation and fallback."""
import pytest

from backend.rag.ui_generator import validate_ui_schema, build_fallback_schema, compute_pattern_hash


VALID_SCHEMA = {
    "version": "1.0",
    "title": "Test",
    "layout": {
        "type": "section",
        "heading": "Answer",
        "child": {
            "type": "stack",
            "direction": "vertical",
            "children": [
                {"type": "component", "component": "text", "props": {"content": "hi"}},
                {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}},
            ],
        },
    },
    "data_bindings": {"sources": []},
}


def test_valid_schema_passes():
    validate_ui_schema(VALID_SCHEMA)  # should not raise


def test_missing_version_fails():
    import jsonschema
    bad = dict(VALID_SCHEMA)
    del bad["version"]
    with pytest.raises(jsonschema.ValidationError):
        validate_ui_schema(bad)


def test_unknown_component_fails():
    import jsonschema
    bad = {
        **VALID_SCHEMA,
        "layout": {
            "type": "component",
            "component": "unknown_widget",
            "props": {},
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_ui_schema(bad)


def test_fallback_schema_is_valid():
    from backend.core.models import SourceRef
    sources = [SourceRef(record_id="r1", source_ref="test.txt", text="hello", score=0.9)]
    fallback = build_fallback_schema("Answer text", sources)
    validate_ui_schema(fallback)  # should not raise


def test_pattern_hash_is_normalized():
    h1 = compute_pattern_hash("What is the employee count?")
    h2 = compute_pattern_hash("WHAT IS THE EMPLOYEE COUNT")
    assert h1 == h2


def test_different_queries_different_hashes():
    h1 = compute_pattern_hash("show employee list")
    h2 = compute_pattern_hash("show product catalog")
    assert h1 != h2
