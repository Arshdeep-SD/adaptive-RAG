from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

from backend.core.config import Settings
from backend.core.models import SourceRef

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Content-type detection helpers
# ---------------------------------------------------------------------------
_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "tif"}
_CODE_EXTS = {
    "py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "cpp", "c", "cs",
    "rb", "sh", "bash", "sql", "html", "css", "yaml", "yml", "toml", "ini",
    "r", "m", "swift", "kt", "php", "scala", "lua", "dart",
}
_AUDIO_EXTS = {"mp3", "wav", "flac", "ogg", "m4a", "aac", "wma"}

_EXT_TO_LANG: dict[str, str] = {
    "py": "python", "js": "javascript", "ts": "typescript", "tsx": "tsx",
    "jsx": "jsx", "go": "go", "rs": "rust", "java": "java", "cpp": "cpp",
    "c": "c", "cs": "csharp", "rb": "ruby", "sh": "bash", "bash": "bash",
    "sql": "sql", "html": "html", "css": "css", "yaml": "yaml", "yml": "yaml",
    "toml": "toml", "json": "json", "kt": "kotlin", "swift": "swift",
    "php": "php", "scala": "scala", "lua": "lua", "dart": "dart",
}


def _file_ext(source_ref: str) -> str:
    return source_ref.rsplit(".", 1)[-1].lower() if "." in source_ref else ""


def _is_image(s: "SourceRef") -> bool:
    return s.content_type == "image" or _file_ext(s.source_ref) in _IMAGE_EXTS


def _is_code(s: "SourceRef") -> bool:
    return _file_ext(s.source_ref) in _CODE_EXTS


def _is_audio(s: "SourceRef") -> bool:
    return _file_ext(s.source_ref) in _AUDIO_EXTS


def _is_pdf(s: "SourceRef") -> bool:
    return s.content_type == "pdf" or _file_ext(s.source_ref) == "pdf"


def _first_of_type(sources: list["SourceRef"], predicate, top_n: int = 3):
    """Return the first source matching predicate within the top_n results, or None."""
    return next((s for s in sources[:top_n] if predicate(s)), None)


# ---------------------------------------------------------------------------
# Stopwords for query normalization
# ---------------------------------------------------------------------------
_STOPWORDS = frozenset(
    "what is the a an of in for on at to from by with how many which who when where why"
    .split()
)

