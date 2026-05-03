# ScholarAI v3 SOTA: Roadmap

## Phase 1: Foundation (The Clean Slate)
- [x] Initialize brand new repository.
- [x] Set up `environment.yml` / `requirements.txt` with PyTorch, Transformers, and AMRLib.
- [x] Establish basic FastAPI skeleton.

## Phase 2: Semantic Graph Engine
- [x] Implement AMR parsing module.
- [x] Develop "Graph Fusion" logic (GraphManipulator).
- [x] Verify semantic preservation across graph-to-text cycles.

## Phase 3: Contrastive Decoding (The SOTA Core)
- [x] Load Llama-3 8B and base GPT-2 models via HuggingFace (optimized for T4 GPU).
- [x] Implement custom LogitsProcessor for token-level AI penalization.
- [x] Benchmark against Turnitin/GPTZero to calibrate penalty weights.

## Phase 4: Integration & Dashboard
- [x] Connect the v3 engine to the Next.js frontend.
- [x] Implement side-by-side "AI vs v3-Human" comparison metrics.
- [ ] Stabilize AMR model deployment on Colab (Fixing 404 links).

---
Related: [[context]], [[architecture-v3]]