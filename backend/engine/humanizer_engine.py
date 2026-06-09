import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


class HumanizerEngine:
    def __init__(self, generator_id="Qwen/Qwen2-7B-Instruct"):
        self.generator_id = generator_id
        self.generator = None
        self.tokenizer = None
        self.adapter_id = "qwen2-7b-pre-ai-dpo"

    def _resolve_adapter_path(self):
        candidates = [
            self.adapter_id,
            f"../{self.adapter_id}",
            f"../../{self.adapter_id}",
            os.path.join(os.getcwd(), self.adapter_id),
        ]
        for path in candidates:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        return None

    def load_models(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            llm_int8_enable_fp32_cpu_offload=True,
        )

        attn_impl = "sdpa"
        print(f"Loading generator: {self.generator_id} using {attn_impl}")

        base_model = AutoModelForCausalLM.from_pretrained(
            self.generator_id,
            quantization_config=bnb_config,
            device_map="auto",
            dtype=torch.float16,
            attn_implementation=attn_impl,
            trust_remote_code=True,
        )

        adapter_path = self._resolve_adapter_path()
        if adapter_path:
            print(f"Engine: DPO adapter found at {adapter_path}.")
            self.generator = PeftModel.from_pretrained(base_model, adapter_path)
            self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
        else:
            print("Engine: No DPO adapter found. Using base model.")
            self.generator = base_model
            self.tokenizer = AutoTokenizer.from_pretrained(self.generator_id, trust_remote_code=True)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _encode_chat(self, prompt: str) -> tuple[torch.Tensor, int]:
        chat = [{"role": "user", "content": prompt}]
        input_ids = self.tokenizer.apply_chat_template(
            chat,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        if not isinstance(input_ids, torch.Tensor):
            input_ids = input_ids["input_ids"]

        input_ids = input_ids.to(self.generator.device)
        return input_ids, input_ids.shape[-1]

    def _generate_once(self, prompt: str, intensity: float, temperature: float) -> str:
        input_ids, input_len = self._encode_chat(prompt)

        # min_p pushes sampling into the "human tail" of the distribution.
        min_p = 0.04 + (intensity * 0.08)
        top_p = max(0.82, 0.98 - (intensity * 0.12))
        repetition_penalty = 1.08 + (intensity * 0.06)

        outputs = self.generator.generate(
            input_ids,
            max_new_tokens=384,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            min_p=min_p,
            repetition_penalty=repetition_penalty,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        generated_tokens = outputs[0][input_len:]
        text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        return self._clean_output(text)

    @staticmethod
    def _clean_output(text: str) -> str:
        """Strip common instruction-leakage patterns from model output."""
        leak_markers = [
            "here's a rewritten",
            "here is a rewritten",
            "rewritten version:",
            "humanized version:",
            "local target",
            "global context",
        ]
        lower = text.lower()
        for marker in leak_markers:
            idx = lower.find(marker)
            if idx != -1:
                text = text[:idx].strip()
                lower = text.lower()

        # Keep only the first paragraph if the model continues with commentary.
        if "\n\n" in text:
            text = text.split("\n\n")[0].strip()
        return text

    def generate_humanized(self, prompt, intensity=0.5, judge=None, max_candidates=3):
        """
        Contrastive-style selection: sample multiple candidates with varied
        temperatures, then pick the one with the best GPT-2 perplexity profile.
        """
        if not self.generator:
            self.load_models()

        intensity = max(0.0, min(1.0, intensity))
        base_temp = 1.0 + (intensity * 0.35)
        temperatures = [
            base_temp,
            base_temp + 0.15,
            base_temp + 0.3,
        ][:max_candidates]

        candidates = []
        for temp in temperatures:
            candidate = self._generate_once(prompt, intensity=intensity, temperature=temp)
            if candidate:
                candidates.append(candidate)

        if not candidates:
            return ""

        if judge is None:
            return candidates[0]

        best_text, _ = judge.pick_best_candidate(candidates)
        return best_text