# ---------------------------------------------------------------------------
# Few-shot examples — one per demo query pattern
# ---------------------------------------------------------------------------
_FEW_SHOT_EXAMPLES = """
## Few-shot examples

### Example 1 — Prose/summary query
Query: "What is the company mission?"
Answer: "Our mission is to empower engineers with intelligent data tools. [ref:abc123]"
Available bindings: ["answer", "sources"]

Output:
{
  "version": "1.0",
  "title": "Company Mission",
  "layout": {
    "type": "section",
    "heading": "Answer",
    "child": {
      "type": "stack",
      "direction": "vertical",
      "children": [
        {"type": "component", "component": "text", "props": {"content_binding": "answer", "variant": "body"}},
        {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}}
      ]
    }
  },
  "data_bindings": {}
}

### Example 2 — Tabular/employee data query
Query: "Show me the employee list"
Answer: "The dataset contains 10 employees across 3 departments. [ref:def456]"
Available bindings: ["answer", "sources", "data"]

Output:
{
  "version": "1.0",
  "title": "Employee List",
  "layout": {
    "type": "stack",
    "direction": "vertical",
    "children": [
      {
        "type": "grid",
        "columns": 3,
        "children": [
          {"type": "component", "component": "kpi", "props": {"label": "Total Employees", "value_binding": "answer"}},
          {"type": "component", "component": "kpi", "props": {"label": "Departments", "value_binding": "answer"}},
          {"type": "component", "component": "kpi", "props": {"label": "Data Source", "value_binding": "answer"}}
        ]
      },
      {
        "type": "component",
        "component": "table",
        "props": {
          "columns": [
            {"key": "name", "label": "Name", "type": "text"},
            {"key": "department", "label": "Department", "type": "text"},
            {"key": "role", "label": "Role", "type": "text"}
          ],
          "rows_binding": "data"
        }
      },
      {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}}
    ]
  },
  "data_bindings": {}
}

### Example 3 — Trend/chart query
Query: "Show me the sales trend over time"
Answer: "Sales grew 23% from Q1 to Q4. [ref:ghi789]"
Available bindings: ["answer", "sources", "data"]

Output:
{
  "version": "1.0",
  "title": "Sales Trend",
  "layout": {
    "type": "stack",
    "direction": "vertical",
    "children": [
      {"type": "component", "component": "kpi", "props": {"label": "Growth", "value": "23%", "unit": "%"}},
      {
        "type": "component",
        "component": "chart",
        "props": {"kind": "line", "x": "month", "y": "revenue", "data_binding": "data"}
      },
      {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}}
    ]
  },
  "data_bindings": {}
}

### Example 4 — Timeline/incident query
Query: "What incidents occurred last month?"
Answer: "3 incidents were recorded. The most severe was on March 15. [ref:jkl012]"
Available bindings: ["answer", "sources", "data"]

Output:
{
  "version": "1.0",
  "title": "Incident Timeline",
  "layout": {
    "type": "section",
    "heading": "Incident Log",
    "child": {
      "type": "stack",
      "direction": "vertical",
      "children": [
        {"type": "component", "component": "timeline", "props": {"events_binding": "data"}},
        {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}}
      ]
    }
  },
  "data_bindings": {}
}

### Example 5 — Product catalog query
Query: "List the available products"
Answer: "The catalog contains 5 products across 2 categories. [ref:mno345]"
Available bindings: ["answer", "sources", "data"]

Output:
{
  "version": "1.0",
  "title": "Product Catalog",
  "layout": {
    "type": "stack",
    "direction": "vertical",
    "children": [
      {"type": "component", "component": "text", "props": {"content_binding": "answer", "variant": "body"}},
      {
        "type": "grid",
        "columns": 2,
        "children": [
          {"type": "component", "component": "card", "props": {"title_binding": "answer", "body_binding": "answer"}},
          {"type": "component", "component": "list", "props": {"items_binding": "data", "item_template": "title_subtitle"}}
        ]
      },
      {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}}
    ]
  },
  "data_bindings": {}
}
"""

# ---------------------------------------------------------------------------
# System prompt (Section 5 contract injected inline)
# ---------------------------------------------------------------------------
_UI_SYSTEM_PROMPT = """\
You generate UI layout schemas for a data platform. Output ONLY valid JSON — no markdown, no prose, no code fences.

## Schema Contract

Top-level shape:
{
  "version": "1.0",
  "title": "string",
  "layout": <LayoutNode>,
  "data_bindings": {}
}

Layout primitives (type field selects which):
- stack: {type:"stack", direction:"vertical"|"horizontal", children:[LayoutNode,...]}
- grid:  {type:"grid", columns:<int 1-6>, children:[LayoutNode,...]}
- tabs:  {type:"tabs", tabs:[{label:"string", content:LayoutNode},...]}
- section: {type:"section", heading:"string", child:LayoutNode}
- component: {type:"component", component:<see below>, props:{...}}

Component library (use ONLY these names):
- text:         {content_binding?:"string", content?:"string", variant?:"body"|"caption"|"heading"}
- kpi:          {label:"string", value?:<string|number>, value_binding?:"string", delta?:<number>, unit?:"string"}
- table:        {columns:[{key,label,type?:"text"|"number"|"date"},...], rows_binding:"string"}
- chart:        {kind:"bar"|"line"|"pie"|"scatter", x:"string", y:<string|string[]>, data_binding:"string"}
- card:         {title?:"string", title_binding?:"string", body?:"string", body_binding?:"string", footer?:"string"}
- list:         {items_binding:"string", item_template:"title_subtitle"|"bullet"}
- timeline:     {events_binding:"string"}
- form:         {fields:[{name,label,type:"text"|"number"|"select",options?:[...]},...], submit_action:"string"}
- source_refs:  {refs_binding:"string"}
- image_viewer: {src_binding:"string", filename_binding?:"string", description_binding?:"string"}
- code_editor:  {code_binding:"string", language?:"string", filename_binding?:"string"}
- audio_player: {src_binding:"string", filename_binding?:"string"}
- pdf_viewer:   {src_binding:"string", filename_binding?:"string"}

## Hard Rules
1. Output ONLY valid JSON. No markdown, no prose, no comments.
2. Use ONLY the components listed above. Never invent component names.
3. Every *_binding string must reference a key that will be in data_bindings.
4. Always include a source_refs component with refs_binding pointing to "sources".
5. Do not nest stack/grid more than 3 levels deep.
6. If the query is prose/unstructured, use: section { heading, stack[ text, source_refs ] }
7. Set "data_bindings" to {} — the backend fills it in.

""" + _FEW_SHOT_EXAMPLES


