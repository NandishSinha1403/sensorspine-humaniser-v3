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
        
        # Jargon Lock: Extract acronyms from the ORIGINAL text to preserve them
        acronym_list = extract_acronyms(text)
        print(f"Worker: Jargon Lock Active. Preserving: {acronym_list}")

        # Step 1: AMR Processing
        print("Worker: Starting AMR Stage...")
        amr_processed_text = amr_handler.humanize_via_amr(text)
        print(f"Worker: AMR Stage Complete. Intermediate text: {amr_processed_text[:50]}...")

        final_text = amr_processed_text
        confidence_score = 0.85
        
        # Step 2: Sentence-Level Micro-Generation
        # Senior Architect: Instead of bulk-rewriting (which allows for smooth AI-like flow),
        # we process 2 sentences at a time. This introduces "structural friction" and
        # disrupts the global statistical signature while maintaining meaning via context injection.
        
        # Robust sentence splitter (splits on period/question/exclamation followed by space and Capital)
        # Prevents splitting on decimals (1.5) or abbreviations (e.g.,)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', amr_processed_text) if s.strip()]
        chunks = [" ".join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]
        
        print(f"Worker: Starting Micro-Generation stage ({len(chunks)} chunks)...")
        humanized_chunks = []
        
        for i, chunk in enumerate(chunks):
            print(f"Worker: Processing humanization for Chunk {i+1}/{len(chunks)}...")
            
            # Use the "Dry Empirical" prompt style with Global Context awareness
            prompt = f"""Rewrite the following small chunk of technical text to evade AI detection. 

GLOBAL CONTEXT (The full paragraph for reference - do NOT rewrite this):
{amr_processed_text}

LOCAL TARGET (Rewrite ONLY this specific part to be more human-like):
{chunk}

CRITICAL HEURISTIC INSTRUCTIONS:
1. ZERO Metaphors or Ornate Language: NEVER use flowery adjectives, metaphors, or dramatic phrasing. Use plain, clinical, literal terminology.
2. Clinical Imperfection: Focus on the data. Mix blunt factual statements with functional clauses. It is okay if the flow feels disjointed.
3. Factual Anchoring: State statistics plainly (e.g., 'Data indicates rates are ~1%').
4. Absolute Objectivity: Remove all traces of narrative or storytelling.

Retain all core facts and metrics. Do NOT alter or paraphrase the following technical jargon: {acronym_list}"""

            candidate_chunk = engine.generate_humanized(prompt, intensity=intensity)
            humanized_chunks.append(candidate_chunk)
            
        final_text = " ".join(humanized_chunks)
        print("Worker: Micro-Generation complete. Stitching result...")

        # Final Judge stage on the stitched result
        print("Worker: Starting Judge Stage...")
        is_human, confidence_score = judge.judge(final_text, threshold=0.7)
        print(f"Worker: Judge Stage Complete. Human Confidence Score: {confidence_score}")
                
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
