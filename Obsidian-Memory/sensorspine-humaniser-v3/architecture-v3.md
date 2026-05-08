# ScholarAI v3 SOTA: Architecture

## Technical Stack
*   **Language:** Python 3.10+
*   **Core Frameworks:** 
    *   **PyTorch**: For tensor operations and model hosting.
    *   **HuggingFace Transformers/Accelerate**: For LLM orchestration and inference.
    *   **AMRLib**: For Abstract Meaning Representation parsing and generation.
*   **API Layer:** FastAPI (High-performance async routing).
*   **Hardware Target:** GPU-accelerated (CUDA/MPS) for real-time contrastive decoding.

## Component Map

### 1. Semantic Parser (AMR)
Converts input text into semantic graphs. Handles the "Fission/Fusion" of ideas at the graph level to ensure natural burstiness.

### 2. Inference Engine (The "Humanizer")
A locally hosted **Gemma-4 E4B** model (4 Billion parameters). Despite its size, it offers SOTA intelligence density (MMLU Pro ~69.4%) and is optimized for instruction following. Quantized to 4-bit/8-bit to run efficiently on T4 GPUs alongside the AMR pipeline.
### 3. Contrastive Validator
A parallel GPT-2/3 model used to calculate the "AI Probability" of tokens during generation, feeding the penalty values back into the Inference Engine's logits.

### 4. Recursive Diagnostic Judge
A streamlined version of the legacy 9-channel detector used to score the final output and trigger regeneration if the "Human Confidence" threshold isn't met.

---
Related: [[context]], [[roadmap]]