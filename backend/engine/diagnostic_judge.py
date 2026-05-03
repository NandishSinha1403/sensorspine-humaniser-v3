import torch
import numpy as np

class DiagnosticJudge:
    def __init__(self, model=None, tokenizer=None):
        self.model = model
        self.tokenizer = tokenizer

    def calculate_perplexity(self, text):
        """
        Uses the provided model (ideally the base GPT-2) to calculate perplexity.
        Lower perplexity often indicates more 'AI-like' predictable text.
        Human text tends to have higher variance/perplexity in specific contexts.
        """
        if not self.model or not self.tokenizer:
            return 0.5 # Default score
        
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            perplexity = torch.exp(loss).item()
            
        return perplexity

    def score_human_confidence(self, text):
        """
        Returns a score between 0 and 1.
        Higher = more confident it's human.
        """
        perplexity = self.calculate_perplexity(text)
        
        # Heuristic: Human text usually has perplexity in a specific range for academic text.
        # This is a very rough normalization for demonstration.
        # GPT-2 perplexity on 'human' text is often 20-100+.
        # On 'AI' text, it might be 5-15.
        score = min(1.0, perplexity / 100.0) 
        return score

    def judge(self, text, threshold=0.7):
        score = self.score_human_confidence(text)
        return score >= threshold, score
