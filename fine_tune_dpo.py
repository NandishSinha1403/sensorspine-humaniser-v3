import os
import sys
import types

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

mock_wandb()
# -----------------------

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from trl import DPOTrainer, DPOConfig
from engine.diagnostic_judge import DiagnosticJudge

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2-7B-Instruct"
# Path to the CLM-fine-tuned adapter from Phase 3
ADAPTER_PATH = "./qwen2-7b-pre-ai-clm" 
DPO_OUTPUT_DIR = "./qwen2-7b-pre-ai-dpo"

def generate_dpo_dataset(model, tokenizer, judge, num_samples=50):
    """
    Generates a DPO dataset by ranking multiple model outputs using the DiagnosticJudge.
    """
    print(f"Generating DPO dataset with {num_samples} samples...")
    
    # Typical AI-generated academic paragraphs to "humanize"
    prompts = [
        "Artificial intelligence has seen significant advancements in recent years, leading to a paradigm shift in how we process data.",
        "The results demonstrate remarkable effectiveness in reducing infection incidence across all clinical trials.",
        "Furthermore, it is worth noting that utilizing blockchain technology facilitates secure transactions.",
        "The implementation of this methodology enables a substantial increase in procedural efficiency.",
        "Moreover, the data suggests that the proposed solution is highly scalable for large-scale enterprises.",
        "In conclusion, it is essential to consider the implications of these findings for future research.",
    ] * (num_samples // 6 + 1)
    prompts = prompts[:num_samples]

    dpo_data = {
        "prompt": [],
        "chosen": [],
        "rejected": [],
    }

    model.eval()
    for i, prompt in enumerate(prompts):
        if i % 5 == 0: print(f"  Progress: {i}/{num_samples}")
        
        # Generate 2 candidate responses with different sampling parameters
        candidates = []
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
                # Decode only the generated part
                candidate = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
                candidates.append(candidate.strip())
        
        # Score candidates using the DiagnosticJudge
        scores = [judge.score_human_confidence(c) for c in candidates]
        
        # Pair them as Chosen (higher human score) vs Rejected (lower human score)
        if scores[0] >= scores[1]:
            chosen, rejected = candidates[0], candidates[1]
        else:
            chosen, rejected = candidates[1], candidates[0]
            
        dpo_data["prompt"].append(prompt)
        dpo_data["chosen"].append(chosen)
        dpo_data["rejected"].append(rejected)

    return Dataset.from_dict(dpo_data)

def train_dpo():
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left" # DPO generation often prefers left padding

    # 2. Quantization Config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load Base Model + Phase 3 Adapter
    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.float16,
    )
    
    if os.path.exists(ADAPTER_PATH):
        print(f"Loading Phase 3 adapter from {ADAPTER_PATH}...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH, is_trainable=True)
    else:
        print("Warning: Phase 3 adapter not found. Starting DPO from base model.")
        # If no adapter, we need to wrap it in a new LoRA config
        peft_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_config)

    # 4. Load Detector Judge (Runs on CPU to save VRAM)
    judge = DiagnosticJudge(device="cpu")
    judge.load_model()

    # 5. Build DPO Dataset
    dataset = generate_dpo_dataset(model, tokenizer, judge)

    # 6. DPOConfig
    dpo_config = DPOConfig(
        output_dir=DPO_OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-6, # DPO needs a lower learning rate
        num_train_epochs=1,
        logging_steps=1,
        save_steps=50,
        fp16=True,
        report_to="none",
        beta=0.1, # DPO temperature
        max_prompt_length=512,
        max_length=1024,
        remove_unused_columns=False,
    )

    # 7. DPO Trainer
    # We pass the same model as 'model' and 'ref_model' is None.
    # DPOTrainer will automatically use the PEFT model with the adapter disabled as the reference.
    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=dpo_config,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )

    # 8. Execute DPO
    print("Starting Phase 4: Detector Penalization (DPO)...")
    dpo_trainer.train()
    
    # 9. Save
    dpo_trainer.model.save_pretrained(DPO_OUTPUT_DIR)
    tokenizer.save_pretrained(DPO_OUTPUT_DIR)
    print(f"DPO Training complete. Model saved to {DPO_OUTPUT_DIR}")

if __name__ == "__main__":
    train_dpo()