def compute_pattern_hash(query: str) -> str:
    tokens = re.sub(r"[^\w\s]", "", query.lower()).split()
    filtered = [t for t in tokens if t not in _STOPWORDS]
    normalized = " ".join(filtered)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _load_schema_validator():
    import jsonschema
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "ui_schema.json")
    with open(os.path.normpath(schema_path)) as f:
        schema = json.load(f)
    return schema, jsonschema.Draft7Validator(schema)


_schema_validator = None


def _get_validator():
    global _schema_validator
    if _schema_validator is None:
        _schema_validator = _load_schema_validator()
    return _schema_validator


def validate_ui_schema(obj: dict) -> None:
    """Raises jsonschema.ValidationError on failure."""
    import jsonschema
    _, validator = _get_validator()
    errors = list(validator.iter_errors(obj))
    if errors:
        raise jsonschema.ValidationError(
            f"{len(errors)} validation error(s): " + "; ".join(e.message for e in errors[:3])
        )


def build_fallback_schema(answer: str, sources: list[SourceRef]) -> dict:
    """Always-valid fallback schema — per spec Section 5.4 rule 6."""
    return {
        "version": "1.0",
        "title": "Query Result",
        "layout": {
            "type": "section",
            "heading": "Answer",
            "child": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {
                        "type": "component",
                        "component": "text",
                        "props": {"content_binding": "answer", "variant": "body"},
                    },
                    {
                        "type": "component",
                        "component": "source_refs",
                        "props": {"refs_binding": "sources"},
                    },
                ],
            },
        },
        "data_bindings": {
            "answer": answer,
            "sources": [s.model_dump() for s in sources],
        },
    }


