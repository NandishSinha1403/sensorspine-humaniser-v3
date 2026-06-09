import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import re
import random
from celery import Celery
from engine import *
from engine.amr_handler import AMRHandler
from engine.humanizer_engine import HumanizerEngine
from engine.diagnostic_judge import DiagnosticJudge
from engine.nlp_post_processor import NLPPostProcessor
from engine.text_protector import (
    has_technical_content,
    protect_spans,
    restore_spans,
    extract_locked_terms,
)

# Speed: single LLM pass per chunk; NLP post-processing does the heavy lifting.
MAX_WORDS_PER_CHUNK = 70


def extract_acronyms(text):
    words = re.findall(r"\b[A-Za-z0-9\-]+\b", text)
    acronyms = {w for w in words if len(re.findall(r"[A-Z]", w)) >= 2}
    return ", ".join(sorted(acronyms)) if acronyms else "None"


def split_sentences(text):
    parts = re.split(
        r"(?<=[.!?])\s+(?=[A-Z\"']|\u27e6)|(?<=[.!?])\s+(?=(?:The|This|These|Advanced|Continuous|Present|During|While)\b)",
        text,
    )
    sentences = [p.strip() for p in parts if p.strip()]

    if len(sentences) <= 1 and len(text.split()) > MAX_WORDS_PER_CHUNK:
        clauses = re.split(r";\s+|,\s+(?=while|whereas|and\s+[A-Z])", text)
        sentences = [c.strip() for c in clauses if c.strip()]

    return sentences if sentences else [text]


def build_chunks(sentences):
    chunks = []
    buffer = []
    for sentence in sentences:
        buffer.append(sentence)
        word_count = len(" ".join(buffer).split())
        if len(buffer) >= 2 or word_count >= MAX_WORDS_PER_CHUNK:
            chunks.append(" ".join(buffer))
            buffer = []
    if buffer:
        chunks.append(" ".join(buffer))
    return chunks


def build_rewrite_prompt(chunk, locked_terms, acronym_list):
    locked = ", ".join(locked_terms) if locked_terms else "None"
    return f"""Edit this academic passage for clarity. Make minimal changes — reorder phrases, vary sentence openings.

Passage:
{chunk}

Rules:
- Keep ALL facts, numbers, equations, and placeholders (⟦PROT#⟧) exactly as written.
- Do NOT change: {locked}
- Do NOT change acronyms: {acronym_list}
- Output only the edited passage. No commentary.
- Avoid: furthermore, moreover, in conclusion, it is worth noting, demonstrates, utilizes."""


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("humanizer_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

worker_state = {"amr_handler": None, "humanizer_engine": None, "judge": None}


def init_worker():
    if worker_state["humanizer_engine"] is None:
        print("Worker: Loading models...")
        worker_state["amr_handler"] = AMRHandler()
        worker_state["humanizer_engine"] = HumanizerEngine()
        worker_state["humanizer_engine"].load_models()
        worker_state["judge"] = DiagnosticJudge(device="cpu")
        worker_state["judge"].load_model()
        print("Worker: Models loaded successfully.")


def prepare_source_text(amr_handler, text):
    protected = protect_spans(text)

    if has_technical_content(text):
        print("Worker: Technical content detected — skipping AMR.")
        return protected.text, protected.spans, protected.text

    print("Worker: Starting AMR Stage...")
    amr_out = amr_handler.humanize_via_amr(protected.text)
    amr_out = restore_spans(amr_out, protected.spans)
    print(f"Worker: AMR complete. Intermediate: {amr_out[:80]}...")
    return amr_out, protected.spans, amr_out


def humanize_text(amr_handler, engine, text, intensity):
    source_text, span_map, amr_intermediate = prepare_source_text(amr_handler, text)
    locked_terms = extract_locked_terms(text)
    acronym_list = extract_acronyms(text)

    sentences = split_sentences(source_text)
    chunks = build_chunks(sentences)
    print(f"Worker: LLM rewrite ({len(chunks)} chunks, single pass each)...")

    humanized_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Worker: Chunk {i + 1}/{len(chunks)}...")
        protected_chunk = protect_spans(chunk)
        prompt = build_rewrite_prompt(protected_chunk.text, locked_terms, acronym_list)

        # Single LLM call per chunk — fast path
        rewritten = engine.generate_humanized(
            prompt,
            intensity=intensity,
            judge=None,
            max_candidates=1,
            reference=chunk,
        )
        rewritten = restore_spans(rewritten, protected_chunk.spans)
        rewritten = restore_spans(rewritten, span_map)
        humanized_chunks.append(rewritten or chunk)

    return " ".join(humanized_chunks), amr_intermediate


@celery_app.task(name="tasks.process_humanization")
def process_humanization(text, intensity):
    init_worker()

    amr_handler = worker_state["amr_handler"]
    engine = worker_state["humanizer_engine"]
    judge = worker_state["judge"]

    try:
        print(f"Worker: Processing humanization for text: {text[:50]}...")
        pass_intensity = max(0.4, min(0.85, float(intensity)))

        llm_text, amr_intermediate = humanize_text(amr_handler, engine, text, pass_intensity)
        pre_nlp_metrics = judge.score_metrics(llm_text)
        print(
            f"Worker: Post-LLM — ai_prob={pre_nlp_metrics['ai_probability']}, "
            f"confidence={pre_nlp_metrics['human_confidence']}"
        )

        print("Worker: Applying humaniser-1 NLP post-processing (CPU)...")
        nlp_seed = hash(text) % (2**31)
        final_evaded_text = NLPPostProcessor.apply_all(
            llm_text, intensity=pass_intensity, seed=nlp_seed
        )

        post_metrics = judge.score_metrics(final_evaded_text)
        print(
            f"Worker: Post-NLP — ai_prob={post_metrics['ai_probability']}, "
            f"confidence={post_metrics['human_confidence']}, "
            f"burst={post_metrics['burstiness']}"
        )

        return {
            "status": "completed",
            "original": text,
            "amr_intermediate": amr_intermediate,
            "humanized": final_evaded_text,
            "confidence_score": round(post_metrics["human_confidence"], 2),
            "diagnostics": {
                "ai_probability": post_metrics["ai_probability"],
                "mean_perplexity": post_metrics["mean_perplexity"],
                "burstiness": post_metrics["burstiness"],
                "sentence_count": post_metrics["sentence_count"],
                "pre_nlp_ai_probability": pre_nlp_metrics["ai_probability"],
            },
        }
    except Exception as e:
        import traceback
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"CRITICAL WORKER ERROR:\n{err_msg}")
        return {"status": "error", "message": err_msg}
