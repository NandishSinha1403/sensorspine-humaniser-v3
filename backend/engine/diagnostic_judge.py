import re
import math
import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2TokenizerFast,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

_MIN_BURSTINESS = 0.18
_AI_DETECTOR_ID = "roberta-base-openai-detector"


class DiagnosticJudge:
    """
    Hybrid scorer aligned with external detectors:
    - RoBERTa OpenAI detector (QuillBot/GPTZero-style classifier proxy)
    - GPT-2 burstiness (sentence-level variance)
    """

    def __init__(self, device="cpu"):
        self.device = device
        self.gpt2_tokenizer = None
        self.gpt2_model = None
        self.detector_tokenizer = None
        self.detector_model = None

    def load_model(self):
        if self.detector_model is not None:
            return

        print(f"Loading AI Detector: {_AI_DETECTOR_ID}")
        self.detector_tokenizer = AutoTokenizer.from_pretrained(_AI_DETECTOR_ID)
        self.detector_model = AutoModelForSequenceClassification.from_pretrained(
            _AI_DETECTOR_ID
        ).to(self.device)
        self.detector_model.eval()

        print("Loading burstiness model: gpt2")
        self.gpt2_tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        self.gpt2_model = GPT2LMHeadModel.from_pretrained("gpt2").to(self.device)
        self.gpt2_model.eval()
        if self.gpt2_tokenizer.pad_token is None:
            self.gpt2_tokenizer.pad_token = self.gpt2_tokenizer.eos_token

    def _ai_probability(self, text: str) -> float:
        """Probability text is AI-generated (0=human, 1=AI)."""
        inputs = self.detector_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            logits = self.detector_model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)

        # Label 1 = Fake/AI for roberta-base-openai-detector
        return probs[0, 1].item()

    def _sentence_perplexity(self, sentence: str) -> float:
        if not sentence.strip():
            return 0.0

        encodings = self.gpt2_tokenizer(
            sentence, return_tensors="pt", truncation=True, max_length=512
        ).to(self.device)
        if encodings.input_ids.shape[1] < 2:
            return 0.0

        with torch.no_grad():
            loss = self.gpt2_model(encodings.input_ids, labels=encodings.input_ids).loss.item()
        return math.exp(min(loss, 20.0))

    def _split_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(⟦])", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def _burstiness_score(self, text: str) -> float:
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return 0.0

        perplexities = [self._sentence_perplexity(s) for s in sentences]
        mean_ppl = sum(perplexities) / len(perplexities)
        variance = sum((p - mean_ppl) ** 2 for p in perplexities) / len(perplexities)
        burstiness = math.sqrt(variance) / (mean_ppl + 1e-6)
        return min(1.0, burstiness / _MIN_BURSTINESS)

    def _corruption_penalty(self, text: str) -> float:
        """Penalize AMR/LLM artifacts that increase detector suspicion."""
        penalty = 0.0
        corruption_markers = [
            r"⟦PROT",                          # leaked placeholder
            r"\bfrac\(",                       # mangled LaTeX
            r"\b(?:sqrt|sigma|epsilon|rho)\(",  # mangled math commands
            r"'s\s+law\b",                     # lowercased law name (sign of corruption)
        ]
        for pat in corruption_markers:
            if re.search(pat, text, re.IGNORECASE):
                penalty += 0.12
        return min(0.45, penalty)

    def score_metrics(self, text: str) -> dict:
        if not self.detector_model:
            self.load_model()

        ai_prob = self._ai_probability(text)
        burst_score = self._burstiness_score(text)
        corruption = self._corruption_penalty(text)

        # Primary signal: classifier human probability
        detector_human = 1.0 - ai_prob
        human_confidence = (
            0.80 * detector_human
            + 0.20 * burst_score
            - corruption
        )
        human_confidence = max(0.0, min(1.0, human_confidence))

        sentences = self._split_sentences(text)
        mean_ppl = 0.0
        burstiness = 0.0
        if sentences:
            perplexities = [self._sentence_perplexity(s) for s in sentences]
            mean_ppl = sum(perplexities) / len(perplexities)
            if len(perplexities) > 1:
                variance = sum((p - mean_ppl) ** 2 for p in perplexities) / len(perplexities)
                burstiness = math.sqrt(variance) / (mean_ppl + 1e-6)

        return {
            "ai_probability": round(ai_prob, 4),
            "mean_perplexity": round(mean_ppl, 2),
            "burstiness": round(burstiness, 3),
            "sentence_count": len(sentences),
            "human_confidence": round(human_confidence, 4),
        }

    def score_human_confidence(self, text):
        return self.score_metrics(text)["human_confidence"]

    def judge(self, text, threshold=0.55):
        metrics = self.score_metrics(text)
        return metrics["human_confidence"] >= threshold, metrics["human_confidence"]

    def pick_best_candidate(self, candidates: list[str], reference: str = "") -> tuple[str, dict]:
        if not candidates:
            return "", {"human_confidence": 0.0}

        best_text = candidates[0]
        best_metrics = self.score_metrics(best_text)
        best_score = best_metrics["human_confidence"]

        ref_words = set(reference.lower().split()) if reference else set()

        for candidate in candidates[1:]:
            metrics = self.score_metrics(candidate)
            score = metrics["human_confidence"]

            # Prefer candidates that preserve reference vocabulary (less paraphraser drift)
            if ref_words:
                cand_words = set(candidate.lower().split())
                overlap = len(ref_words & cand_words) / max(len(ref_words), 1)
                score += 0.05 * overlap

            if score > best_score:
                best_text = candidate
                best_metrics = metrics
                best_score = score

        return best_text, best_metrics
