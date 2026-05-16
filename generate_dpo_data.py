import os
os.environ["WANDB_DISABLED"] = "true"
os.environ["WANDB_MODE"] = "disabled"

import sys
import types 
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from engine.diagnostic_judge import DiagnosticJudge

# --- HARD MOCK WANDB ---
def mock_wandb():
    m = types.ModuleType("wandb")
    m.__version__ = "9.9.9"
    m.__path__ = []
    m.__file__ = "mock_wandb.py"
    class SDK: pass
    m.sdk = SDK()
    def dummy(*args, **kwargs): return None
    m.init = dummy
    m.log = dummy
    m.finish = dummy
    m.login = dummy
    import importlib.machinery
    m.__spec__ = importlib.machinery.ModuleSpec("wandb", None)
    sys.modules["wandb"] = m

sys.modules.pop("wandb", None)
mock_wandb()
# -----------------------

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2-7B-Instruct"
ADAPTER_PATH = "./qwen2-7b-pre-ai-clm" 
DPO_DATASET_PATH = "./dpo_dataset.json"

def batched_judge_scoring(judge, candidate_list):
    """Wrap judge scoring in a batching helper to speed up execution."""
    try:
        return judge.score_human_confidence(candidate_list)
    except TypeError:
        return [judge.score_human_confidence(c) for c in candidate_list]

def generate_and_save_dpo_dataset(model, tokenizer, judge, num_samples=500):
    print(f"Generating DPO dataset with {num_samples} valid samples...")
    
    base_prompts = [
        "Artificial intelligence has seen significant advancements in recent years, leading to a paradigm shift in how we process data.",
        "The results demonstrate remarkable effectiveness in reducing infection incidence across all clinical trials.",
        "Furthermore, it is worth noting that utilizing blockchain technology facilitates secure transactions.",
        "The implementation of this methodology enables a substantial increase in procedural efficiency.",
        "Moreover, the data suggests that the proposed solution is highly scalable for large-scale enterprises.",
        "In conclusion, it is essential to consider the implications of these findings for future research.",
    ]
    
    dpo_data = {"prompt": [], "chosen": [], "rejected": []}
    tokenizer.padding_side = "left"
    model.eval()
    
    prompt_idx = 0
    batch_size = 8 
    
    while len(dpo_data["prompt"]) < num_samples:
        current_prompts = [base_prompts[j % len(base_prompts)] for j in range(prompt_idx, prompt_idx + batch_size)]
        prompt_idx += batch_size
        
        all_candidates = []
        for prompt in current_prompts:
            for temp in [0.7, 1.2]:
                full_prompt = f"Humanize this: {prompt}"
                inputs = tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs, 
                        max_new_tokens=128, 
                        do_sample=True, 
                        temperature=temp,
                        pad_token_id=tokenizer.eos_token_id
                    )
                candidate = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
                all_candidates.append(candidate.strip())
        
        all_scores = batched_judge_scoring(judge, all_candidates)
        
        for i, prompt in enumerate(current_prompts):
            c1, c2 = all_candidates[2*i], all_candidates[2*i+1]
            s1, s2 = all_scores[2*i], all_scores[2*i+1]
            
            if abs(s1 - s2) < 0.1:
                continue
            
            if s1 >= s2:
                chosen, rejected = c1, c2
            else:
                chosen, rejected = c2, c1
                
            dpo_data["prompt"].append(prompt)
            dpo_data["chosen"].append(chosen)
            dpo_data["rejected"].append(rejected)
            
            if len(dpo_data["prompt"]) >= num_samples:
                break
                
        print(f"  Progress: {len(dpo_data['prompt'])}/{num_samples} valid pairs collected.")

    with open(DPO_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(dpo_data, f, indent=2)
    print(f"Dataset successfully saved to {DPO_DATASET_PATH}")

def main():
    print("Initializing dataset generation...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    print("Loading model for generation...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.float16,
    )
    
    if os.path.exists(ADAPTER_PATH):
        print(f"Loading Phase 3 adapter from {ADAPTER_PATH}...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    
    judge = DiagnosticJudge(device="cpu")
    judge.load_model()
    
    generate_and_save_dpo_dataset(model, tokenizer, judge, num_samples=500)

if __name__ == "__main__":
    main()
