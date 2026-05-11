# Troubleshooting & Known Issues (v3 SOTA)

## 1. RuntimeError: CUDA Major Version Mismatch
- **Problem:** `Detected that PyTorch and torchvision were compiled with different CUDA major versions (13.0 vs 12.8).`
- **Root Cause:** A general `pip install --upgrade` command was overwriting the CUDA 12.1-specific PyTorch binaries with default PyPi versions.
- **Resolution:** Removed `torch` and `torchvision` from the upgrade command. Explicitly installed them via the `--index-url https://download.pytorch.org/whl/cu121` index.

## 2. ModuleNotFoundError: 'Gemma4Config'
- **Problem:** `transformers` library failing to load the Gemma-4 configuration class.
- **Root Cause:** Gemma-4 is a multimodal model. Recent environment downgrades broke `pillow` and `torchvision` dependencies. Because the model class is multimodal, the loader crashes if vision libraries are in an inconsistent state.
- **Resolution:** Pinned `numpy<2.1` and `pillow<12.0` in the Colab setup cell to satisfy the multimodal imports.

## 3. AttributeError: 'Qwen2ForCausalLM' has no len()
- **Problem:** Crash during the generation loop on T4 GPUs.
- **Root Cause:** `torch.compile` optimization introduced internal attribute mismatches with the Qwen2 model architecture in the `transformers` dev branch.
- **Resolution:** Disabled `torch.compile` in `humanizer_engine.py`. Stability prioritized over marginal speed gains for pitch delivery.

## 4. AttributeError: 'BatchEncoding' object has no attribute 'shape'
- **Problem:** Crash when calculating `input_len`.
- **Root Cause:** Incorrectly attempting to access `.shape` on the `BatchEncoding` object returned by `tokenizer.apply_chat_template` instead of accessing the underlying `.input_ids.shape`.
- **Resolution:** Updated `humanizer_engine.py` to use `formatted_inputs.input_ids.shape[-1]`.

## 5. 403 Client Error: Gated Repo (Llama-3)
- **Problem:** Access denied when trying to pull `meta-llama/Meta-Llama-3-8B-Instruct`.
- **Resolution:** Pivoted to `Qwen/Qwen2-7B-Instruct`. It is a non-gated, high-performance SOTA alternative that requires no manual permissions.

## 6. Frontend JSON Parsing Errors (ngrok)
- **Problem:** Frontend failing to connect to backend via ngrok tunnel.
- **Root Cause:** ngrok "Browser Warning" interstitial page intercepting API calls and returning HTML.
- **Resolution:** Injected `ngrok-skip-browser-warning: true` headers into both the FastAPI middleware and all frontend `fetch()` requests.
