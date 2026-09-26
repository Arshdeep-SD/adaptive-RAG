# Local-First Migration Plan for adaptive-RAG

## Overview
Replace all AWS paid services (DynamoDB, S3, OpenSearch, Bedrock) with locally running alternatives.

---

## Current AWS Services Used

| Service | Location | Usage | Local Alternative |
|---------|----------|-------|-------------------|
| **DynamoDB** | `backend/db/dynamo.py` | User store, Job store, Record store, UI cache | SQLite (`sqlite_store.py`) |
| **S3** | `backend/storage/s3.py` | Object storage for data/files | Local filesystem (`local_fs.py`) |
| **OpenSearch** | `backend/search/opensearch.py` | Vector search with k-NN | FAISS (`faiss_local.py`) |
| **Bedrock** | `backend/embedding/bedrock_provider.py` | Embeddings, LLM inference, Vision | Ollama + SentenceTransformers |

---

## Migration Steps (Phased Approach)

### Phase 1: Database Layer (DynamoDB → SQLite)
- [ ] Create `backend/db/sqlite_store.py` with classes matching DynamoDB interface
- [ ] Update `backend/db/__init__.py` to conditionally import local or AWS stores
- [ ] Update config to use SQLite when `USE_LOCAL_STORE=True`
- [ ] Add migration script to convert existing data (if needed)

### Phase 2: Object Storage (S3 → Local Filesystem)
- [ ] Verify `backend/storage/local_fs.py` is complete and tested
- [ ] Update `backend/storage/__init__.py` to import local store by default
- [ ] Test file read/write operations

### Phase 3: Vector Search (OpenSearch → FAISS)
- [ ] Create `backend/search/faiss_local.py` with full FAISS integration
- [ ] Add vector database persistence using SQLite/FAISS
- [ ] Update config to use FAISS when `USE_LOCAL_STORE=True`
- [ ] Test vector search functionality

### Phase 4: Embedding Models (Bedrock → Local)
- [ ] Verify `backend/embedding/local_provider.py` works with SentenceTransformers
- [ ] Ensure Ollama is running and models are available
- [ ] Update embedding initialization in pipeline

### Phase 5: Integration & Configuration
- [ ] Update `core/config.py` environment variables
- [ ] Add `.env.example` template for local setup
- [ ] Create Docker Compose setup for all local services (SQLite, FAISS, Ollama)
- [ ] Update README with local deployment instructions

### Phase 6: Testing & Validation
- [ ] Run full test suite with local services
- [ ] Verify API endpoints work correctly
- [ ] Test vector search accuracy
- [ ] Check data persistence across restarts

---

## Local Services Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   SQLite     │◄───────►│   API Server  │              │
│  │   (Postgres) │    DB   │   (FastAPI)   │              │
│  └──────────────┘         └──────────────┘              │
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   FAISS      │◄───────►│   Vector Ret │              │
│  │    (Local)   │   Vec   │               │              │
│  └──────────────┘         └──────────────┘              │
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Ollama     │◄───────►│   LLM Ret    │              │
│  │  (Local LLM) │    Vec   │   Triever    │              │
│  └──────────────┘         └──────────────┘              │
│                                                           │
│  ┌──────────────┐                                         │
│  │  Local FS    │◄───────►│   File Store   │            │
│  │ (object store)│    Obj   │               │            │
│  └──────────────┘         └─────────────────┘            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Notes

1. **Thread Safety**: SQLite with WAL mode, use proper locking for concurrent access
2. **Data Persistence**: Use FAISS for vector indices, SQLite for metadata
3. **Backward Compatibility**: Keep AWS support for users transitioning gradually
4. **Graceful Degradation**: Local-first by default, AWS as optional backup

---

## Estimated Timeline

- Phase 1: 1 hour
- Phase 2: 30 mins
- Phase 3: 1.5 hours
- Phase 4: 1 hour
- Phase 5: 30 mins
- Phase 6: 1 hour (testing)

**Total: ~4 hours**

---

## Next Steps

1. Start with Phase 1 (SQLite database layer)
2. Test each phase before moving to next
3. Document any issues encountered