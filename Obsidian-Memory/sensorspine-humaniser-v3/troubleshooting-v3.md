# ScholarAI v3 SOTA: Troubleshooting & Deployment Notes

## Current Deployment State (May 4, 2026)

### 1. CORS (Cross-Origin Resource Sharing) Issue
**Problem:** The Next.js frontend (`localhost:3000`) could not communicate with the `ngrok` tunneled backend in Google Colab, resulting in "Failed to fetch" errors.
**Fix:** Added `CORSMiddleware` to `backend/main.py` allowing `allow_origins=["*"]`.

### 2. Google Colab Module Discovery
**Problem:** `pip install amrlib` in Colab cells often failed to register the `amrlib.setup_utils` module immediately for following shell commands.
**Fix:** Moved model downloads into a direct `python3 -c` call or `importlib.reload(amrlib)` to force environment refresh.

### 3. AMR Model Download 404s
**Problem:** The previous links to `amrlib` models on GitHub releases were incorrect or outdated (T5 models were deprecated), causing `wget` to return 404 errors.
**Status:** **RESOLVED (2026-05-07)**
**Fix:** Pivoted to `amrlib`'s built-in automated downloaders in `change.txt`.
*   Command: `!python3 -c "import amrlib; amrlib.setup_sentence_to_amr(); amrlib.setup_amr_to_sentence()"`
**Note:** This is the most robust method as it fetches the current default models directly into the `amrlib` cache, bypassing brittle manual URLs. `backend/engine/amr_handler.py` was simplified to use default loading paths.

### 4. Directory Structure Sync
**Problem:** Repeated `git clone` commands in Colab were creating nested directory structures (e.g., `.../backend/sensorspine-humaniser-v3/backend`).
**Fix:** Updated `change.txt` to include `%cd /content` and `!rm -rf` at the start of the setup block to ensure a clean, consistent root.

---
Related: [[context]], [[roadmap]]
