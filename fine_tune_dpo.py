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
from trl import DPOTrainer, DPOConfig

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
DPO_OUTPUT_DIR = "./qwen2-7b-pre-ai-dpo"
DPO_DATASET_PATH = "./dpo_dataset.json"

def train_dpo():
    # Standard DDP initialization for multi-GPU coordination
    if "RANK" in os.environ and not torch.distributed.is_initialized():
        torch.distributed.init_process_group(backend="nccl")
    
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    
    # 2. Quantization Config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load Model
    print(f"[{local_rank}] Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map={"": local_rank},
        dtype=torch.float16,
    )
    model.config.use_cache = False
    
    # Memory safety for T4
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    if os.path.exists(ADAPTER_PATH):
        print(f"[{local_rank}] Loading Phase 3 adapter from {ADAPTER_PATH}...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH, is_trainable=True)
    else:
        print(f"[{local_rank}] Warning: Phase 3 adapter not found. Starting DPO from base model.")
        peft_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_config)

    # 4. Load Dataset (Strict Check)
    if not os.path.exists(DPO_DATASET_PATH):
        raise FileNotFoundError(
            f"DPO dataset not found at {DPO_DATASET_PATH}. "
            "Please run 'python generate_dpo_data.py' before starting DPO training."
        )

    print(f"[{local_rank}] Loading DPO dataset from {DPO_DATASET_PATH}...")
    with open(DPO_DATASET_PATH, "r", encoding="utf-8") as f:
        dpo_data_loaded = json.load(f)
    dataset = Dataset.from_dict(dpo_data_loaded)

    # Reset padding side to right for DPOTrainer training phase
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 5. DPOConfig
    dpo_config = DPOConfig(
        output_dir=DPO_OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-6, 
        num_train_epochs=1,
        logging_steps=1,
        save_steps=50,
        fp16=False,
        bf16=False,
        gradient_checkpointing=True,
        save_total_limit=3,
        report_to="none",
        beta=0.1, 
        max_length=1024,
        remove_unused_columns=False,
        ddp_find_unused_parameters=False,
    )

    # 6. DPO Trainer
    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None, 
        args=dpo_config,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    # 7. Execute DPO
    print(f"[{local_rank}] Starting Phase 4: Detector Penalization (DPO)...")
    dpo_trainer.train()
    
    # 8. Save
    if local_rank == 0:
        dpo_trainer.model.save_pretrained(DPO_OUTPUT_DIR)
        tokenizer.save_pretrained(DPO_OUTPUT_DIR)
        print(f"DPO Training complete. Model saved to {DPO_OUTPUT_DIR}")

if __name__ == "__main__":
    train_dpo()
