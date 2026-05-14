import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class DiagnosticJudge:
    def __init__(self, model_id="cross-encoder/nli-deberta-v3-small", device="cpu"):
        """
        Uses a DeBERTa-based classifier for AI detection.
        In a full production setup, you would point this to a fine-tuned 
        AI-detection model (e.g., 'roberta-base-openai-detector' or a custom tune).
        """
        self.model_id = model_id
        self.device = device
        self.tokenizer = None
        self.model = None

    def load_model(self):
        print(f"Loading Diagnostic Judge (DeBERTa): {self.model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        # Using a classification model. Note: For a generic 'small' model, 
        # this acts as a placeholder for a specific AI-detector fine-tune.
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_id, 
            num_labels=3, # Fix #2: Correctly match DeBERTa-v3 NLI 3-class output size
            ignore_mismatched_sizes=True
        ).to(self.device)
        self.model.eval()

    def score_human_confidence(self, text):
        """
        Returns a score between 0 and 1.
        Higher = more confident it's human.
        """
        if not self.model or not self.tokenizer:
            self.load_model()
            
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Apply softmax to get probabilities
            probs = torch.softmax(outputs.logits, dim=-1)
            # Fix #2: Use index 2 (entailment) as the human confidence score
            # Support both single strings and batches of strings
            if probs.dim() == 1:
                return probs[2].item()
            return probs[:, 2].tolist() if probs.shape[0] > 1 else probs[0, 2].item()

    def judge(self, text, threshold=0.7):
        score = self.score_human_confidence(text)
        # In a real-world scenario, you'd use a fine-tuned model where 'score' 
        # is the actual probability of being human.
        return score >= threshold, score
