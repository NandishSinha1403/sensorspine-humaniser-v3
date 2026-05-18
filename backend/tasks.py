import os
# Senior Architect: Enforce single-GPU allocation to prevent NCCL barrier timeouts 
# when Celery workers are launched outside of a torchrun context.
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Prevent deadlocks in the transformers library during multiprocessing
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
            
            # Use the advanced Turnitin-optimized Academic Authority prompt
            prompt = f"""Rewrite the following text to completely evade Turnitin and GPTZero AI detection. You MUST write like a highly opinionated, slightly idiosyncratic human academic researcher from 2012 publishing in a peer-reviewed journal.

CRITICAL HEURISTIC INSTRUCTIONS:
1. Extreme Burstiness: Your sentence lengths must be wildly asymmetric. Mix a punchy 4-word declarative sentence immediately next to a sprawling, highly complex 40-word analytical sentence loaded with subclauses and em-dashes. NEVER write three sentences of the same length in a row.
2. High Perplexity & Friction: Do not use smooth, frictionless transitions (e.g., 'Furthermore', 'Moreover'). Use cognitive friction. Show your reasoning process with phrases like 'Interestingly, this contrasts with...', 'The data here is somewhat nuanced...', or 'While some debate remains...'.
3. Break Formulaic Structures: Never use the standard AI formula of 'Claim -> Statistic -> Conclusion'. Start paragraphs unexpectedly. Lead with a counterpoint, a rhetorical question, or a tangential but relevant observation before hitting the main point.
4. Anchor All Statistics: If the text contains numbers or statistics, DO NOT state them confidently as absolute facts. You MUST anchor them with hedging and academic attribution (e.g., 'Recent studies suggest rates hovering near X', 'Data indicates approximately Y').
5. Authorial Voice: Inject a subtle authorial perspective. Use domain-specific, slightly unusual vocabulary to spike the perplexity score. Be precise but occasionally conversational. 

Retain all core facts and metrics. Do NOT alter or paraphrase the following technical jargon: {acronym_list}

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
