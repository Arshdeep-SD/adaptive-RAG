#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDS=()

cleanup() {
  echo ""
  echo "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# ── Prerequisites ────────────────────────────────────────────────
check() {
  command -v "$1" &>/dev/null || { echo "ERROR: '$1' not found. Install it and retry."; exit 1; }
}
check ollama
check uvicorn
check npm

# ── Ollama ───────────────────────────────────────────────────────
if ! pgrep -x ollama &>/dev/null; then
  echo "Starting Ollama..."
  ollama serve &>/dev/null &
  PIDS+=($!)
  sleep 2
else
  echo "Ollama already running."
fi

# Pull models if missing (non-blocking output)
ollama list | grep -q "llama3.2" || { echo "Pulling llama3.2 (~2 GB)..."; ollama pull llama3.2; }
ollama list | grep -q "llava"    || { echo "Pulling llava (~4 GB, optional vision model)..."; ollama pull llava || echo "llava pull failed — images will use metadata only."; }

# ── Backend ──────────────────────────────────────────────────────
echo "Starting backend on http://localhost:8000 ..."
cd "$ROOT"
USE_LOCAL_STORE=true EMBEDDING_PROVIDER=local \
  uvicorn backend.api.main:app --reload --port 8000 \
  > "$ROOT/logs/backend.log" 2>&1 &
PIDS+=($!)

# Wait for backend to be ready
mkdir -p "$ROOT/logs"
echo -n "Waiting for backend"
for i in $(seq 1 30); do
  curl -s http://localhost:8000/health &>/dev/null && break
  echo -n "."
  sleep 1
done
echo ""

# ── Frontend ─────────────────────────────────────────────────────
echo "Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev > "$ROOT/logs/frontend.log" 2>&1 &
PIDS+=($!)

# ── Ready ────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  App:     http://localhost:5173"
echo "  API:     http://localhost:8000"
echo "  Login:   admin / changeme"
echo "  Logs:    logs/backend.log  logs/frontend.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Press Ctrl+C to stop all servers."
echo ""

wait
