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

## Phase 3: Deep Humanization Training (Complete)
- [x] **Pre-AI Corpus Acquisition:** 500/500 prestigious research papers (2000-2015) downloaded. Expanded topics to 50+ domains for maximum generalization.
- [x] **Data Preprocessing:** 500/500 papers surgically cleaned and ready for training.
- [x] **Phase 3 CLM Fine-Tuning:** Executed `fine_tune_clm.py` on the complete 500-paper corpus to shift model distribution.
- [x] **Phase 4 Detector Penalization:** Executed `fine_tune_dpo.py` using DeBERTa judge for active AI-trait penalization.
- [x] **Persistence Fix:** Decoupled DPO generation from DDP training to prevent sync timeouts on Kaggle T4 x2.

## Phase 4: Scaling & Production (Current)
- [ ] **GPU Load Balancing:** Scaling to multiple T4 workers.
- [ ] **Feedback Loop:** Implementing real-time human evaluation of judge accuracy.
- [ ] **Mobile Interface:** Responsive Next.js UI for mobile demos.

---
*Last Updated: 2026-05-18*
