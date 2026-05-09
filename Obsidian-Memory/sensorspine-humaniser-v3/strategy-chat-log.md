a# Strategy Log: The Pivot to v3 SOTA

## The Decision (2026-05-03)
During the v2.2 maintenance phase, we identified that heuristic, rule-based evasion (spaCy inversions, Unicode jitter) was increasingly vulnerable to enterprise-grade statistical detectors. 

### The Critique of v2.2
*   **Unicode Tricks**: Brittle and easily stripped by detectors.
*   **Rule-Based Inversion**: Creates "Frankenstein" sentences that feel unnatural to human reviewers.
*   **Static DNA**: Simple bigram/trigram models can't capture the deep semantic flow of modern scholarship.

### The v3 Vision
We decided to build a brand new project from scratch, moving away from "fixing AI text" to **"regenerating human text from AI concepts."** This requires a clean-slate repository built on PyTorch and HuggingFace, focusing on Contrastive Decoding and Semantic Graph Fusion.

---
## Current State: May 4, 2026 - 01:00 AM
**Status:** Implementation complete, deployment in progress.
**Key Issues Resolved:**
- **CORS:** Added middleware to `main.py` to allow the Next.js frontend to talk to the ngrok tunnel.
- **Colab Sync:** Optimized `backend_runner.ipynb` and `change.txt` for clean clones and module discovery.
- **AMR Models:** Fixed 404 links for STOG/GTOS models in `change.txt` and updated `amr_handler.py` to recognize new folder names.

---
## Current State: May 9, 2026 - 03:00 AM
**Status:** Production-Ready Architecture Finalized.
**Key Issues Resolved:**
- **Secure Async Frontend:** Refactored `page.tsx` to auto-fetch JWT tokens and poll the `/status` endpoint, providing real-time feedback to the user.
- **Auth Compatibility:** Fixed `/token` request to use `application/x-www-form-urlencoded` to match FastAPI/OAuth2 standards.
- **Orchestration Script:** Created `backend/start.sh` to unified Redis, Celery, and FastAPI startup.
- **Documentation Overhaul:** Rewrote `README.md` and `DEPLOYMENT_GUIDE.md` to professional standards with verified model links.

---
## Current State: May 10, 2026 - 12:30 AM
**Status: Architectural Pivot to Single-Model Aggressive Paraphrasing.**
**Root Cause Audit & Decision:**
- **The Bug:** CUDA device-side asserts triggered due to vocabulary mismatches during Contrastive Decoding (CD).
- **The Problem:** GPT-2 (50k vocab) cannot be subtracted from Gemma-4 (256k vocab) in a tight loop. Mapping via string projection introduced 60s+ latency overhead (10k+ tokenizer roundtrips).
- **The Pivot:** Dropped GPT-2 base model entirely. Substituted CD with **Aggressive Sampling parameters** scaled by `intensity`.
- **New Formula:** `temp = 1.1 + (0.5 * intensity)`, `top_p = 0.90 + (0.05 * intensity)`.
- **Outcome:** Fixed CUDA crashes, reduced VRAM usage by ~1.5GB, and achieved near-instant generation latency.
- **Model Fix:** Switched Diagnostic Judge to `cross-encoder/nli-deberta-v3-small` (Safetensors) to bypass unpatchable `torch.load` version block in `transformers`.

**Files Created/Modified:**
- `backend/engine/humanizer_engine.py` (Renamed from `contrastive_decoder.py` + refactored)
- `backend/engine/amr_handler.py` (Surgical root-cause patch for `torch.load`)
- `backend/engine/diagnostic_judge.py` (Safetensors migration)
- `Obsidian-Memory/sensorspine-humaniser-v3/architecture-v3.md` (Updated)

Related: [[context]], [[architecture-v3]], [[troubleshooting-v3]]