a# Strategy Log: The Pivot to v3 SOTA

## The Decision (2026-05-03)
During the v2.2 maintenance phase, we identified that heuristic, rule-based evasion (spaCy inversions, Unicode jitter) was increasingly vulnerable to enterprise-grade statistical detectors. 

### The Critique of v2.2
*   **Unicode Tricks**: Brittle and easily stripped by detectors.
*   **Rule-Based Inversion**: Creates "Frankenstein" sentences that feel unnatural to human reviewers.
*   **Static DNA**: Simple bigram/trigram models can't capture the deep semantic flow of modern scholarship.

### The v3 Vision
We decided to build a brand new project from scratch, moving away from "fixing AI text" to **"regenerating human text from AI concepts."** This requires a clean-slate repository built on PyTorch and HuggingFace, focusing on Contrastive Decoding and Semantic Graph Fusion.

---
## Current State: May 4, 2026 - 01:00 AM
**Status:** Implementation complete, deployment in progress.
**Key Issues Resolved:**
- **CORS:** Added middleware to `main.py` to allow the Next.js frontend to talk to the ngrok tunnel.
- **Colab Sync:** Optimized `backend_runner.ipynb` and `change.txt` for clean clones and module discovery.
- **AMR Models:** Fixed 404 links for STOG/GTOS models in `change.txt` and updated `amr_handler.py` to recognize new folder names.

**Current Blockers:**
- **GitHub Push:** Local `git push` is currently timing out on the Mac. **User must run `git push` manually when the connection is stable.**
- **Model Download:** The previous 404 error was due to malformed release URLs; corrected links are now in `change.txt`.

**Files Created/Modified:**
- `backend/engine/amr_handler.py` (updated paths)
- `change.txt` (corrected setup code)
- `Obsidian-Memory/sensorspine-humaniser-v3/troubleshooting-v3.md` (new)
- `Obsidian-Memory/sensorspine-humaniser-v3/context.md` (updated)
- `Obsidian-Memory/sensorspine-humaniser-v3/roadmap.md` (updated)

---
## Current State: May 5, 2026 - 10:00 AM
**Status:** Backend connectivity fixed; models ready for cloud deployment.
**Key Issues Resolved:**
- **AMR 404s:** Fixed the release tag URLs in `change.txt` by adding the `model_` prefix (e.g., `model_parse_t5-v0_2_0`). 
- **Code Audit:** Verified that `HumanizerEngine`, `ContrastiveLogitsProcessor`, and `DiagnosticJudge` are correctly integrated in `main.py` for recursive refinement.

**Current Blockers:**
- **None:** Git push successful; cloud backend can now sync latest fixes.

---
## Current State: May 7, 2026 - 01:30 PM
**Status:** AMR Pipeline stabilized with latest models.
**Key Issues Resolved:**
- **Deprecated Models:** Identified that T5 models were deprecated. Updated `change.txt` and `amr_handler.py` to use `xfm_bart_base` (Parsing) and `t5wtense` (Generation) models.
- **Wget Progress:** Removed quiet flag from `change.txt` to monitor download progress in Colab.

**Current Blockers:**
- **Inference Verification:** Need to run the updated setup in Colab to confirm the full cycle.

Related: [[context]], [[architecture-v3]], [[troubleshooting-v3]]