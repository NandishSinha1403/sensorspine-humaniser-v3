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

---
Related: [[architecture-v3]], [[roadmap]]