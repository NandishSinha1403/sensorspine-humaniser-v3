# ADR-001: Decoupled DPO Dataset Generation

## Context
During Phase 4 (DPO Training) on Kaggle T4 x2 hardware, the system experienced intermittent NCCL barrier timeouts (`torch.distributed.DistBackendError`). 

The root cause was the high latency of dataset generation:
1. Rank 0 would start generating 500 samples (recursive LLM calls + DeBERTa scoring).
2. Rank 1 would reach the `torch.distributed.barrier()` and wait.
3. The generation process took > 3 hours, exceeding the default 10-minute (600s) socket timeout.

## Decision
We moved the dataset generation logic out of the distributed environment into a standalone script `generate_dpo_data.py`.

## Implementation
- **Script:** `generate_dpo_data.py` runs on a single GPU using `device_map="auto"`.
- **Workflow:** The notebook executes generation sequentially *before* calling `torchrun`.
- **Resilience:** `fine_tune_dpo.py` now includes a strict file-check and raises `FileNotFoundError` if the data isn't ready, preventing idle GPU time.

## Consequences
- **Easier Rollbacks:** We can now inspect/edit the `dpo_dataset.json` before wasting GPU hours on training.
- **Stability:** NCCL timeouts are eliminated as both GPUs engage simultaneously for actual compute.
- **Efficiency:** The second GPU is not initialized during the slow generation phase, saving VRAM.
