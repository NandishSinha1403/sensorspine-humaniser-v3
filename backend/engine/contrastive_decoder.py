import torch
from transformers import LogitsProcessor, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

class ContrastiveLogitsProcessor(LogitsProcessor):
    def __init__(self, base_model, base_tokenizer, alpha=0.1):
        self.base_model = base_model
        self.base_tokenizer = base_tokenizer
        self.alpha = alpha

    def __call__(self, input_ids, scores):
        # We need to get the probabilities from the base model for the current sequence
        # Note: This is a simplified version. Real contrastive decoding usually
        # aligns tokenizers if they differ, or uses a common base.
        with torch.no_grad():
            outputs = self.base_model(input_ids)
            base_logits = outputs.logits[:, -1, :]
            base_probs = torch.softmax(base_logits, dim=-1)
            
            # Penalize the scores of the generator model
            # scores = scores - alpha * base_probs
            # This pushes the generator away from tokens the base model (AI-like) predicts
            scores = scores - self.alpha * base_probs
            
        return scores

class HumanizerEngine:
    def __init__(self, generator_id="meta-llama/Meta-Llama-3-8B", base_id="gpt2"):
        self.generator_id = generator_id
        self.base_id = base_id
        self.generator = None
        self.base_model = None
        self.tokenizer = None
        self.base_tokenizer = None

    def load_models(self):
        # Quantization config for T4 (15GB VRAM)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )

        print(f"Loading generator: {self.generator_id}")
        self.generator = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.generator_id)

        print(f"Loading base model: {self.base_id}")
        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.base_id,
            device_map="auto"
        )
        self.base_tokenizer = AutoTokenizer.from_pretrained(self.base_id)

    def generate_humanized(self, prompt, alpha=0.5):
        if not self.generator:
            self.load_models()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.generator.device)
        
        # Initialize our custom processor
        contrastive_processor = ContrastiveLogitsProcessor(
            self.base_model, 
            self.base_tokenizer, 
            alpha=alpha
        )

        outputs = self.generator.generate(
            **inputs,
            max_new_tokens=256,
            logits_processor=[contrastive_processor],
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
