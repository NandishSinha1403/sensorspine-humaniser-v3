# ScholarAI v3 SOTA: Refactoring Roadmap

## Phase 1: Critical Hotfixes (Complete)
- [x] **Dependency Fix:** Add `word2number` and pin `numpy`/`pillow`.
- [x] **Concurrency Fix:** Unblock FastAPI event loop using `asyncio.to_thread`.
- [x] **Input Validation:** Implement 3000-char limit on humanize requests.
- [x] **KV-Caching:** Fix $O(N^2)$ bottleneck.
- [x] **State Management:** Remove `global` models and use worker state persistence.
- [x] **CUDA Stability:** Resolved major version mismatch between PyTorch and torchvision.

## Phase 2: Architectural Overhaul (Complete)
- [x] **AMR Graph Surgery:** Implemented `penman` objects and variable remapping for collision-free graph fusion.
- [x] **Model Pivot:** Migrated from Gemma-4 -> Llama-3 -> **Qwen2-7B-Instruct** for pitch stability and non-gated access.
- [x] **DeBERTa Judge:** Migrated to Safetensors and CPU placement.
- [x] **Frontend Bridge:** Implemented `ngrok-skip-browser-warning` across frontend and backend.

## Phase 3: Scaling & Production (1-3 Months)
- [ ] **Multi-User Auth:** Replace mock JWT with real DB authentication.
- [ ] **GPU Load Balancing:** Scaling to multiple T4 workers.
- [ ] **Feedback Loop:** Implementing real-time human evaluation of judge accuracy.
- [ ] **Mobile Interface:** Responsive Next.js UI for mobile demos.

---
*Last Updated: 2026-05-11 (Pitch Prep Session)*
