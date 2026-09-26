"""SQLite-based local database store for adaptive-RAG."""


from __future__ import annotations
import json, os
from datetime import datetime, timezone
import sqlite3

def _now_iso():
    return datetime.now(timezone.utc).isoformat()
