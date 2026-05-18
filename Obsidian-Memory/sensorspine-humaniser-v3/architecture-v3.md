# ScholarAI v3 SOTA: System Architecture (Post-Pitch Pivot)

## 1. High-Level Design
ScholarAI v3 SOTA is a distributed AI-humanization service. Following the May 11th emergency audit, the architecture was pivoted for maximum stability on T4 GPU hardware, moving away from experimental multimodal models to a high-performance, pure-text instruction-following engine.

## 2. Core Components

### A. FastAPI Gateway
- **Role:** Handles HTTP requests, JWT authentication, and task management.
- **Pitch Optimization:** Custom middleware injects `ngrok-skip-browser-warning: true` headers to ensure seamless frontend connection.

### B. Celery + Redis Task Queue
- **Role:** Decouples ML inference from the web tier. 
- **Stability Fix:** Workers are configured with `--concurrency=1` to prevent VRAM contention on T4 GPUs.

### C. Humanization Pipeline (The "Engine")
1. **AMR Structural Surgery (amrlib):**
   - Parses text into Abstract Meaning Representation (AMR) graphs.
   - Applies "Burstiness" via structural Fission/Fusion.
   - **Remapping:** Uses `penman` library to perform variable remapping.
2. **Qwen2 Generator (SOTA Pivot):**
   - **Model:** `Qwen/Qwen2-7B-Instruct` (Pivoted from Gemma-4 and Llama-3 for stability/non-gated access).
   - **Quantization:** 4-bit NF4 with CPU offloading enabled.
   - **Attention:** Hardcoded to `SDPA` (Scaled Dot Product Attention). `Flash Attention` and `torch.compile` were removed to prevent attribute-level attribute errors (`len()` mismatch).
   - **Sampling:** Dynamic scaling of `temperature` (0.8-1.2) and `top_p` (0.9-0.95) based on user-defined `intensity`.

### D. Diagnostic Judge (DeBERTa-v3)
- **Role:** Discriminative AI detection classifier.
- **Model:** `cross-encoder/nli-deberta-v3-small` (Safetensors).
- **Placement:** Runs on **CPU** to preserve GPU VRAM for the Qwen2 model.

### E. Deep Humanization Training (Phase 3 Evolution)
- **Corpus:** 1M+ tokens of pre-AI (2000-2015) prestigious academic prose.
- **Base Model:** `Qwen/Qwen2-7B-Instruct` (Quantized).
- **Stage 1 (CLM):** Adapts the model's innate token prediction to human academic syntax.
- **Stage 2 (DPO):** Uses the Diagnostic Judge to penalize AI-like statistical traits in a preference-learning loop.
- **Decoupled Architecture:** To prevent DDP barrier timeouts (600s), dataset generation was moved to a standalone single-GPU script (`generate_dpo_data.py`). Multi-GPU training only commences after the dataset is verified on disk.

## 3. Infrastructure & Deployment
- **Target:** Google Colab T4 (15GB VRAM).
- **Environment:** CUDA 12.1 with pinned `numpy<2.1` and `pillow<12.0` to satisfy implicit multimodal dependency requirements in the `transformers` loader.
- **Networking:** `ngrok` tunnel with specialized frontend headers.
