# ScholarAI v3 SOTA: Deployment & Usage Guide

Follow these steps to run the production-grade, async, and secure backend on Google Colab.

---

## Step 1: Push Latest Code (Mac Terminal)
Run these commands in your local terminal to ensure Colab pulls the latest changes.

```bash
cd /Users/am_nandish/Documents/sensorspine-humaniser-3
git add .
git commit -m "Production-grade async backend with JWT and Flash Attention"
git push
```

---

## Step 2: Google Colab Setup (Cell 1)
Paste and run this to install dependencies and download AMR models.

```python
# 1. Reset & Install
%cd /content
!rm -rf sensorspine-humaniser-v3
!pip install --upgrade amrlib fastapi uvicorn pydantic torch accelerate bitsandbytes python-multipart pyngrok penman unidecode huggingface_hub sentencepiece protobuf word2number celery redis flash-attn python-jose[cryptography] passlib[bcrypt] slowapi
!pip install git+https://github.com/huggingface/transformers.git

# 2. HuggingFace Login
from google.colab import userdata
from huggingface_hub import login
login(token=userdata.get('HF_TOKEN'))

# 3. Clone & Download Models
!git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
%cd sensorspine-humaniser-v3/backend
!mkdir -p models
!wget https://github.com/bjascob/amrlib-models/releases/download/parse_xfm_bart_base-v0_1_0/model_parse_xfm_bart_base-v0_1_0.tar.gz -O models/stog.tar.gz
!tar -xzf models/stog.tar.gz -C models/ && mv models/model_parse_xfm_bart_base-v0_1_0 models/model_stog
!wget https://github.com/bjascob/amrlib-models/releases/download/model_generate_t5wtense-v0_1_0/model_generate_t5wtense-v0_1_0.tar.gz -O models/gtos.tar.gz
!tar -xzf models/gtos.tar.gz -C models/ && mv models/model_generate_t5wtense-v0_1_0 models/model_gtos
```

---

## Step 3: Start the Backend (Cell 2)
This starts the Redis broker, the Celery Worker, and the FastAPI server.

```python
from google.colab import userdata
from pyngrok import ngrok
import os

# 1. Set up Tunnel
NGROK_TOKEN = userdata.get('NGROK_TOKEN')
ngrok.set_auth_token(NGROK_TOKEN)
public_url = ngrok.connect(8000).public_url
print(f"🚀 BACKEND API URL: {public_url}")

# 2. Start Services
# This runs the specialized start script we created
!chmod +x start.sh
!./start.sh
```

---

## Step 4: How to Use the API (Frontend/Postman)

Because the system is now **Secure** and **Async**, you must follow this 3-step flow:

### 1. Get an Access Token
**POST** to `{URL}/token`
*Returns:* `{"access_token": "...", "token_type": "bearer"}`

### 2. Submit Text for Humanization
**POST** to `{URL}/humanize`
*Header:* `Authorization: Bearer <YOUR_TOKEN>`
*Body:* `{"text": "Your text here", "intensity": 1.0}`
*Returns:* `{"task_id": "xxxx-xxxx", "status": "pending"}`

### 3. Check Progress
**GET** to `{URL}/status/xxxx-xxxx`
*Header:* `Authorization: Bearer <YOUR_TOKEN>`
*Returns:* The final humanized text once `status` is `completed`.

---

## Production Notes
- **VRAM:** The system uses 4-bit quantization and CPU offloading to fit Gemma 4B on the T4.
- **Speed:** The first request may take 20s as models "warm up". Subsequent requests will be 2x faster due to Flash Attention and KV-Caching.
- **Concurrency:** The system handles multiple requests by queuing them. No more "Internal Server Errors" during concurrent hits.
