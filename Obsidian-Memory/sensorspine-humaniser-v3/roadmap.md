# ScholarAI v3 SOTA: Refactoring Roadmap

## Phase 1: Critical Hotfixes (Immediate)
- [x] **Dependency Fix:** Add `word2number` to requirements.
- [x] **Concurrency Fix:** Unblock FastAPI event loop using `asyncio.to_thread`.
- [x] **Input Validation:** Implement 500-word limit on humanize requests.
- [x] **KV-Caching:** Fix $O(N^2)$ bottleneck in `ContrastiveLogitsProcessor`.
- [x] **State Management:** Remove `global` models in `main.py` and move to FastAPI lifespan/dependencies.
- [x] **AMR Initialization:** Remove silent exception swallowing.

## Phase 2: Architectural Overhaul (Complete)
- [x] **AMR Graph Surgery:** Replace string manipulation in `graph_manipulator.py` with `penman` objects and variable remapping.
- [x] **Containerization:** Create `Dockerfile` for backend.
- [x] **DeBERTa Judge:** Migrated to Safetensors to bypass security version blocks.
- [x] **Single-Model Pivot:** Dropped GPT-2 base model to resolve tokenizer mismatches and CUDA asserts.

## Phase 3: Scaling & Production (1-3 Months)
- [x] **Task Queue:** Implement Celery/Redis for asynchronous humanization processing.
- [x] **Auth & Security:** Implement JWT authentication and per-user rate limiting using `slowapi`.
- [x] **HF Inference Optimization:** Implement Flash Attention 2 (SDPA fallback) and `torch.compile` for speedup.
- [x] **Prompt Engineering:** Implemented strict Chat Templates to prevent prompt leakage and gibberish loops.

---
*Last Updated: 2026-05-10*