def _detect_tabular_columns(sources: list[SourceRef]) -> list[dict] | None:
    """Try to infer table columns from the first JSON-array source chunk."""
    for s in sources:
        try:
            data = json.loads(s.text)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return [
                    {"key": k, "label": k.replace("_", " ").title(),
                     "type": "number" if isinstance(v, (int, float)) else "text"}
                    for k, v in list(data[0].items())[:8]
                ]
            if isinstance(data, dict):
                return [
                    {"key": k, "label": k.replace("_", " ").title(),
                     "type": "number" if isinstance(v, (int, float)) else "text"}
                    for k, v in list(data.items())[:8]
                ]
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _extract_table_rows(sources: list[SourceRef]) -> list[dict]:
    """Collect all JSON-parseable rows from sources."""
    rows: list[dict] = []
    for s in sources:
        try:
            data = json.loads(s.text)
            if isinstance(data, list):
                rows.extend(r for r in data if isinstance(r, dict))
            elif isinstance(data, dict):
                rows.append(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return rows


def build_heuristic_schema(query: str, answer: str, sources: list[SourceRef]) -> dict:
    """
    Choose a UI layout based on query keywords and source data shape.
    Used in local dev mode (no Bedrock). Always produces a valid schema.
    """
    q = query.lower()
    data_bindings: dict[str, Any] = {
        "answer": answer,
        "sources": [s.model_dump() for s in sources],
    }

    # --- Rich media: use the top-ranked source's type as the primary signal ---
    # Searching all of top-3 and applying a fixed priority order causes the wrong
    # viewer: e.g. a PDF at rank 2 would shadow a .py file at rank 1 because
    # pdf > code in the priority chain. Using sources[0] means the highest-scoring
    # result dictates the layout, which is what the user actually queried for.
    top = sources[0] if sources else None
    img  = top if (top and _is_image(top)) else None
    pdf  = top if (top and _is_pdf(top))   else None
    code = top if (top and _is_code(top))  else None
    aud  = top if (top and _is_audio(top)) else None

    if img:
        data_bindings["file_url"] = f"/jobs/{img.job_id}/file" if img.job_id else ""
        data_bindings["description"] = answer
        data_bindings["filename"] = img.source_ref
        return {
            "version": "1.0",
            "title": f"Image: {img.source_ref}",
            "layout": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {"type": "component", "component": "image_viewer", "props": {
                        "src_binding": "file_url",
                        "filename_binding": "filename",
                        "description_binding": "description",
                    }},
                    {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}},
                ],
            },
            "data_bindings": data_bindings,
        }

    if pdf:
        data_bindings["file_url"] = f"/jobs/{pdf.job_id}/file" if pdf.job_id else ""
        data_bindings["filename"] = pdf.source_ref
        data_bindings["explanation"] = answer
        return {
            "version": "1.0",
            "title": f"PDF: {pdf.source_ref}",
            "layout": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {"type": "component", "component": "text", "props": {
                        "content_binding": "explanation", "variant": "body",
                    }},
                    {"type": "component", "component": "pdf_viewer", "props": {
                        "src_binding": "file_url",
                        "filename_binding": "filename",
                    }},
                    {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}},
                ],
            },
            "data_bindings": data_bindings,
        }

    if code:
        lang = _EXT_TO_LANG.get(_file_ext(code.source_ref), "plaintext")
        code_sources = [s for s in sources if _is_code(s)]
        same_file = sorted(
            [cs for cs in code_sources if cs.source_ref == code.source_ref],
            key=lambda cs: cs.chunk_index,
        )
        data_bindings["code"] = "\n".join(cs.text for cs in same_file)
        data_bindings["language"] = lang
        data_bindings["filename"] = code.source_ref
        data_bindings["explanation"] = answer
        return {
            "version": "1.0",
            "title": f"Code: {code.source_ref}",
            "layout": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {"type": "component", "component": "text", "props": {
                        "content_binding": "explanation", "variant": "body",
                    }},
                    {"type": "component", "component": "code_editor", "props": {
                        "code_binding": "code",
                        "language": lang,
                        "filename_binding": "filename",
                    }},
                    {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}},
                ],
            },
            "data_bindings": data_bindings,
        }

    if aud:
        data_bindings["file_url"] = f"/jobs/{aud.job_id}/file" if aud.job_id else ""
        data_bindings["filename"] = aud.source_ref
        data_bindings["description"] = answer
        return {
            "version": "1.0",
            "title": f"Audio: {aud.source_ref}",
            "layout": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {"type": "component", "component": "audio_player", "props": {
                        "src_binding": "file_url",
                        "filename_binding": "filename",
                    }},
                    {"type": "component", "component": "text", "props": {
                        "content_binding": "description", "variant": "body",
                    }},
                    {"type": "component", "component": "source_refs", "props": {"refs_binding": "sources"}},
                ],
            },
            "data_bindings": data_bindings,
        }

    # --- Timeline: incident / event / when / log / history ---
    if any(w in q for w in ("incident", "event", "when", "log", "history", "occurred", "timeline")):
        events = []
        for s in sources:
            try:
                data = json.loads(s.text)
                rows = data if isinstance(data, list) else [data]
                for r in rows:
                    if isinstance(r, dict):
                        events.append({
                            "time": str(r.get("time", r.get("date", r.get("created_at", "")))),
                            "title": str(r.get("title", r.get("event", r.get("severity", "Event")))),
                            "description": str(r.get("description", r.get("details", ""))),
                        })
            except (json.JSONDecodeError, ValueError):
                pass
        data_bindings["events"] = events or [{"time": "", "title": answer[:60], "description": ""}]
        return {
            "version": "1.0",
            "title": "Incident Timeline",
            "layout": {
                "type": "section",
                "heading": "Events",
                "child": {
                    "type": "stack",
                    "direction": "vertical",
                    "children": [
                        {"type": "component", "component": "timeline",
                         "props": {"events_binding": "events"}},
                        {"type": "component", "component": "source_refs",
                         "props": {"refs_binding": "sources"}},
                    ],
                },
            },
            "data_bindings": data_bindings,
        }

    # --- Chart: trend / sales / revenue / over time / monthly ---
    if any(w in q for w in ("trend", "sales", "revenue", "over time", "monthly", "chart", "growth")):
        rows = _extract_table_rows(sources)
        data_bindings["data"] = rows
        # Pick x/y from first row's keys if available
        x_key, y_key = "month", "revenue"
        if rows and isinstance(rows[0], dict):
            keys = list(rows[0].keys())
            x_key = next((k for k in keys if k in ("month", "date", "time", "period", "year")), keys[0])
            y_key = next((k for k in keys if k not in (x_key,) and isinstance(rows[0][k], (int, float))), keys[-1])
        return {
            "version": "1.0",
            "title": "Trend",
            "layout": {
                "type": "stack",
                "direction": "vertical",
                "children": [
                    {"type": "component", "component": "chart",
                     "props": {"kind": "line", "x": x_key, "y": y_key, "data_binding": "data"}},
                    {"type": "component", "component": "source_refs",
                     "props": {"refs_binding": "sources"}},
                ],
            },
            "data_bindings": data_bindings,
        }

    # --- Table: list / show / employee / people / catalog ---
    if any(w in q for w in ("list", "show", "employee", "people", "staff", "product", "catalog", "table", "all")):
        columns = _detect_tabular_columns(sources)
        if columns:
            rows = _extract_table_rows(sources)
            data_bindings["rows"] = rows
            return {
                "version": "1.0",
                "title": "Results",
                "layout": {
                    "type": "stack",
                    "direction": "vertical",
                    "children": [
                        {"type": "component", "component": "kpi",
                         "props": {"label": "Total Records", "value": len(rows)}},
                        {"type": "component", "component": "table",
                         "props": {"columns": columns, "rows_binding": "rows"}},
                        {"type": "component", "component": "source_refs",
                         "props": {"refs_binding": "sources"}},
                    ],
                },
                "data_bindings": data_bindings,
            }

    # --- Default: prose text + source_refs ---
    return build_fallback_schema(answer, sources)


