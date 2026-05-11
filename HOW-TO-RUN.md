# 🚀 ScholarAI v3 SOTA: Quick Start Guide (Pitch Ready)

This guide contains the exact steps to launch the **Deep Semantic Evasion** pipeline for your pitch.

---

## 1. Cloud Backend Setup (Google Colab)

The backend runs on a T4 GPU to handle the heavy AI humanization.

### **Step A: Preparation**
1.  Open [Google Colab](https://colab.research.google.com/).
2.  Set Runtime to **T4 GPU** (`Runtime > Change runtime type > T4 GPU`).
3.  Add **Secrets** (Key icon 🔑):
    *   `HF_TOKEN`: Your HuggingFace Token.
    *   `NGROK_TOKEN`: Your ngrok Authtoken.
    *   **Toggle "Notebook access" to ON for both.**

### **Step B: Execution (Setup Cell)**
Paste and run this in the first cell to install dependencies and models:
```python
# 1. Environment Setup (CUDA 12.1 Stable)
%cd /content
!rm -rf sensorspine-humaniser-v3
!apt-get install -y redis-server > /dev/null
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
!pip install --upgrade amrlib fastapi uvicorn "pydantic<=2.12.3" accelerate bitsandbytes python-multipart pyngrok penman unidecode huggingface_hub sentencepiece protobuf word2number celery redis python-jose[cryptography] passlib[bcrypt] slowapi "numpy<2.1" "pillow<12.0"
!pip install git+https://github.com/huggingface/transformers.git

# 2. Auth & Clone
from google.colab import userdata
from huggingface_hub import login
login(token=userdata.get('HF_TOKEN'))
!git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
%cd sensorspine-humaniser-v3/backend

# 3. Download AMR Models
!mkdir -p models
!wget -q --show-progress https://github.com/bjascob/amrlib-models/releases/download/parse_xfm_bart_base-v0_1_0/model_parse_xfm_bart_base-v0_1_0.tar.gz
!tar -xzf model_parse_xfm_bart_base-v0_1_0.tar.gz -C models/ && mv models/model_parse_xfm_bart_base-v0_1_0 models/model_stog
!wget -q --show-progress https://github.com/bjascob/amrlib-models/releases/download/model_generate_t5wtense-v0_1_0/model_generate_t5wtense-v0_1_0.tar.gz
!tar -xzf model_generate_t5wtense-v0_1_0.tar.gz -C models/ && mv models/model_generate_t5wtense-v0_1_0 models/model_gtos
print("✅ SETUP COMPLETE")
```

### **Step C: Launch Cell**
Paste and run this in the second cell to start the API:
```python
from google.colab import userdata
from pyngrok import ngrok

# Launch Tunnel
NGROK_TOKEN = userdata.get('NGROK_TOKEN')
ngrok.set_auth_token(NGROK_TOKEN)
ngrok.kill()
public_url = ngrok.connect(8000).public_url
print(f"\n🚀 BACKEND URL: {public_url}")

# Start Services
!chmod +x start.sh
!./start.sh
```

---

## 2. Local Frontend Setup (Your Mac)

Run the interface locally to interact with the cloud engine.

1.  **Open Terminal:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
2.  **Open Browser:** Go to [http://localhost:3000](http://localhost:3000)
3.  **Connect:** Paste the **BACKEND URL** from Colab into the dashboard.

---

## ⚠️ Emergency Reset (Use if Backend Crashes)

If you see errors or the system feels stuck, run this in a new Colab cell:

```python
# 1. Kill old processes
!pkill -9 -f celery
!pkill -9 -f uvicorn
!pkill -9 -f redis-server
from pyngrok import ngrok
ngrok.kill()

# 2. Pull latest fixes
%cd /content/sensorspine-humaniser-v3
!git pull

# 3. Restart
%cd backend
public_url = ngrok.connect(8000).public_url
print(f"\n🚀 NEW BACKEND URL: {public_url}")
!./start.sh
```

---

## 🌟 Pitch Performance Tips
- **First Load:** The first humanization request takes ~30 seconds to wake up the AMR models. Run a "test" request right before your pitch starts.
- **Intensity:** Use `0.6 - 0.8` for the best balance of human-like tone and factual accuracy.
