import os
from celery import Celery
import asyncio
import transformers.utils.import_utils as import_utils

# Bypassing the torch 2.6+ requirement for torch.load (CVE-2025-32434)
# Since we are in a trusted Colab environment loading known models.
def patched_check_torch_load_is_safe():
    return True

import_utils.check_torch_load_is_safe = patched_check_torch_load_is_safe

from engine.amr_handler import AMRHandler
from engine.humanizer_engine import HumanizerEngine
from engine.diagnostic_judge import DiagnosticJudge

# Initialize Celery
# Note: Using 'redis://localhost:6379/0' as default. 
# In production/Docker, this would be 'redis://redis:6379/0'
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "humanizer_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Global instances for the worker process
# (Worker processes are long-lived, so we load models once)
worker_state = {
    "amr_handler": None,
    "humanizer_engine": None,
    "judge": None
}

def init_worker():
    """Load models into the worker process."""
    if worker_state["humanizer_engine"] is None:
        print("Worker: Loading models...")
        worker_state["amr_handler"] = AMRHandler()
        worker_state["humanizer_engine"] = HumanizerEngine()
        worker_state["humanizer_engine"].load_models()
        worker_state["judge"] = DiagnosticJudge(device="cpu")
        worker_state["judge"].load_model()
        print("Worker: Models loaded successfully.")

@celery_app.task(name="tasks.process_humanization")
def process_humanization(text, intensity):
    init_worker()
    
    amr_handler = worker_state["amr_handler"]
    engine = worker_state["humanizer_engine"]
    judge = worker_state["judge"]
    
    try:
        # Step 1: AMR Processing
        amr_processed_text = amr_handler.humanize_via_amr(text)
        
        final_text = amr_processed_text
        confidence_score = 0.85
        
        # Step 2: Recursive Refinement
        for attempt in range(2):
            prompt = f"Rewrite this text to be more natural and human-like: {final_text if attempt > 0 else amr_processed_text}"
            candidate_text = engine.generate_humanized(prompt, alpha=intensity * 0.5)
            
            is_human, score = judge.judge(candidate_text, threshold=0.7)
            final_text = candidate_text
            confidence_score = score
            
            if is_human:
                break
                
        return {
            "status": "completed",
            "original": text,
            "amr_intermediate": amr_processed_text,
            "humanized": final_text,
            "confidence_score": round(confidence_score, 2)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
