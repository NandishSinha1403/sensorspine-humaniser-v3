import re
import math
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

# GPTZero-style thresholds (empirical proxies for human academic prose)
_MIN_HUMAN_PERPLEXITY = 18.0
_MAX_HUMAN_PERPLEXITY = 280.0
_MIN_BURSTINESS = 0.22


class DiagnosticJudge:
    """
    GPTZero-proxy scorer using GPT-2 sentence perplexity and burstiness.

    GPTZero flags text when (a) average perplexity is too low (predictable tokens)
    and (b) burstiness (variance of sentence-level perplexity) is too uniform.
    """

    def __init__(self, model_id="gpt2", device="cpu"):
        self.model_id = model_id
        self.device = device
        self.tokenizer = None
        self.model = None

    def load_model(self):
        if self.model is not None:
            return
        print(f"Loading Diagnostic Judge (GPT-2 perplexity proxy): {self.model_id}")
        self.tokenizer = GPT2TokenizerFast.from_pretrained(self.model_id)
        self.model = GPT2LMHeadModel.from_pretrained(self.model_id).to(self.device)
        self.model.eval()
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _sentence_perplexity(self, sentence: str) -> float:
        if not sentence.strip():
            return 0.0

        encodings = self.tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)

        input_ids = encodings.input_ids
        if input_ids.shape[1] < 2:
            return 0.0

        with torch.no_grad():
            outputs = self.model(input_ids, labels=input_ids)
            loss = outputs.loss.item()

        return math.exp(min(loss, 20.0))

    def _split_sentences(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def score_metrics(self, text: str) -> dict:
        """Return raw perplexity/burstiness metrics for logging and selection."""
        if not self.model:
            self.load_model()

        sentences = self._split_sentences(text)
        if not sentences:
            return {
                "mean_perplexity": 0.0,
                "burstiness": 0.0,
                "sentence_count": 0,
                "human_confidence": 0.0,
            }

        perplexities = [self._sentence_perplexity(s) for s in sentences]
        mean_ppl = sum(perplexities) / len(perplexities)
        if len(perplexities) > 1:
            variance = sum((p - mean_ppl) ** 2 for p in perplexities) / len(perplexities)
            burstiness = math.sqrt(variance) / (mean_ppl + 1e-6)
        else:
            burstiness = 0.0

        # Penalize overly smooth (low PPL) and overly chaotic (extreme PPL) text.
        if mean_ppl < _MIN_HUMAN_PERPLEXITY:
            ppl_score = mean_ppl / _MIN_HUMAN_PERPLEXITY
        elif mean_ppl > _MAX_HUMAN_PERPLEXITY:
            ppl_score = max(0.0, 1.0 - (mean_ppl - _MAX_HUMAN_PERPLEXITY) / _MAX_HUMAN_PERPLEXITY)
        else:
            ppl_score = 1.0

        burst_score = min(1.0, burstiness / _MIN_BURSTINESS)
        human_confidence = 0.45 * ppl_score + 0.55 * burst_score

        return {
            "mean_perplexity": round(mean_ppl, 2),
            "burstiness": round(burstiness, 3),
            "sentence_count": len(sentences),
            "human_confidence": round(human_confidence, 4),
        }

    def score_human_confidence(self, text):
        return self.score_metrics(text)["human_confidence"]

    def judge(self, text, threshold=0.55):
        metrics = self.score_metrics(text)
        score = metrics["human_confidence"]
        return score >= threshold, score

    def pick_best_candidate(self, candidates: list[str]) -> tuple[str, dict]:
        """Select the candidate with the highest human-confidence score."""
        if not candidates:
            return "", {"human_confidence": 0.0}

        best_text = candidates[0]
        best_metrics = self.score_metrics(best_text)

        for candidate in candidates[1:]:
            metrics = self.score_metrics(candidate)
            if metrics["human_confidence"] > best_metrics["human_confidence"]:
                best_text = candidate
                best_metrics = metrics

        return best_text, best_metrics
