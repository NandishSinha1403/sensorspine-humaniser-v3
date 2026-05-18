# ScholarAI v3 SOTA: Core Context

## Philosophy
ScholarAI v3 abandons rule-based heuristics (regex, synonym swapping) in favor of **Deep Semantic Evasion**. The goal is to generate text that is mathematically indistinguishable from human writing by navigating the "human tail" of token probability distributions.

## Core Strategies

### 1. Evasion-Guided Generation (Contrastive Decoding)
Instead of standard sampling, v3 uses a dual-model setup. A SOTA local LLM (e.g., Llama-3 8B) generates text while a smaller "base" model (e.g., GPT-2) identifies high-probability AI tokens. The generator is mathematically penalized for choosing tokens the base model predicts, forcing it into human-like linguistic patterns.

### 2. Semantic Graph Paraphrasing (DIPPER Style)
Text is first converted into an **Abstract Meaning Representation (AMR)** graph. This graph represents pure concepts without syntactic bias. New sentences are then synthesized from the graph, completely destroying the original AI's syntactic DNA.

### 3. Integrated Graph Burstiness
Fission (splitting) and Fusion (merging) of sentences are performed at the **Semantic Graph level** before regeneration. This ensures extreme variance in sentence length (burstiness) while maintaining perfect grammatical integrity.

### 4. Innate Style Emulation (Pre-AI Grounding)
The model is fine-tuned via CLM on a curated corpus of prestigious research papers from the **2000-2015 era**. This grounds the model's baseline token prediction in a purely human statistical distribution, allowing it to bypass modern AI detectors (Turnitin, GPTZero) by mimicking the structural and lexical patterns of the pre-LLM academic world.

---
## Hardware-Aware Implementation (v3.1)
Due to MacBook M2 (8GB RAM) limitations, the architecture has been split:
*   **Local Frontend:** Next.js dashboard for user interaction.
*   **Cloud Backend:** Google Colab (T4 GPU) hosting Llama-3 8B (4-bit), GPT-2, and AMR models.
*   **Bridge:** `ngrok` tunnel connecting the local UI to the cloud engine.

Related: [[architecture-v3]], [[roadmap]], [[troubleshooting-v3]]