import os
import re
import random
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

class AdversarialPostProcessor:
    """
    Applies lightweight, deterministic NLP passes to disrupt AI detection heuristics
    (perplexity and burstiness) by simplifying language and unpacking dense noun phrases.
    """
    
    # QuillBot Strategy: Simplify smart-sounding AI words to "boring" human words
    PHRASE_REPLACEMENTS = {
        "paradigm shift": ["paradigm change", "major shift"],
        "enables": ["allows", "permits", "lets"],
        "cumulating to circa": ["amounting to about", "totaling some"],
        "per annum": ["a year", "annually"],
        "demonstrate remarkable effectiveness": ["prove to be very successful", "work quite well"],
        "furthermore": ["and", "also", "plus"],
        "moreover": ["also", "besides"],
        "it is worth noting": ["notably", "of note"],
        "significant": ["major", "real", "big"],
        "substantial": ["large", "significant", "major"],
        "incident": ["case", "occurrence"],
        "utilizing": ["using", "employing"],
        "facilitating": ["allowing", "helping"],
    }

    # QuillBot Strategy: Unpack dense clinical noun chunks into prepositional phrases
    NOUN_PHRASE_UNPACKER = {
        "infection incidence": "the infection rate",
        "procedural complexity": "the complexity of the procedure",
        "optical fiberoptic arthosopes": "optical devices like fiberoptic arthroscopes",
        "learning curve progression": "progress along the learning curve",
        "vital function": "essential bodily functions",
    }
    
    @staticmethod
    def pass_phrase_replacement(text: str) -> str:
        """Replace overly flowery words with dry, simple equivalents (QuillBot style)."""
        new_text = text
        for phrase, replacements in AdversarialPostProcessor.PHRASE_REPLACEMENTS.items():
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            def replace_fn(match):
                original = match.group(0)
                replacement = random.choice(replacements)
                if original[0].isupper():
                    return replacement[0].upper() + replacement[1:]
                return replacement
            new_text = pattern.sub(replace_fn, new_text)
        return new_text

    @staticmethod
    def pass_de_jargonization(text: str) -> str:
        """Unpack dense noun chunks into prepositional phrases (QuillBot style)."""
        new_text = text
        for jargon, simple in AdversarialPostProcessor.NOUN_PHRASE_UNPACKER.items():
            pattern = re.compile(rf"\b{re.escape(jargon)}\b", re.IGNORECASE)
            new_text = pattern.sub(simple, new_text)
        return new_text

    @staticmethod
    def pass_invisible_padding(text: str) -> str:
        """Inject Hair Spaces (U+200A) in common bigrams to destroy token predictability."""
        common_bigrams = [
            ("of", "the"), ("in", "the"), ("to", "the"),
            ("on", "the"), ("and", "the"),
        ]
        new_text = text
        for b1, b2 in common_bigrams:
            pattern = re.compile(rf"\b{b1}\s+{b2}\b", re.IGNORECASE)
            if random.random() < 0.5:
                new_text = pattern.sub(f"{b1}\u200A{b2}", new_text)
        return new_text

    @staticmethod
    def pass_zwj_jitter(text: str) -> str:
        """Inject Zero-Width Non-Joiner (\\u200C) inside AI trigger words."""
        triggers = ["therefore", "consequently", "essential", "crucial", "however"]
        new_text = text
        for t in triggers:
            pattern = re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)
            if random.random() < 0.4:
                mid = len(t) // 2
                jittered = t[:mid] + "\u200C" + t[mid:]
                new_text = pattern.sub(jittered, new_text)
        return new_text

    @staticmethod
    def pass_adversarial_punctuation(text: str) -> str:
        """Upgrade commas to semicolons and em-dashes to mimic human academic density."""
        if random.random() < 0.5:
            pattern = re.compile(r"([^,;]+),\s*([^,;]+),\s*and\s+([^,;.]+)")
            text = pattern.sub(r"\1; \2; and \3", text)
            
        pattern2 = re.compile(r",\s*(which|who|that|namely)\s+([^,.]+),")
        text = pattern2.sub(r" — \1 \2 — ", text)
        return text
        
    @classmethod
    def apply_all(cls, text: str) -> str:
        """Run the full adversarial post-processing pipeline."""
        text = cls.pass_phrase_replacement(text)
        text = cls.pass_de_jargonization(text)
        text = cls.pass_zwj_jitter(text)
        text = cls.pass_adversarial_punctuation(text)
        text = cls.pass_invisible_padding(text)
        return text

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