async def generate_ui_schema(
    query: str,
    answer: str,
    sources: list[SourceRef],
    ui_cache_store,
    settings: Settings,
    raw_data: Any = None,
) -> tuple[dict, bool]:
    """
    Generate a UI schema for this query result.
    Returns (schema, cache_hit).
    """
    pattern_hash = compute_pattern_hash(query)

    # 1. Check UICache
    cached = await ui_cache_store.get(pattern_hash)
    if cached:
        await ui_cache_store.increment_hit(pattern_hash)
        # Always rebuild layout from current sources — cached layout may not match
        # the content type of newly uploaded files.
        fresh = build_heuristic_schema(query, answer, sources)
        return fresh, True

    # 2. Local dev mode — use heuristic schema (no Bedrock)
    if settings.USE_LOCAL_STORE:
        schema = build_heuristic_schema(query, answer, sources)
        await ui_cache_store.put(pattern_hash, schema, sample_query=query)
        return schema, False

    # 3. Rich media — heuristic already produces the correct schema; skip Bedrock
    # (Bedrock is only told about "answer"/"sources" as available bindings, so it
    # can't reference file_url/code/filename and may generate wrong src_binding keys.)
    top = sources[0] if sources else None
    if top and (_is_image(top) or _is_pdf(top) or _is_code(top) or _is_audio(top)):
        schema = build_heuristic_schema(query, answer, sources)
        await ui_cache_store.put(pattern_hash, schema, sample_query=query)
        return schema, False

    # 4. Call Bedrock (prose / tabular queries only)
    data_bindings: dict[str, Any] = {
        "answer": answer,
        "sources": [s.model_dump() for s in sources],
    }
    if raw_data is not None:
        data_bindings["data"] = raw_data

    available_bindings = list(data_bindings.keys())
    user_prompt = (
        f"Query: {query}\n\n"
        f"Answer: {answer}\n\n"
        f"Available data_bindings keys: {available_bindings}\n\n"
        "Generate the UI schema JSON for this result."
    )

    try:
        raw_json = await _call_bedrock_ui(user_prompt, settings)
    except Exception as exc:
        logger.warning("Bedrock UI generation failed (%s) — using fallback", exc)
        schema = build_fallback_schema(answer, sources)
        await ui_cache_store.put(pattern_hash, schema, sample_query=query)
        return schema, False

    # 4. Parse + validate
    # Always build heuristic data_bindings (file_url, code, filename, etc.) so
    # Bedrock-generated layouts that reference those keys actually resolve.
    heuristic = build_heuristic_schema(query, answer, sources)
    rich_bindings = {**heuristic.get("data_bindings", {}), **data_bindings}

    schema: dict
    try:
        # Strip any accidental markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw_json).strip()
        schema = json.loads(clean)
        validate_ui_schema(schema)
        schema["data_bindings"] = rich_bindings
    except Exception as exc:
        logger.warning("UI schema invalid (%s) — using fallback", exc)
        schema = build_fallback_schema(answer, sources)
        schema["data_bindings"] = rich_bindings

    # 5. Cache and return
    await ui_cache_store.put(pattern_hash, schema, sample_query=query)
    return schema, False


