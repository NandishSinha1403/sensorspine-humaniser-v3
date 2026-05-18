# ScholarAI v3: Deep Humanization Training Log

## Corpus Statistics (As of 2026-05-18)
- **Timeframe:** 2000 - 2015 (Strictly Pre-AI)
- **Target Institutions:** MIT, Harvard, Stanford, IITs, IISc, etc.
- **Downloaded PDFs:** 500 (Target Met)
- **Successfully Preprocessed:** 500
- **Domain Coverage:** 50+ diverse academic domains.
- **Total Training Tokens (Estimate):** ~2.5M+ tokens of high-signal human academic prose.

## Training Phases (Completed)

### 1. Stage 1: CLM Fine-Tuning (`fine_tune_clm.py`)
- **Status:** [x] SUCCESS
- **Hardware:** Kaggle GPU T4 x2 (DDP)
- **Result:** Successfully shifted Qwen2-7B base weights toward human academic token distributions. 

### 2. Stage 2: Detector Penalization via DPO (`fine_tune_dpo.py`)
- **Status:** [x] SUCCESS
- **Dataset:** 500 humanization pairs generated recursively via `generate_dpo_data.py`.
- **Hardware:** Kaggle GPU T4 x2 (DDP)
- **Fix Applied:** Decoupled slow single-GPU generation (~4 hours) from distributed training to prevent NCCL barrier timeouts.
- **Result:** Model shows significant reduction in AI-typical transition words ("Moreover", "Furthermore") and increased structural burstiness.

## Performance Targets
- **Turnitin Evasion Score:** < 10% AI Probability (Target).
- **GPTZero Evasion Score:** "Highly likely human" (Target).
- **Linguistic Quality:** Successfully increased structural burstiness while maintaining logical coherence.

---
*Last Updated: 2026-05-18*
