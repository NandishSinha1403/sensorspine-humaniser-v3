# ScholarAI v3 SOTA: Refactoring Roadmap

## Phase 1: Critical Hotfixes (Immediate)
- [x] **Dependency Fix:** Add `word2number` to requirements.
- [x] **Concurrency Fix:** Unblock FastAPI event loop using `asyncio.to_thread`.
- [x] **Input Validation:** Implement 500-word limit on humanize requests.
- [x] **KV-Caching:** Fix $O(N^2)$ bottleneck in `ContrastiveLogitsProcessor`.
- [x] **State Management:** Remove `global` models in `main.py` and move to FastAPI lifespan/dependencies.
- [x] **AMR Initialization:** Remove silent exception swallowing.

## Phase 2: Architectural Overhaul (Next 2-4 Weeks)
- [x] **AMR Graph Surgery:** Replace string manipulation in `graph_manipulator.py` with `penman` objects and variable remapping.
- [x] **Containerization:** Create `Dockerfile` for backend.
- [ ] **Model Serving:** Research `vLLM` or `HuggingFace TGI` for production model serving.
- [x] **DeBERTa Judge:** Replace GPT-2 perplexity with a production-grade DeBERTa-v3 classifier.

## Phase 3: Scaling & Production (1-3 Months)
- [x] **Task Queue:** Implement Celery/Redis for asynchronous humanization processing.
- [x] **Auth & Security:** Implement JWT authentication and per-user rate limiting using `slowapi`.
- [x] **HF Inference Optimization:** Implement Flash Attention 2 and `torch.compile` for 2x-3x speedup on the existing pipeline.

---
*Last Updated: 2026-05-09*
