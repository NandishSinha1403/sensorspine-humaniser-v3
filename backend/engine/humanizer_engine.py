import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

class HumanizerEngine:
    def __init__(self, generator_id="Qwen/Qwen2-7B-Instruct"):
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

        # Senior Architect: Use SDPA for maximum stability on T4 GPUs
        attn_impl = "sdpa"
        print(f"Loading generator: {self.generator_id} using {attn_impl}")
        self.generator = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation=attn_impl,
            trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.generator_id,
            trust_remote_code=True
        )
        
        # Performance Optimization: torch.compile
        try:
            print("Compiling model for faster inference...")
            self.generator = torch.compile(self.generator)
        except Exception as e:
            print(f"Warning: torch.compile failed (not supported on this system): {e}")

    def generate_humanized(self, prompt, intensity=0.5):
        if not self.generator:
            self.load_models()

        # Senior Architect: Use apply_chat_template to prevent prompt leakage and gibberish loops
        # Gemma-4 IT models require structured turn delimiters to separate prompt from response.
        chat = [{"role": "user", "content": prompt}]
        formatted_inputs = self.tokenizer.apply_chat_template(
            chat, 
            add_generation_prompt=True, 
            return_tensors="pt"
        ).to(self.generator.device)
        
        input_len = formatted_inputs.shape[-1]
        
        # Clamp intensity to valid range 0.0 - 1.0
        intensity = max(0.0, min(1.0, intensity))
        
        # Recalibrated formulas for stable evasion (preventing distribution collapse)
        gen_temperature = 0.8 + (intensity * 0.4)          # Range: 0.8 -> 1.2
        gen_top_p = 0.90 + (intensity * 0.05)              # Range: 0.90 -> 0.95
        gen_repetition_penalty = 1.05 + (intensity * 0.1)  # Range: 1.05 -> 1.15

        outputs = self.generator.generate(
            formatted_inputs,
            max_new_tokens=512, # Increased for longer academic passages
            do_sample=True,
            temperature=gen_temperature,
            top_p=gen_top_p,
            repetition_penalty=gen_repetition_penalty,
            use_cache=True
        )

        # Senior Architect: Slice output to return ONLY the newly generated tokens
        generated_tokens = outputs[0][input_len:]
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
