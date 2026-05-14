import os
os.environ["WANDB_DISABLED"] = "true" # Fix #12: Disable W&B at env level before any imports
os.environ["WANDB_MODE"] = "disabled"

import sys
import types 

# --- HARD MOCK WANDB ---
# Fix #12: Move mock definition and call to the absolute top to intercept TRL's lazy loader
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

# Fix #12: Force clear any cached broken wandb reference
sys.modules.pop("wandb", None)
mock_wandb()
# -----------------------

import json # Fix #9: Required for saving/loading dataset to disk
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
from trl import DPOTrainer, DPOConfig
from engine.diagnostic_judge import DiagnosticJudge

# Configuration
BASE_MODEL_ID = "Qwen/Qwen2-7B-Instruct"
ADAPTER_PATH = "./qwen2-7b-pre-ai-clm" 
DPO_OUTPUT_DIR = "./qwen2-7b-pre-ai-dpo"
DPO_DATASET_PATH = "./dpo_dataset.json" # Fix #9: File path for disk separation

def batched_judge_scoring(judge, candidate_list):
    """Fix #11: Wrap judge scoring in a batching helper to speed up execution."""
    try:
        # Check if judge natively supports batched scoring
        return judge.score_human_confidence(candidate_list)
    except TypeError:
        # Fallback to list comprehension if only single inputs are supported
        return [judge.score_human_confidence(c) for c in candidate_list]

# Fix #9: Separate generation logic into its own function to avoid circularity
def generate_and_save_dpo_dataset(model, tokenizer, judge, num_samples=500): # Fix #5: Increased default to 500
    print(f"Generating DPO dataset with {num_samples} valid samples...")
    
    # Base prompts to "humanize"
    base_prompts = [
        "Artificial intelligence has seen significant advancements in recent years, leading to a paradigm shift in how we process data.",
        "The results demonstrate remarkable effectiveness in reducing infection incidence across all clinical trials.",
        "Furthermore, it is worth noting that utilizing blockchain technology facilitates secure transactions.",
        "The implementation of this methodology enables a substantial increase in procedural efficiency.",
        "Moreover, the data suggests that the proposed solution is highly scalable for large-scale enterprises.",
        "In conclusion, it is essential to consider the implications of these findings for future research.",
    ]
    
    dpo_data = {"prompt": [], "chosen": [], "rejected": []}
    
    # Fix #10: Set left padding strictly for generation phase
    tokenizer.padding_side = "left"
    model.eval()
    
    prompt_idx = 0
    batch_size = 8 # Process prompts in batches for scoring efficiency
    
    # Fix #6: Loop dynamically until num_samples valid pairs are gathered
    while len(dpo_data["prompt"]) < num_samples:
        # Fetch a chunk of prompts from the cyclic pool
        current_prompts = [base_prompts[j % len(base_prompts)] for j in range(prompt_idx, prompt_idx + batch_size)]
        prompt_idx += batch_size
        
        all_candidates = []
        # Generate candidates for the batch
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
        
        # Fix #11: Score the entire candidate batch at once
        all_scores = batched_judge_scoring(judge, all_candidates)
        
        # Process scored candidates back into pairs
        for i, prompt in enumerate(current_prompts):
            c1, c2 = all_candidates[2*i], all_candidates[2*i+1]
            s1, s2 = all_scores[2*i], all_scores[2*i+1]
            
            # Fix #6: Minimum score gap filter to ensure a clear reward signal
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

    # Fix #9: Save generated dataset to disk
    with open(DPO_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(dpo_data, f, indent=2)
    print(f"Dataset successfully saved to {DPO_DATASET_PATH}")

def train_dpo():
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
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    print("Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        quantization_config=bnb_config,
        device_map={"": local_rank},
        dtype=torch.float16, # Fix #7: Replaced torch_dtype with dtype
    )
    model.config.use_cache = False
    # Fix #4: Removed model.config.pretraining_tp = 1 (LLaMA-specific)
    
    # Memory safety for T4
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    if os.path.exists(ADAPTER_PATH):
        print(f"Loading Phase 3 adapter from {ADAPTER_PATH}...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH, is_trainable=True)
    else:
        print("Warning: Phase 3 adapter not found. Starting DPO from base model.")
        peft_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        # Fix #3: Explicitly apply peft_config to the base model in the fallback branch
        model = get_peft_model(model, peft_config)

    # Fix #13: Handle DDP race condition. Only Rank 0 generates data, others wait.
    if local_rank == 0:
        if not os.path.exists(DPO_DATASET_PATH):
            judge = DiagnosticJudge(device="cpu") # CPU to save VRAM for model
            judge.load_model()
            # Fix #4: Explicitly pass 500 samples to ensure the audit fix is applied
            generate_and_save_dpo_dataset(model, tokenizer, judge, num_samples=500)
    
    # Ensure all processes wait until Rank 0 has finished saving the dataset
    if torch.distributed.is_initialized():
        torch.distributed.barrier()
    
    print(f"Loading DPO dataset from {DPO_DATASET_PATH}...")
    with open(DPO_DATASET_PATH, "r", encoding="utf-8") as f:
        dpo_data_loaded = json.load(f)
    dataset = Dataset.from_dict(dpo_data_loaded)

    # Fix #10: Reset padding side to right for DPOTrainer training phase
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 6. DPOConfig
    try:
        dpo_config = DPOConfig(
            output_dir=DPO_OUTPUT_DIR,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            learning_rate=5e-6, 
            num_train_epochs=1,
            logging_steps=1,
            save_steps=50,
            fp16=False, # Fix #2: Disabled fp16 to prevent GradScaler crash with BF16 weights
            bf16=False,
            gradient_checkpointing=True, # Instruction: Keep for T4 memory safety
            save_total_limit=3, # Instruction: Keep for Kaggle disk management
            report_to="none",
            beta=0.1, 
            # Fix #1: Removed max_prompt_length and truncation_mode for max compatibility.
            # max_length=1024 is sufficient for universal TRL versions.
            max_length=1024,
            remove_unused_columns=False,
            ddp_find_unused_parameters=False,
        )
    except TypeError:
        # Fix #1: Helpful debug for future DPOConfig parameter changes
        import inspect
        print("DPOConfig initialization failed. Valid arguments are:")
        print(inspect.signature(DPOConfig.__init__))
        raise

    # 7. DPO Trainer
    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None, # Automatically uses PEFT base as ref
        args=dpo_config,
        train_dataset=dataset,
        processing_class=tokenizer,
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
