# Strategy Log: The Pivot to v3 SOTA

... (previous logs) ...

---
## Current State: May 11, 2026 - 01:30 AM (Pre-Pitch Emergency Fixes)
**Status:** Pitch-Ready stability achieved.

### 1 AM Audit & Crisis Management:
- **Environment Crisis:** Identified a critical CUDA major version mismatch (13.0 vs 12.8) in Colab that was crashing the `torchvision` pipeline.
- **Model Pivot:** Attempted a pivot to Llama-3 8B, which hit a gating wall (403 errors). 
- **Final Pivot (Qwen2):** Successfully migrated the engine to **Qwen2-7B-Instruct**. This model is non-gated, ultra-high performance (SOTA in the 7B class), and highly stable on T4 GPUs.
- **Optimization Audit:** Removed `torch.compile` and `Flash Attention` to eliminate attribute-level crashes (`len()` and `BatchEncoding` errors).
- **Communication Bridge:** Fixed a major bug in the frontend where ngrok's interstitial warning page was blocking JSON API calls. Injected `ngrok-skip-browser-warning` across the stack.

### Outcomes:
- [x] Verified full end-to-end inference on complex medical text (Arthroscopy).
- [x] Consolidated Colab launch logic into a single "Emergency Reset" cell.
- [x] Created `HOW-TO-RUN.md` for simplified operation during the pitch.

**Pitch Strategy:** Use **Qwen2-7B-Instruct** with Intensity **0.6-0.8** for clinical demos. The system now demonstrates high semantic retention with varied linguistic structures.

Related: [[context]], [[architecture-v3]], [[troubleshooting-v3]]
