# ScholarAI v3 SOTA: Deployment & Usage Guide

Follow these steps to run the production-grade, async, and secure backend on Google Colab (T4 GPU).

---

## Step 1: Sync Latest Code (Mac Terminal)
Run these commands in your local terminal before starting Colab to ensure you have the latest orchestration scripts and model paths.

```bash
cd /Users/am_nandish/Documents/sensorspine-humaniser-3
git add .
git commit -m "Final production sync: start.sh and frontend auth fixes"
git push
```

---

## Step 2: Google Colab Setup (Cell 1)
Paste and run this to install dependencies and download the AMR models into the correct directory structure.

```python
# 1. Reset & Install Core Dependencies
%cd /content
!rm -rf sensorspine-humaniser-v3
!pip install --upgrade amrlib fastapi uvicorn pydantic torch accelerate bitsandbytes python-multipart pyngrok penman unidecode huggingface_hub sentencepiece protobuf word2number celery redis flash-attn python-jose[cryptography] passlib[bcrypt] slowapi
!pip install git+https://github.com/huggingface/transformers.git

# 2. HuggingFace Login (Using Colab Secrets)
from google.colab import userdata
from huggingface_hub import login
try:
    HF_TOKEN = userdata.get('HF_TOKEN')
    login(token=HF_TOKEN)
except Exception:
    print("ERROR: HF_TOKEN not found in Colab Secrets (the Key icon).")

# 3. Clone Repository
!git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
%cd sensorspine-humaniser-v3/backend

# 4. Manual Model Download (Verified Links for amrlib v0.8.1)
print("Downloading SOTA AMR models...")
!mkdir -p models

# Download STOG Model (Parsing)
!wget --show-progress https://github.com/bjascob/amrlib-models/releases/download/parse_xfm_bart_base-v0_1_0/model_parse_xfm_bart_base-v0_1_0.tar.gz
!tar -xzf model_parse_xfm_bart_base-v0_1_0.tar.gz -C models/
!rm model_parse_xfm_bart_base-v0_1_0.tar.gz
!mv models/model_parse_xfm_bart_base-v0_1_0 models/model_stog

# Download GTOS Model (Generation)
!wget --show-progress https://github.com/bjascob/amrlib-models/releases/download/model_generate_t5wtense-v0_1_0/model_generate_t5wtense-v0_1_0.tar.gz
!tar -xzf model_generate_t5wtense-v0_1_0.tar.gz -C models/
!rm model_generate_t5wtense-v0_1_0.tar.gz
!mv models/model_generate_t5wtense-v0_1_0 models/model_gtos

print("✅ Setup Complete! Models are ready.")
```

---

## Step 3: Start the Backend (Cell 2)
This establishes the ngrok tunnel and launches the unified orchestration script.

```python
from google.colab import userdata
from pyngrok import ngrok

# 1. Set up Tunnel
NGROK_TOKEN = userdata.get('NGROK_TOKEN')
ngrok.set_auth_token(NGROK_TOKEN)
public_url = ngrok.connect(8000).public_url
print(f"🚀 BACKEND API URL: {public_url}")

# 2. Start Services (Redis + Celery + FastAPI)
# All logs (Inference + API) will stream below.
!chmod +x start.sh
!./start.sh
```

---

## Step 4: Secure Async API Workflow

The system is now **Secure (JWT)** and **Asynchronous (Task Queue)**.

### 1. Fetch JWT Token
**POST** to `{URL}/token`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** (Empty)
- **Returns:** `{"access_token": "...", "token_type": "bearer"}`

### 2. Submit Task
**POST** to `{URL}/humanize`
- **Header:** `Authorization: Bearer <TOKEN>`
- **Body:** `{"text": "AI text here", "intensity": 1.0}`
- **Returns:** `{"task_id": "...", "status": "pending"}`

### 3. Poll for Results
**GET** to `{URL}/status/{task_id}`
- **Header:** `Authorization: Bearer <TOKEN>`
- **Returns:** Final result when `status == "completed"`.

---

## Production Notes (T4 Optimized)
- **VRAM:** Uses 4-bit NF4 quantization with CPU offloading for Gemma 4B.
- **Speed:** Accelerated via **Flash Attention 2**. 
- **Queueing:** Handled by Celery/Redis; ensures single-GPU safety and prevents 500 errors under load.
