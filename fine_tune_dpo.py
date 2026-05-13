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
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import DPOTrainer
from engine.diagnostic_judge import DiagnosticJudge

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2-7B-Instruct"
# Path to the CLM-fine-tuned adapter from Phase 3
ADAPTER_PATH = "./qwen2-7b-pre-ai-clm" 
DPO_OUTPUT_DIR = "./qwen2-7b-pre-ai-dpo"

def generate_dpo_dataset(model, tokenizer, judge, num_samples=100):
    """
    Generates a DPO dataset by ranking multiple model outputs using the DiagnosticJudge.
    """
    print(f"Generating DPO dataset with {num_samples} samples...")
    
    # Placeholder prompts: In a real run, these would be typical AI-generated academic paragraphs
    prompts = [
        "Artificial intelligence has seen significant advancements in recent years, leading to a paradigm shift in how we process data.",
        "The results demonstrate remarkable effectiveness in reducing infection incidence across all clinical trials.",
        "Furthermore, it is worth noting that utilizing blockchain technology facilitates secure transactions.",
        # ... add more diverse AI-style academic prompts
    ] * (num_samples // 3)

    dpo_data = {
        "prompt": [],
        "chosen": [],
        "rejected": [],
    }

    model.eval()
    for prompt in prompts:
        # Generate 2 candidate responses with different sampling parameters
        candidates = []
        for temp in [0.7, 1.2]:
            inputs = tokenizer(f"Humanize this: {prompt}", return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=temp)
                candidate = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
                candidates.append(candidate)
        
        # Score candidates using the DiagnosticJudge
        scores = [judge.score_human_confidence(c) for c in candidates]
        
        # Pair them as Chosen (higher human score) vs Rejected (lower human score)
        if scores[0] > scores[1]:
            chosen, rejected = candidates[0], candidates[1]
        else:
            chosen, rejected = candidates[1], candidates[0]
            
        # Only add if there's a significant difference or to establish a preference
        dpo_data["prompt"].append(prompt)
        dpo_data["chosen"].append(chosen)
        dpo_data["rejected"].append(rejected)

    return Dataset.from_dict(dpo_data)

def train_dpo():
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token

    # 2. Quantization Config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )

    # 3. Load Base Model + Phase 3 Adapter
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    # If the adapter exists, we'd load it here. For the script, we assume it's merged or ready.
    # model = PeftModel.from_pretrained(model, ADAPTER_PATH)

    # 4. Load Detector Judge (Runs on CPU to save VRAM)
    judge = DiagnosticJudge(device="cpu")
    judge.load_model()

    # 5. Build DPO Dataset
    dataset = generate_dpo_dataset(model, tokenizer, judge)

    # 6. LoRA Config for DPO
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 7. Training Arguments
    training_args = TrainingArguments(
        output_dir=DPO_OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        num_train_epochs=1,
        logging_steps=1,
        save_steps=50,
        fp16=True,
        report_to="none",
    )

    # 8. DPO Trainer
    dpo_trainer = DPOTrainer(
        model,
        args=training_args,
        beta=0.1, # Temperature parameter for DPO
        train_dataset=dataset,
        tokenizer=tokenizer,
        peft_config=peft_config,
    )

    # 9. Execute DPO
    print("Starting Phase 4: Detector Penalization (DPO)...")
    dpo_trainer.train()
    
    # 10. Save
    dpo_trainer.model.save_pretrained(DPO_OUTPUT_DIR)
    print(f"DPO Training complete. Model saved to {DPO_OUTPUT_DIR}")

if __name__ == "__main__":
    train_dpo()
