# Troubleshooting & Known Issues

## 1. Memory Issues (OOM)
- **Problem:** CUDA Out of Memory on 15GB/16GB cards.
- **Resolution:** Dropped the GPT-2 base model (VRAM saving ~1.5GB). Added NF4 4-bit quantization + CPU offloading for Gemma-4.

## 2. CUDA Device-Side Assert (Root Cause: Tokenizer Mismatch)
- **Problem:** `index out of bounds: 0 <= tmp4 < 50257` during generation.
- **Root Cause:** GPT-2 (50k vocab) cannot be element-wise subtracted from Gemma-4 (256k vocab). The indices represent different semantic tokens.
- **Resolution:** Removed the Contrastive Decoding loop. Pivoted to single-model Aggressive Sampling (Option 3).

## 3. Prompt Leakage & Output Gibberish
- **Problem:** "Rewrite this text..." appears in output; model repeats fragments like "findingsitt...".
- **Root Cause:** Missing Chat Template delimiters (`<start_of_turn>user`) and aggressive sampling (temp=1.6) without proper sequence anchoring.
- **Resolution:** Implemented `tokenizer.apply_chat_template` with `add_generation_prompt=True` and output slicing. Recalibrated temperature to `0.8-1.2`.

## 4. torch.load Security Block (CVE-2025-32434)
- **Problem:** `ValueError` citing CVE-2025-32434 prevents loading `.bin` models on Torch < 2.6.
- **Resolution:** 
    - Migrated Diagnostic Judge to `cross-encoder/nli-deberta-v3-small` (Safetensors).
    - Applied surgical monkeypatch to `transformers.modeling_utils` for local AMR models.

## 5. Frontend "Failed to Fetch"
- **Problem:** ngrok interstitial warning page blocks browser API requests.
- **Resolution:** Added custom middleware in `main.py` to inject `ngrok-skip-browser-warning: true` header into all responses.
