# ScholarAI v3 SOTA: End-to-End Deployment Guide

This guide provides a comprehensive, step-by-step walkthrough for deploying the **ScholarAI v3 SOTA** humanization system. It is designed to be accessible to both technical and non-technical users.

---

## 1. Prerequisites (Prepare Your Environment)

Before starting, ensure your local machine is equipped with the necessary tools:

1.  **Node.js (LTS):** The frontend requires Node.js. Download and install the "LTS" version from [nodejs.org](https://nodejs.org/).
2.  **ngrok Account:** The backend uses ngrok to create a secure tunnel. Sign up for a free account at [ngrok.com](https://ngrok.com/) and locate your **Authtoken** in the dashboard.
3.  **HuggingFace Token:** A free account at [huggingface.co](https://huggingface.co/) is required to access the LLM weights. Generate a "Read" token in your Settings.

---

## 2. Phase A: Cloud Backend Orchestration (Google Colab)

The "Brain" of the system runs on Google's T4 GPUs to handle high-performance ML inference.

### **Setup (Cell 1)**
1.  Open [Google Colab](https://colab.research.google.com/) and create a new notebook.
2.  Set the runtime to **T4 GPU** (Runtime > Change runtime type > T4 GPU).
3.  Configure **Secrets** (Key icon on the left):
    *   `NGROK_TOKEN`: Your ngrok Authtoken.
    *   `HF_TOKEN`: Your HuggingFace token.
4.  Paste and run the following code:

```python
# 1. Environment & System Dependency Setup
%cd /content
!rm -rf sensorspine-humaniser-v3
!apt-get install -y redis-server > /dev/null
!pip install --upgrade amrlib fastapi uvicorn pydantic torch accelerate bitsandbytes python-multipart pyngrok penman unidecode huggingface_hub sentencepiece protobuf word2number celery redis flash-attn python-jose[cryptography] passlib[bcrypt] slowapi git+https://github.com/huggingface/transformers.git

# 2. Authenticate & Clone
from google.colab import userdata
from huggingface_hub import login
try:
    login(token=userdata.get('HF_TOKEN'))
except Exception:
    print("WARNING: HF_TOKEN missing from Colab Secrets.")

!git clone https://github.com/NandishSinha1403/sensorspine-humaniser-v3.git
%cd sensorspine-humaniser-v3/backend

# 3. Automated Model Acquisition (Verified amrlib v0.8.1 paths)
print("Synchronizing SOTA AMR models...")
!mkdir -p models
!wget -q --show-progress https://github.com/bjascob/amrlib-models/releases/download/parse_xfm_bart_base-v0_1_0/model_parse_xfm_bart_base-v0_1_0.tar.gz
!tar -xzf model_parse_xfm_bart_base-v0_1_0.tar.gz -C models/ && rm model_parse_xfm_bart_base-v0_1_0.tar.gz
!mv models/model_parse_xfm_bart_base-v0_1_0 models/model_stog

!wget -q --show-progress https://github.com/bjascob/amrlib-models/releases/download/model_generate_t5wtense-v0_1_0/model_generate_t5wtense-v0_1_0.tar.gz
!tar -xzf model_generate_t5wtense-v0_1_0.tar.gz -C models/ && rm model_generate_t5wtense-v0_1_0.tar.gz
!mv models/model_generate_t5wtense-v0_1_0 models/model_gtos

print("✅ Backend Environment Ready.")
```

### **Execution (Cell 2)**
Establish the secure tunnel and launch the service orchestration.

```python
from google.colab import userdata
from pyngrok import ngrok

# Launch Secure Tunnel
NGROK_TOKEN = userdata.get('NGROK_TOKEN')
ngrok.set_auth_token(NGROK_TOKEN)
public_url = ngrok.connect(8000).public_url
print(f"🚀 PUBLIC API URL: {public_url}")

# Orchestrate Services (Redis + Celery + FastAPI)
!chmod +x start.sh
!./start.sh
```
*Keep this Colab tab open while using the application.*

---

## 3. Phase B: Local Frontend Deployment (Mac/PC)

The "Interface" runs locally on your machine for low-latency interactions.

1.  **Open Terminal:** Press `Cmd + Space` and type "Terminal".
2.  **Navigate to Project:**
    ```bash
    cd ~/Documents/sensorspine-humaniser-3/frontend
    ```
3.  **Install Dependencies:** (Required only once)
    ```bash
    npm install
    ```
4.  **Launch Dashboard:**
    ```bash
    npm run dev
    ```
5.  **Access UI:** Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 4. End-to-End Workflow

1.  Copy the **PUBLIC API URL** from the Google Colab output (Step 2).
2.  Paste it into the **Backend URL** field on the local dashboard.
3.  Input your AI-generated text and select the desired **Intensity**.
4.  Click **Execute Semantic Evasion**. The system will automatically handle:
    *   **JWT Authentication:** Fetching a temporary secure token.
    *   **Task Queueing:** Submitting your text to the GPU worker.
    *   **Real-time Polling:** Monitoring the progress until the humanization is complete.

---

## 5. Troubleshooting & FAQ

*   **"npm command not found":** Ensure Node.js is installed from [nodejs.org](https://nodejs.org/). Restart your terminal after installation.
*   **"Authentication failed":** Verify that your Colab backend is running and the URL in the dashboard exactly matches the `ngrok` output.
*   **Latency:** The first request may take up to 60 seconds as models load into VRAM. Subsequent requests are significantly faster.
