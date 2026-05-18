import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

class HumanizerEngine:
    def __init__(self, generator_id="Qwen/Qwen2-7B-Instruct"):
        self.generator_id = generator_id
        self.generator = None
        self.tokenizer = None
        self.adapter_id = "qwen2-7b-pre-ai-dpo"

    def _resolve_adapter_path(self):
        """
        Senior Architect: Resolve adapter path relative to repo root.
        Handles execution from / or /backend/ or /backend/engine/.
        """
        candidates = [
            self.adapter_id,                                # Root execution
            f"../{self.adapter_id}",                        # /backend/ execution
            f"../../{self.adapter_id}",                     # /backend/engine/ execution
            os.path.join(os.getcwd(), self.adapter_id)
        ]
        for path in candidates:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        return None

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
        
        # Load Base Model
        base_model = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto",
            dtype=torch.float16,
            attn_implementation=attn_impl,
            trust_remote_code=True
        )

        # Apply DPO Adapter if present
        adapter_path = self._resolve_adapter_path()
        if adapter_path:
            print(f"Engine: Phase 4 DPO Adapter found at {adapter_path}. Injecting SOTA weights...")
            self.generator = PeftModel.from_pretrained(base_model, adapter_path)
            self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
        else:
            print("Engine: Warning: No DPO Adapter found. Falling back to Base Model inference.")
            self.generator = base_model
            self.tokenizer = AutoTokenizer.from_pretrained(self.generator_id, trust_remote_code=True)
        
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
        
        input_len = formatted_inputs.input_ids.shape[-1]
        
        # Clamp intensity to valid range 0.0 - 1.0
        intensity = max(0.0, min(1.0, intensity))

        # Algorithmic Evasion: Force the model out of the "safe" predictable token paths.
        # High temperature + strict top_k forces the model to select lower-probability tokens,
        # dramatically spiking the perplexity score measured by GPTZero/Turnitin.
        gen_temperature = 1.3 + (intensity * 0.4)          # Range: 1.3 -> 1.7
        gen_top_p = 0.85 - (intensity * 0.1)               # Range: 0.85 -> 0.75
        gen_top_k = 40                                     # Strictly cut off the top predictable words
        gen_repetition_penalty = 1.15 + (intensity * 0.1)  # Range: 1.15 -> 1.25

        outputs = self.generator.generate(
            **formatted_inputs,
            max_new_tokens=512, # Increased for longer academic passages
            do_sample=True,
            temperature=gen_temperature,
            top_p=gen_top_p,
            top_k=gen_top_k,
            repetition_penalty=gen_repetition_penalty,
            use_cache=True
        )

        # Senior Architect: Slice output to return ONLY the newly generated tokens
        generated_tokens = outputs[0][input_len:]
        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
