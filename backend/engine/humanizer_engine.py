import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

class HumanizerEngine:
    def __init__(self, generator_id="google/gemma-4-e4b-it"):
        self.generator_id = generator_id
        self.generator = None
        self.tokenizer = None

    def load_models(self):
        # Quantization config for T4 (15GB VRAM) 
        # Added cpu_offload to handle the 16GB Gemma weights on 15GB VRAM
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            llm_int8_enable_fp32_cpu_offload=True
        )

        # Determine attention implementation based on availability
        attn_impl = "sdpa"
        try:
            import importlib
            if importlib.util.find_spec("flash_attn"):
                attn_impl = "flash_attention_2"
        except ImportError:
            pass

        print(f"Loading generator: {self.generator_id} using {attn_impl}")
        self.generator = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation=attn_impl
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.generator_id)
        
        # Performance Optimization: torch.compile
        try:
            print("Compiling model for faster inference...")
            self.generator = torch.compile(self.generator)
        except Exception as e:
            print(f"Warning: torch.compile failed (not supported on this system): {e}")

    def generate_humanized(self, prompt, intensity=0.5):
        if not self.generator:
            self.load_models()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.generator.device)
        
        # Senior Architect Pivot: Aggressive Sampling for Evasion
        # We drop Contrastive Decoding (CD) due to massive latency and tokenizer mismatches.
        # Instead, we use hyper-optimized sampling parameters to flatten the token distribution.
        
        # Clamp intensity to valid range 0.0 - 1.0
        intensity = max(0.0, min(1.0, intensity))
        
        # Formula-driven aggressive parameters
        gen_temperature = 1.1 + (intensity * 0.5)          # Range: 1.1 -> 1.6
        gen_top_p = 0.90 + (intensity * 0.05)              # Range: 0.90 -> 0.95
        gen_repetition_penalty = 1.1 + (intensity * 0.1)   # Range: 1.1 -> 1.2

        outputs = self.generator.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            temperature=gen_temperature,
            top_p=gen_top_p,
            repetition_penalty=gen_repetition_penalty,
            use_cache=True
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
