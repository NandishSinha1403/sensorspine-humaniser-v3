import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import re
import random
from celery import Celery
from engine import *  # CVE-2025-32434 bypass
from engine.amr_handler import AMRHandler
from engine.humanizer_engine import HumanizerEngine
from engine.diagnostic_judge import DiagnosticJudge
from engine.post_processor import AdversarialPostProcessor

CHUNK_CONFIDENCE_THRESHOLD = 0.50
FINAL_CONFIDENCE_THRESHOLD = 0.58
MAX_CHUNK_ATTEMPTS = 3
MAX_GLOBAL_PASSES = 2


def extract_acronyms(text):
    words = re.findall(r"\b[A-Za-z0-9\-]+\b", text)
    acronyms = {w for w in words if len(re.findall(r"[A-Z]", w)) >= 2}
    return ", ".join(sorted(acronyms)) if acronyms else "None"


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text) if s.strip()]


def build_variable_chunks(sentences):
    """Variable chunk sizes (1–3 sentences) to increase structural burstiness."""
    chunks = []
    i = 0
    while i < len(sentences):
        size = random.choice([1, 2, 2, 3])
        chunk = " ".join(sentences[i : i + size])
        if chunk:
            chunks.append(chunk)
        i += size
    return chunks


def build_rewrite_prompt(chunk, full_context, acronym_list):
    return f"""You are editing a research manuscript. Rewrite ONLY the passage below.

Full paragraph (reference only — do not rewrite):
{full_context}

Passage to rewrite:
{chunk}

Requirements:
- Preserve every fact, number, citation, and technical term exactly.
- Do not change or paraphrase these terms: {acronym_list}
- Use direct, academic prose. Short sentences are fine next to longer ones.
- Avoid stock transitions (furthermore, moreover, in conclusion, it is worth noting).
- Do not add commentary, labels, or meta text. Output only the rewritten passage."""


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "humanizer_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

worker_state = {
    "amr_handler": None,
    "humanizer_engine": None,
    "judge": None,
}


def init_worker():
    if worker_state["humanizer_engine"] is None:
        print("Worker: Loading models...")
        worker_state["amr_handler"] = AMRHandler()
        worker_state["humanizer_engine"] = HumanizerEngine()
        worker_state["humanizer_engine"].load_models()
        worker_state["judge"] = DiagnosticJudge(device="cpu")
        worker_state["judge"].load_model()
        print("Worker: Models loaded successfully.")


def generate_chunk_with_feedback(engine, judge, prompt, intensity):
    """Generate a chunk, retrying with higher intensity if perplexity score is low."""
    best_text = ""
    best_metrics = {"human_confidence": 0.0}
    attempt_intensity = intensity
    last_candidate = ""

    for attempt in range(1, MAX_CHUNK_ATTEMPTS + 1):
        candidate = engine.generate_humanized(
            prompt,
            intensity=attempt_intensity,
            judge=judge,
            max_candidates=3,
        )
        if not candidate:
            attempt_intensity = min(1.0, attempt_intensity + 0.12)
            continue

        last_candidate = candidate
        metrics = judge.score_metrics(candidate)
        print(
            f"    Attempt {attempt}: confidence={metrics['human_confidence']}, "
            f"ppl={metrics['mean_perplexity']}, burst={metrics['burstiness']}"
        )

        if metrics["human_confidence"] > best_metrics["human_confidence"]:
            best_text = candidate
            best_metrics = metrics

        if metrics["human_confidence"] >= CHUNK_CONFIDENCE_THRESHOLD:
            return candidate, metrics

        attempt_intensity = min(1.0, attempt_intensity + 0.12)

    return best_text or last_candidate, best_metrics


def humanize_text(amr_handler, engine, judge, text, intensity):
    acronym_list = extract_acronyms(text)

    print("Worker: Starting AMR Stage...")
    amr_processed_text = amr_handler.humanize_via_amr(text)
    print(f"Worker: AMR complete. Intermediate: {amr_processed_text[:80]}...")

    sentences = split_sentences(amr_processed_text)
    if not sentences:
        sentences = [amr_processed_text]

    chunks = build_variable_chunks(sentences)
    print(f"Worker: Micro-generation ({len(chunks)} variable chunks)...")

    humanized_chunks = []
    chunk_metrics = []

    for i, chunk in enumerate(chunks):
        print(f"Worker: Chunk {i + 1}/{len(chunks)}...")
        prompt = build_rewrite_prompt(chunk, amr_processed_text, acronym_list)
        rewritten, metrics = generate_chunk_with_feedback(engine, judge, prompt, intensity)
        humanized_chunks.append(rewritten)
        chunk_metrics.append(metrics)

    final_text = " ".join(humanized_chunks)
    final_metrics = judge.score_metrics(final_text)
    return final_text, amr_processed_text, final_metrics, chunk_metrics


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
        pass_intensity = max(0.3, min(1.0, float(intensity)))

        for global_pass in range(1, MAX_GLOBAL_PASSES + 1):
            print(f"Worker: Global pass {global_pass}/{MAX_GLOBAL_PASSES} (intensity={pass_intensity:.2f})...")
            final_text, amr_intermediate, final_metrics, _ = humanize_text(
                amr_handler, engine, judge, text, pass_intensity
            )
            print(
                f"Worker: Pass {global_pass} score — confidence={final_metrics['human_confidence']}, "
                f"ppl={final_metrics['mean_perplexity']}, burst={final_metrics['burstiness']}"
            )

            if final_metrics["human_confidence"] > best_metrics["human_confidence"]:
                best_final_text = final_text
                best_metrics = final_metrics

            if final_metrics["human_confidence"] >= FINAL_CONFIDENCE_THRESHOLD:
                break

            pass_intensity = min(1.0, pass_intensity + 0.15)

        print("Worker: Applying lexical post-processing...")
        final_evaded_text = AdversarialPostProcessor.apply_all(best_final_text)

        post_metrics = judge.score_metrics(final_evaded_text)
        confidence_score = post_metrics["human_confidence"]

        return {
            "status": "completed",
            "original": text,
            "amr_intermediate": amr_intermediate,
            "humanized": final_evaded_text,
            "confidence_score": round(confidence_score, 2),
            "diagnostics": {
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