async def generate_ui_schema_from_data(
    data: dict | list,
    intent: str | None,
    settings: Settings,
) -> dict:
    """POST /ui-schema endpoint — schema from arbitrary JSON, no retrieval."""
    if settings.USE_LOCAL_STORE:
        return {
            "version": "1.0",
            "title": intent or "Data View",
            "layout": {
                "type": "section",
                "heading": intent or "Data",
                "child": {
                    "type": "component",
                    "component": "text",
                    "props": {"content": str(data)[:500]},
                },
            },
            "data_bindings": {"data": data},
        }

    user_prompt = (
        f"Intent: {intent or 'display this data'}\n\n"
        f"Data (truncated): {json.dumps(data)[:2000]}\n\n"
        "Generate the UI schema JSON."
    )
    try:
        raw_json = await _call_bedrock_ui(user_prompt, settings)
    except Exception as exc:
        logger.warning("Bedrock UI generation failed (%s) — using fallback", exc)
        raw_json = ""
    try:
        clean = re.sub(r"```(?:json)?|```", "", raw_json).strip()
        schema = json.loads(clean)
        validate_ui_schema(schema)
        schema["data_bindings"] = {"data": data}
        return schema
    except Exception as exc:
        logger.warning("UI schema from data invalid (%s) — using fallback", exc)
        return {
            "version": "1.0",
            "title": intent or "Data View",
            "layout": {
                "type": "section",
                "heading": intent or "Data",
                "child": {
                    "type": "component",
                    "component": "text",
                    "props": {"content": str(data)[:500]},
                },
            },
            "data_bindings": {"data": data},
        }


async def _call_bedrock_ui(user_prompt: str, settings: Settings) -> str:
    import boto3
    client = boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION)
    resp = client.converse(
        modelId=settings.BEDROCK_ANSWER_MODEL,
        system=[{"text": _UI_SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 2048, "temperature": 0.0},
    )
    return resp["output"]["message"]["content"][0]["text"]
