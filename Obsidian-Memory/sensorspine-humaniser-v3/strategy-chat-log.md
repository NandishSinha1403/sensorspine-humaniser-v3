# Strategy Log: The Pivot to v3 SOTA

## The Decision (2026-05-03)
During the v2.2 maintenance phase, we identified that heuristic, rule-based evasion (spaCy inversions, Unicode jitter) was increasingly vulnerable to enterprise-grade statistical detectors. 

### The Critique of v2.2
*   **Unicode Tricks**: Brittle and easily stripped by detectors.
*   **Rule-Based Inversion**: Creates "Frankenstein" sentences that feel unnatural to human reviewers.
*   **Static DNA**: Simple bigram/trigram models can't capture the deep semantic flow of modern scholarship.

### The v3 Vision
We decided to build a brand new project from scratch, moving away from "fixing AI text" to **"regenerating human text from AI concepts."** This requires a clean-slate repository built on PyTorch and HuggingFace, focusing on Contrastive Decoding and Semantic Graph Fusion.

---
Related: [[context]], [[architecture-v3]]