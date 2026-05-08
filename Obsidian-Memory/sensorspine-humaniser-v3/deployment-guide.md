# ScholarAI v3 SOTA: Deployment & Usage Guide

## 1. Local Code Push (Mac Terminal)
```bash
cd /Users/am_nandish/Documents/sensorspine-humaniser-3
git add .
git commit -m "Production-grade async backend with JWT and Flash Attention"
git push
```

## 2. Google Colab Setup (Execution Environment)
### Cell 1: Environment & Dependencies
```python
%cd /content
!rm -rf sensorspine-humaniser-v3
!pip install --upgrade amrlib fastapi uvicorn pydantic torch accelerate bitsandbytes python-multipart pyngrok penman unidecode huggingface_hub sentencepiece protobuf word2number celery redis flash-attn python-jose[cryptography] passlib[bcrypt] slowapi
!pip install git+https://github.com/huggingface/transformers.git

from google.colab import userdata
from huggingface_hub import login
login(token=userdata.get('HF_TOKEN'))

!git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
%cd sensorspine-humaniser-v3/backend
!mkdir -p models
!wget https://github.com/bjascob/amrlib-models/releases/download/parse_xfm_bart_base-v0_1_0/model_parse_xfm_bart_base-v0_1_0.tar.gz -O models/stog.tar.gz
!tar -xzf models/stog.tar.gz -C models/ && mv models/model_parse_xfm_bart_base-v0_1_0 models/model_stog
!wget https://github.com/bjascob/amrlib-models/releases/download/model_generate_t5wtense-v0_1_0/model_generate_t5wtense-v0_1_0.tar.gz -O models/gtos.tar.gz
!tar -xzf models/gtos.tar.gz -C models/ && mv models/model_generate_t5wtense-v0_1_0 models/model_gtos
```

### Cell 2: Service Orchestration
```python
from google.colab import userdata
from pyngrok import ngrok
import os

NGROK_TOKEN = userdata.get('NGROK_TOKEN')
ngrok.set_auth_token(NGROK_TOKEN)
public_url = ngrok.connect(8000).public_url
print(f"🚀 BACKEND API URL: {public_url}")

!chmod +x start.sh
!./start.sh
```

## 3. Production API Workflow
1. **Auth:** Fetch JWT from `/token`.
2. **Submit:** POST to `/humanize` with Bearer token.
3. **Poll:** GET status from `/status/{task_id}` until `status == "completed"`.

## 4. Hardware Constraints (T4 Optimization)
- **VRAM Management:** Uses NF4 quantization + CPU offloading.
- **Inference Speed:** Accelerated via Flash Attention 2 and `torch.compile`.
- **Concurrency:** Managed by Celery task queue (single-worker mode for GPU safety).
