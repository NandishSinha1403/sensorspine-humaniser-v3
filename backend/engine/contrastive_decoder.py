import torch
from transformers import LogitsProcessor, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

class ContrastiveLogitsProcessor(LogitsProcessor):
    def __init__(self, base_model, base_tokenizer, alpha=0.1):
        self.base_model = base_model
        self.base_tokenizer = base_tokenizer
        self.alpha = alpha
        self.past_key_values = None

    def __call__(self, input_ids, scores):
        # Optimized with KV-Caching to prevent O(N^2) complexity
        with torch.no_grad():
            # Only process the last token if we have past_key_values
            if self.past_key_values is not None:
                model_inputs = {"input_ids": input_ids[:, -1:], "past_key_values": self.past_key_values, "use_cache": True}
            else:
                model_inputs = {"input_ids": input_ids, "use_cache": True}
            
            outputs = self.base_model(**model_inputs)
            self.past_key_values = outputs.past_key_values
            
            base_logits = outputs.logits[:, -1, :]
            base_probs = torch.softmax(base_logits, dim=-1)
            
            # Penalize the scores of the generator model
            scores = scores - self.alpha * base_probs
            
        return scores

class HumanizerEngine:
    def __init__(self, generator_id="google/gemma-4-e4b-it", base_id="gpt2"):
        self.generator_id = generator_id
        self.base_id = base_id
        self.generator = None
        self.base_model = None
        self.tokenizer = None
        self.base_tokenizer = None

    def load_models(self):
        # Quantization config for T4 (15GB VRAM) 
        # Added cpu_offload to handle the 16GB Gemma weights on 15GB VRAM
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            llm_int8_enable_fp32_cpu_offload=True
        )

        print(f"Loading generator: {self.generator_id}")
        self.generator = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation="flash_attention_2"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.generator_id)

        print(f"Loading base model: {self.base_id}")
        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.base_id,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation="flash_attention_2"
        )
        self.base_tokenizer = AutoTokenizer.from_pretrained(self.base_id)
        
        # Performance Optimization: torch.compile
        # This speeds up the forward passes used in the Contrastive Decoding loop.
        try:
            print("Compiling models for faster inference...")
            self.base_model = torch.compile(self.base_model)
            # We don't compile the generator yet as generate() has its own 
            # experimental compilation in newer transformers versions
        except Exception as e:
            print(f"Warning: torch.compile failed (not supported on this system): {e}")

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
            top_p=0.9,
            use_cache=True # Ensure generator uses cache too
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
