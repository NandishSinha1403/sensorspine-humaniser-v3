# ScholarAI v3 SOTA: System Architecture

## 1. High-Level Design
ScholarAI v3 SOTA is a distributed AI-humanization service designed to bypass state-of-the-art AI detectors. It uses a multi-layered approach involving structural graph manipulation (AMR) and token-level contrastive decoding.

## 2. Core Components

### A. FastAPI Gateway
- **Role:** Handles HTTP requests, authentication, and task management.
- **Security:** JWT-based Bearer authentication and `slowapi` rate limiting.
- **Async Pattern:** Returns `task_id` immediately; clients poll for results.

### B. Celery + Redis Task Queue
- **Role:** Decouples long-running ML inference (5-20s) from the web tier.
- **Worker:** A persistent background process that maintains model weights in VRAM.

### C. Humanization Pipeline (The "Engine")
1. **AMR Structural Surgery:**
   - Parses text into Abstract Meaning Representation (AMR) graphs using BART/T5.
   - Applies "Burstiness" via structural Fission/Fusion.
   - **Remapping:** Uses `penman` library to perform variable remapping, preventing variable name collisions during graph merge.
   - **Generation:** Converts modified graphs back to natural language.
2. **Contrastive Decoding (Gemma 4B + GPT-2):**
   - **Generator:** Gemma 4 E4B (Quantized 4-bit).
   - **Base:** GPT-2 (serving as the "AI-predictability" baseline).
   - **Logic:** Penalizes tokens that are highly predictable by the base model.
   - **Optimization:** KV-Caching implementation ($O(1)$ complexity) and Flash Attention 2.

### D. Diagnostic Judge (DeBERTa-v3)
- **Role:** Discriminative AI detection classifier.
- **Placement:** Runs on **CPU** to save GPU VRAM for the main LLMs.
- **Loop:** Provides a feedback signal for recursive refinement of humanized text.

## 3. Infrastructure & Deployment
- **Containerization:** Docker with CUDA 12.1 runtime support.
- **Optimization:** `torch.compile` for base model forward passes.
- **Memory Management:** 4-bit quantization with CPU offloading enabled to fit on 15GB T4 GPUs.
