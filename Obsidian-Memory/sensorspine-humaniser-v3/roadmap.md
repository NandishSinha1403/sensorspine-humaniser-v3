# ScholarAI v3 SOTA: Roadmap

## Phase 1: Foundation (The Clean Slate)
- [ ] Initialize brand new repository.
- [ ] Set up `environment.yml` / `requirements.txt` with PyTorch, Transformers, and AMRLib.
- [ ] Establish basic FastAPI skeleton.

## Phase 2: Semantic Graph Engine
- [ ] Implement AMR parsing module.
- [ ] Develop "Graph Fusion" logic to merge concepts for complex sentence generation.
- [ ] Verify semantic preservation across graph-to-text cycles.

## Phase 3: Contrastive Decoding (The SOTA Core)
- [ ] Load Llama-3 8B and base GPT-2 models via HuggingFace.
- [ ] Implement custom LogitsProcessor for token-level AI penalization.
- [ ] Benchmark against Turnitin/GPTZero to calibrate penalty weights.

## Phase 4: Integration & Dashboard
- [ ] Connect the v3 engine to the Next.js frontend.
- [ ] Implement side-by-side "AI vs v3-Human" comparison metrics.

---
Related: [[context]], [[architecture-v3]]