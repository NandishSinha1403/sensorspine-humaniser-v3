# ScholarAI v3 SOTA: Troubleshooting & Deployment Notes

## Current Deployment State (May 4, 2026)

### 1. CORS (Cross-Origin Resource Sharing) Issue
**Problem:** The Next.js frontend (`localhost:3000`) could not communicate with the `ngrok` tunneled backend in Google Colab, resulting in "Failed to fetch" errors.
**Fix:** Added `CORSMiddleware` to `backend/main.py` allowing `allow_origins=["*"]`.

### 2. Google Colab Module Discovery
**Problem:** `pip install amrlib` in Colab cells often failed to register the `amrlib.setup_utils` module immediately for following shell commands.
**Fix:** Moved model downloads into a direct `python3 -c` call or `importlib.reload(amrlib)` to force environment refresh.

### 3. AMR Model Download 404s
**Problem:** The previous links to `amrlib` models on GitHub releases were incorrect or outdated, causing `wget` to return 404 errors.
**Status:** Updated `change.txt` with correct links:
*   StoG: `parse_t5-v0_2_0`
*   GtoS: `generate_t5-v0_1_0`
**Next Step:** User needs to run the updated "Final Stable Version v2" from `change.txt` in Colab after pushing local fixes to GitHub.

### 4. Directory Structure Sync
**Problem:** Repeated `git clone` commands in Colab were creating nested directory structures (e.g., `.../backend/sensorspine-humaniser-v3/backend`).
**Fix:** Updated `change.txt` to include `%cd /content` and `!rm -rf` at the start of the setup block to ensure a clean, consistent root.

---
Related: [[context]], [[roadmap]]
