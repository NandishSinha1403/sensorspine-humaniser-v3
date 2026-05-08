# Troubleshooting & Known Issues

## 1. Memory Issues (OOM)
- **Problem:** CUDA Out of Memory on 15GB/16GB cards.
- **Solution:** Ensure `llm_int8_enable_fp32_cpu_offload=True` is set in `BitsAndBytesConfig`. This allows the overflow of the 16GB Gemma weights to be stored in system RAM.

## 2. AMR Model Loading
- **Problem:** `No module named 'word2number'`.
- **Solution:** This dependency is required by `amrlib`. Ensure it is installed via `pip install word2number`. It is included in the latest `change.txt`.

## 3. Task Status "Pending" Forever
- **Problem:** The API returns `task_id` but status never changes.
- **Solution:** Ensure the Celery worker is running.
  - Command: `celery -A tasks worker --loglevel=info --concurrency=1`
  - Note: `--concurrency=1` is recommended for single-GPU environments.

## 4. Contrastive Decoding Latency
- **Problem:** Generation is slow despite KV-caching.
- **Solution:** 
  - Verify Flash Attention 2 is enabled in `contrastive_decoder.py`.
  - Ensure `torch.compile` successfully initialized on the base model (GPT-2).

## 5. AMR Fusion Warnings
- **Problem:** `CRITICAL WARNING: Structural AMR Fusion failed`.
- **Solution:** This occurs if `penman` cannot reconcile variables even with remapping. The system will fall back to returning the first graph to avoid crashing the pipeline. Check the logs for specific variable collision details.
