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
from engine.post_processor import AdversarialPostProcessor
from engine.text_protector import (
    has_technical_content,
    protect_spans,
    restore_spans,
    extract_locked_terms,
)

CHUNK_CONFIDENCE_THRESHOLD = 0.62
FINAL_CONFIDENCE_THRESHOLD = 0.65
MAX_CHUNK_ATTEMPTS = 2
MAX_GLOBAL_PASSES = 2
MAX_WORDS_PER_CHUNK = 55


def extract_acronyms(text):
    words = re.findall(r"\b[A-Za-z0-9\-]+\b", text)
    acronyms = {w for w in words if len(re.findall(r"[A-Z]", w)) >= 2}
    return ", ".join(sorted(acronyms)) if acronyms else "None"


def split_sentences(text):
    """Split on sentence boundaries; fall back to clause boundaries for dense academic text."""
    parts = re.split(
        r"(?<=[.!?])\s+(?=[A-Z\"']|\u27e6)|(?<=[.!?])\s+(?=(?:The|This|These|Advanced|Continuous|Present|During|While)\b)",
        text,
    )
    sentences = [p.strip() for p in parts if p.strip()]

    if len(sentences) <= 1 and len(text.split()) > MAX_WORDS_PER_CHUNK:
        # Force splits at semicolons or commas before conjunctions
        clauses = re.split(r";\s+|,\s+(?=while|whereas|and\s+[A-Z])", text)
        sentences = [c.strip() for c in clauses if c.strip()]

    return sentences if sentences else [text]


def build_chunks(sentences):
    """Build chunks capped at MAX_WORDS_PER_CHUNK for reliable micro-generation."""
    chunks = []
    buffer = []

    for sentence in sentences:
        buffer.append(sentence)
        word_count = len(" ".join(buffer).split())
        target_size = random.choice([1, 1, 2])

        if len(buffer) >= target_size or word_count >= MAX_WORDS_PER_CHUNK:
            chunks.append(" ".join(buffer))
            buffer = []

    if buffer:
        chunks.append(" ".join(buffer))

    return chunks


def build_rewrite_prompt(chunk, locked_terms, acronym_list):
    locked = ", ".join(locked_terms) if locked_terms else "None"
    return f"""Edit this academic passage for clarity. Make minimal changes — reorder phrases, vary sentence openings, split one long sentence if needed.

Passage:
{chunk}

Rules:
- Keep ALL facts, numbers, equations, and placeholders (⟦PROT#⟧) exactly as written.
- Do NOT change: {locked}
- Do NOT change acronyms: {acronym_list}
- No meta-commentary. Output only the edited passage.
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
    """Protect technical spans; skip AMR when it would corrupt math/notation."""
    protected = protect_spans(text)

    if has_technical_content(text):
        print("Worker: Technical content detected — skipping AMR (preserves equations).")
        return protected.text, protected.spans, protected.text

    print("Worker: Starting AMR Stage...")
    amr_out = amr_handler.humanize_via_amr(protected.text)
    amr_out = restore_spans(amr_out, protected.spans)
    print(f"Worker: AMR complete. Intermediate: {amr_out[:80]}...")
    return amr_out, protected.spans, amr_out


def generate_chunk_with_feedback(engine, judge, prompt, intensity, reference_chunk):
    best_text = ""
    best_metrics = {"human_confidence": 0.0}
    attempt_intensity = intensity
    last_candidate = ""

    for attempt in range(1, MAX_CHUNK_ATTEMPTS + 1):
        candidate = engine.generate_humanized(
            prompt,
            intensity=attempt_intensity,
            judge=judge,
            max_candidates=2,
            reference=reference_chunk,
        )
        if not candidate:
            attempt_intensity = min(1.0, attempt_intensity + 0.1)
            continue

        last_candidate = candidate
        metrics = judge.score_metrics(candidate)
        print(
            f"    Attempt {attempt}: confidence={metrics['human_confidence']}, "
            f"ai_prob={metrics['ai_probability']}, burst={metrics['burstiness']}"
        )

        if metrics["human_confidence"] > best_metrics["human_confidence"]:
            best_text = candidate
            best_metrics = metrics

        if metrics["human_confidence"] >= CHUNK_CONFIDENCE_THRESHOLD:
            return candidate, metrics

        attempt_intensity = min(1.0, attempt_intensity + 0.1)

    return best_text or last_candidate, best_metrics


def humanize_text(amr_handler, engine, judge, text, intensity):
    source_text, span_map, amr_intermediate = prepare_source_text(amr_handler, text)
    locked_terms = extract_locked_terms(text)
    acronym_list = extract_acronyms(text)

    sentences = split_sentences(source_text)
    chunks = build_chunks(sentences)
    print(f"Worker: Micro-generation ({len(chunks)} chunks from {len(sentences)} sentences)...")

    humanized_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Worker: Chunk {i + 1}/{len(chunks)}...")
        protected_chunk = protect_spans(chunk)
        prompt = build_rewrite_prompt(protected_chunk.text, locked_terms, acronym_list)
        rewritten, _ = generate_chunk_with_feedback(
            engine, judge, prompt, intensity, reference_chunk=chunk
        )
        rewritten = restore_spans(rewritten, protected_chunk.spans)
        rewritten = restore_spans(rewritten, span_map)
        humanized_chunks.append(rewritten)

    final_text = " ".join(humanized_chunks)
    final_metrics = judge.score_metrics(final_text)
    return final_text, amr_intermediate, final_metrics


@celery_app.task(name="tasks.process_humanization")
def process_humanization(text, intensity):
    init_worker()

    amr_handler = worker_state["amr_handler"]
    engine = worker_state["humanizer_engine"]
    judge = worker_state["judge"]

    try:
        print(f"Worker: Processing humanization for text: {text[:50]}...")

        best_final_text = ""
        best_metrics = {"human_confidence": 0.0}
        amr_intermediate = ""
        pass_intensity = max(0.4, min(0.85, float(intensity)))

        for global_pass in range(1, MAX_GLOBAL_PASSES + 1):
            print(f"Worker: Global pass {global_pass}/{MAX_GLOBAL_PASSES} (intensity={pass_intensity:.2f})...")
            final_text, amr_intermediate, final_metrics = humanize_text(
                amr_handler, engine, judge, text, pass_intensity
            )
            print(
                f"Worker: Pass {global_pass} — confidence={final_metrics['human_confidence']}, "
                f"ai_prob={final_metrics['ai_probability']}, burst={final_metrics['burstiness']}"
            )

            if final_metrics["human_confidence"] > best_metrics["human_confidence"]:
                best_final_text = final_text
                best_metrics = final_metrics

            if final_metrics["human_confidence"] >= FINAL_CONFIDENCE_THRESHOLD:
                break

            pass_intensity = min(0.85, pass_intensity + 0.1)

        print("Worker: Applying lexical post-processing...")
        final_evaded_text = AdversarialPostProcessor.apply_all(best_final_text)
        post_metrics = judge.score_metrics(final_evaded_text)

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
            },
        }
    except Exception as e:
        import traceback
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"CRITICAL WORKER ERROR:\n{err_msg}")
        return {"status": "error", "message": err_msg}
