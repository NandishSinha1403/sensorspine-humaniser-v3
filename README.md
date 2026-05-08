# ScholarAI v3 SOTA: Deep Semantic Evasion Humanizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Frontend-Next.js%2015-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

**ScholarAI v3 SOTA** is a production-grade text humanization engine designed to bypass state-of-the-art AI detectors (GPTZero, Originality.ai, Turnitin) through **Deep Semantic Evasion**. 

Unlike traditional "paraphrasers" that rely on synonym swapping or regex-based jitter, v3 employs a multi-layered linguistic surgery pipeline that reconstructs text from its core semantic representation.

---

## 🧠 The "Deep Semantic Evasion" Philosophy

Modern AI detectors look for statistical predictability (low perplexity) and rigid syntactic structures. ScholarAI v3 breaks this "AI DNA" using three core pillars:

1.  **AMR Structural Surgery:** Text is parsed into **Abstract Meaning Representation (AMR)** graphs—a language-agnostic representation of "who is doing what to whom." By performing graph-level fission (splitting) and fusion (merging), we rebuild the sentence's DNA from scratch.
2.  **Contrastive Decoding (Gemma 4 E4B + GPT-2):** We use a dual-model generation strategy. A SOTA generator (Gemma) produces text while a base model (GPT-2) identifies "AI-predictable" tokens. The generator is mathematically penalized for choosing tokens the base model predicts, forcing it into the "human tail" of probability distributions.
3.  **Diagnostic Feedback Loop:** A **DeBERTa-v3** classifier acts as an internal judge, scoring the output's "humanity" in real-time and triggering recursive refinement if the evasion threshold isn't met.

---

## 🛠️ Technical Architecture

### **Backend (Python / FastAPI / Celery)**
*   **Engine:** PyTorch-based inference using `transformers`, `accelerate`, and `bitsandbytes`.
*   **Asynchronous Processing:** Celery + Redis task queue handles long-running (10-30s) ML tasks without blocking the gateway.
*   **Quantization:** 4-bit NF4 quantization with CPU offloading allows large models to run on 15GB T4 GPUs.
*   **Optimizations:** Flash Attention 2, KV-Caching ($O(1)$ complexity), and `torch.compile` for 3x inference speedups.
*   **Security:** JWT-based Bearer authentication and `slowapi` rate limiting.

### **Frontend (TypeScript / Next.js 15)**
*   **Modern UI:** A clean, dark-mode dashboard built with Tailwind CSS and Framer Motion.
*   **Reactive Polling:** Automatic JWT handling and real-time status polling for the asynchronous backend.
*   **Streaming Logs:** Visual feedback of the AMR surgery and refinement steps.

---

## 🚀 Deployment Guide

### **Cloud Backend (Google Colab / T4 GPU)**
The backend is optimized for Google Colab to provide free access to high-end GPUs.

1.  **Clone & Setup:**
    ```python
    !git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
    %cd sensorspine-humaniser-v3/backend
    !chmod +x start.sh
    # Follow DEPLOYMENT_GUIDE.md for full setup cells
    ```
2.  **Orchestration:** Run `./start.sh` to launch Redis, the Celery Worker, and the FastAPI Gateway in a unified environment.
3.  **Tunneling:** Use `ngrok` to expose port 8000 to the public internet.

### **Local Frontend (Next.js)**
1.  **Install:** `cd frontend && npm install`
2.  **Launch:** `npm run dev`
3.  **Connect:** Paste your ngrok URL into the "Backend URL" field on the dashboard.

---

## 📊 API Specification

### `POST /token`
Fetch a temporary JWT access token.
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** (Empty)

### `POST /humanize`
Submit text for semantic evasion.
- **Auth:** `Bearer <JWT_TOKEN>`
- **Body:** `{"text": "...", "intensity": 1.0}`

### `GET /status/{task_id}`
Poll for task completion and diagnostic results.
- **Auth:** `Bearer <JWT_TOKEN>`

---

## ⚖️ License & Disclaimer

This project is licensed under the MIT License. 

**Disclaimer:** This tool is intended for research and educational purposes in the field of Natural Language Processing (NLP). The authors do not condone the use of this tool for academic dishonesty or the violation of any institution's terms of service. Use responsibly.

---
*Developed by the ScholarAI Team*
