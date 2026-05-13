import os
import sys
import types

# --- HARD MOCK WANDB ---
# Kaggle's system wandb/protobuf is broken. This mock satisfies all internal 
# Python import checks (including __spec__) to prevent hard crashes.
def mock_wandb():
    m = types.ModuleType("wandb")
    m.__version__ = "9.9.9"
    m.__path__ = []
    m.__file__ = "mock_wandb.py"
    
    class SDK:
        pass
    m.sdk = SDK()
    
    def dummy(*args, **kwargs): return None
    m.init = dummy
    m.log = dummy
    m.finish = dummy
    m.login = dummy
    
    # Satisfy importlib / PEP 451
    import importlib.machinery
    m.__spec__ = importlib.machinery.ModuleSpec("wandb", None)
    
    sys.modules["wandb"] = m

mock_wandb()
# -----------------------

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# Configuration
MODEL_ID = "Qwen/Qwen2-7B-Instruct"
CLEANED_CORPUS_DIR = "./cleaned_corpus"
OUTPUT_DIR = "./qwen2-7b-pre-ai-clm"
BLOCK_SIZE = 1024  # Max context window for chunks

def load_cleaned_corpus():
    """Load all .txt files from the cleaned_corpus directory."""
    all_text = []
    files = [f for f in os.listdir(CLEANED_CORPUS_DIR) if f.endswith(".txt")]
    print(f"Loading {len(files)} cleaned files...")
    
    for filename in files:
        with open(os.path.join(CLEANED_CORPUS_DIR, filename), "r", encoding="utf-8") as f:
            all_text.append(f.read())
            
    # Create a Dataset object
    dataset = Dataset.from_dict({"text": all_text})
    return dataset

def train():
    # 1. Load Dataset
    dataset = load_cleaned_corpus()
    
    # 2. Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 3. Quantization Config for T4/Kaggle
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    # 4. Load Model
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        dtype=torch.float16, 
        trust_remote_code=True,
    )
    model.config.use_cache = False # Disable for training
    model.config.pretraining_tp = 1
    model = prepare_model_for_kbit_training(model)

    # 5. LoRA Config
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    # NOTE: Do NOT call get_peft_model(model, peft_config) manually. 
    # SFTTrainer handles this internally.

    # 6. SFTConfig (The modern way to pass arguments to SFTTrainer)
    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR,
        dataset_text_field="text",
        max_length=BLOCK_SIZE,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=10,
        num_train_epochs=3,
        save_steps=100,
        fp16=True,  # Enable standard float16
        bf16=False, # Explicitly disable bfloat16 for T4
        push_to_hub=False,
        report_to="none",
        optim="paged_adamw_8bit",
    )

    # 7. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        processing_class=tokenizer,
        args=sft_config,
        peft_config=peft_config,
    )

    # 8. Start Training
    print("Starting Phase 3: CLM Fine-Tuning...")
    trainer.train()
    
    # 9. Save final model
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Training complete. Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    if not os.listdir(CLEANED_CORPUS_DIR):
        print("Error: No cleaned text files found. Run preprocess_papers.py first.")
    else:
        train()
