import os
import re
import random
from celery import Celery
import asyncio
from engine import * # Triggers the centralized CVE-2025-32434 bypass
from engine.amr_handler import AMRHandler
from engine.humanizer_engine import HumanizerEngine
from engine.diagnostic_judge import DiagnosticJudge
from engine.post_processor import AdversarialPostProcessor

def extract_acronyms(text):
    """
    Find words with at least 2 uppercase letters (handles VoWiFi, QoS, A-MPDU).
    This ensures technical jargon is locked during humanization.
    """
    # Pattern looks for words that contain at least two uppercase letters anywhere
    words = re.findall(r'\b[A-Za-z0-9\-]+\b', text)
    acronyms = set([w for w in words if len(re.findall(r'[A-Z]', w)) >= 2])
    return ", ".join(acronyms) if acronyms else "None"

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
        print(f"Worker: Processing humanization for text: {text[:50]}...")
        # Step 1: AMR Processing
        print("Worker: Starting AMR Stage...")
        amr_processed_text = amr_handler.humanize_via_amr(text)
        print(f"Worker: AMR Stage Complete. Intermediate text: {amr_processed_text[:50]}...")
        
        # Jargon Lock: Extract acronyms from the AMR processed text to preserve them
        acronym_list = extract_acronyms(amr_processed_text)
        print(f"Worker: Jargon Lock Active. Preserving: {acronym_list}")

        final_text = amr_processed_text
        confidence_score = 0.85
        
        # Step 2: Recursive Refinement
        for attempt in range(2):
            print(f"Worker: Starting LLM Refinement Stage (Attempt {attempt+1})...")
            
            # Use the advanced QuillBot-style simplification prompt
            prompt = f"""Rewrite the following technical text to read naturally and simply, as a human researcher would write it. 

CRITICAL INSTRUCTIONS:
1. Lexical Simplification: Do NOT use a thesaurus. Avoid flowery, overly formal, or rare words (e.g., avoid "circumvent", "paradigm shift", "per annum", "demonstrate remarkable effectiveness"). Use simple, boring, everyday English equivalents (e.g., "avoid", "paradigm change", "per year", "are very successful").
2. Structural Decompression: Do NOT write long, breathless, multi-clause run-on sentences. LLMs string together endless clauses using participles ("categorized as...", "hovering at..."). You must chop long thoughts into shorter, distinct sentences with hard periods.
3. De-Jargonizing Noun Phrases: Unpack dense, clinical "noun chunks" into conversational prepositional phrases (e.g., change "infection incidence" to "the infection rate", or "given procedural complexity" to "depending on the complexity of the procedure").

Retain all original facts, metrics, and technical jargon intact. Do NOT alter or paraphrase the following core technical terms: {acronym_list}

Text: {final_text if attempt > 0 else amr_processed_text}"""

            candidate_text = engine.generate_humanized(prompt, intensity=intensity)
            print(f"Worker: LLM Stage Complete. Candidate: {candidate_text[:50]}...")
            
            print("Worker: Starting Judge Stage...")
            is_human, score = judge.judge(candidate_text, threshold=0.7)
            final_text = candidate_text
            confidence_score = score
            print(f"Worker: Judge Stage Complete. Score: {score}")
            
            if is_human:
                print("Worker: Human threshold met.")
                break
                
        # --- NEW: V1 Adversarial Post-Processing ---
        print("Worker: Applying Adversarial Post-Processing (v1 passes)...")
        final_evaded_text = AdversarialPostProcessor.apply_all(final_text)
                
        return {
            "status": "completed",
            "original": text,
            "amr_intermediate": amr_processed_text,
            "humanized": final_evaded_text,
            "confidence_score": round(confidence_score, 2)
        }
    except Exception as e:
        import traceback
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"CRITICAL WORKER ERROR:\n{err_msg}")
        return {"status": "error", "message": err_msg}
