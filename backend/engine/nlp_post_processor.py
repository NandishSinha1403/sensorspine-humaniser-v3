"""
Fast rule-based NLP pipeline (ported from sensorspine-humaniser-1).
Runs on CPU after LLM generation — no extra GPU time.
"""

import re
import random
from typing import Optional

from engine.ai_phrases import AI_PHRASE_REPLACEMENTS, AI_SIGNATURE_PHRASES, COMPILED_AI_PHRASES

try:
    from nltk.tokenize import sent_tokenize
    import nltk
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    _HAS_NLTK = True
except Exception:
    _HAS_NLTK = False


def _sentences(text: str) -> list[str]:
    if _HAS_NLTK:
        return [s.strip() for s in sent_tokenize(text) if s.strip()]
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text.strip())
    return [p.strip() for p in parts if p.strip()] or [text]


def _join_sentences(sents: list[str]) -> str:
    return " ".join(s.strip() for s in sents if s.strip())


def _capitalize_replacement(original: str, replacement: str) -> str:
    if not replacement:
        return replacement
    if original and original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


class NLPPostProcessor:
    """
    Multi-pass NLP humanizer applied after the LLM stage.
    Order mirrors humaniser-1 apply_full_passes (fast subset, no Unicode tricks).
    """

    SHORT_ANCHORS = [
        "This bears emphasis.",
        "The point is clear.",
        "This warrants attention.",
        "The trend is evident.",
        "These findings align.",
    ]

    NUANCE_PREFIXES = [
        "one might argue,",
        "arguably,",
        "to some extent,",
        "in many respects,",
        "it appears that",
        "broadly speaking,",
    ]

    MERGE_CONNECTORS = [
        ", which further suggests that ",
        "; in a related vein, ",
        ", and when considered alongside this, ",
    ]

    @classmethod
    def pass_signature_phrase_breaker(cls, text: str, rng: random.Random) -> str:
        """Force-replace every AI signature phrase (humaniser-1)."""
        new_text = text
        for phrase in sorted(AI_SIGNATURE_PHRASES, key=len, reverse=True):
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            replacements = AI_PHRASE_REPLACEMENTS.get(
                phrase.lower(), ["also", "and", "notably", "in fact"]
            )

            def _repl(match, _replacements=replacements):
                return _capitalize_replacement(match.group(0), rng.choice(_replacements))

            new_text = pattern.sub(_repl, new_text)
        return new_text

    @classmethod
    def pass_phrase_replacement(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Probabilistic AI cliché swap (humaniser-1)."""
        new_text = text
        used: set[str] = set()
        force_all = intensity >= 0.75

        for pattern, replacements in COMPILED_AI_PHRASES:
            if not force_all and rng.random() > intensity:
                continue

            def _repl(match, _replacements=replacements):
                original = match.group(0)
                pool = [r for r in _replacements if r.lower() not in used] or _replacements
                choice = rng.choice(pool)
                used.add(choice.lower())
                return _capitalize_replacement(original, choice)

            new_text = pattern.sub(_repl, new_text)
        return new_text

    @classmethod
    def pass_burstiness(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Sentence-length variance without spaCy (humaniser-1 rhythm.py logic)."""
        paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()] or [text]
        out_paragraphs = []

        for para in paragraphs:
            sents = _sentences(para)
            if len(sents) < 2:
                out_paragraphs.append(para)
                continue

            word_count = len(para.split())
            lengths = [len(s.split()) for s in sents]
            has_short = any(l < 8 for l in lengths)
            has_long = any(l > 32 for l in lengths)

            if word_count > 50 and intensity >= 0.4:
                if not has_short and len(sents) > 1:
                    idx = min(2, len(sents))
                    sents.insert(idx, rng.choice(cls.SHORT_ANCHORS))
                    has_short = True

                if not has_long and len(sents) >= 2:
                    for i in range(len(sents) - 1):
                        w1, w2 = len(sents[i].split()), len(sents[i + 1].split())
                        if w1 + w2 > 18:
                            merged = (
                                sents[i].rstrip(".!?")
                                + rng.choice(cls.MERGE_CONNECTORS)
                                + sents[i + 1][0].lower()
                                + sents[i + 1][1:]
                            )
                            sents[i] = merged
                            sents.pop(i + 1)
                            break

            out_paragraphs.append(_join_sentences(sents))

        return "\n\n".join(out_paragraphs)

    @classmethod
    def pass_restructuring(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Split long sentences at conjunctions; merge very short neighbors."""
        sents = _sentences(text)
        if len(sents) < 2:
            return text

        new_sents: list[str] = []
        i = 0
        while i < len(sents):
            sent = sents[i]
            wc = len(sent.split())

            if wc > 28 and rng.random() < intensity:
                parts = re.split(
                    r",\s+(?=and|but|while|whereas|which|who)\s+",
                    sent,
                    maxsplit=1,
                )
                if len(parts) == 2:
                    new_sents.append(parts[0].rstrip(",; ") + ".")
                    rest = parts[1].strip()
                    if rest:
                        new_sents.append(rest[0].upper() + rest[1:])
                    i += 1
                    continue

            if wc < 6 and i + 1 < len(sents) and rng.random() < intensity * 0.5:
                merged = sent.rstrip(".!?") + ", " + sents[i + 1][0].lower() + sents[i + 1][1:]
                new_sents.append(merged)
                i += 2
                continue

            new_sents.append(sent)
            i += 1

        return _join_sentences(new_sents)

    @classmethod
    def pass_nuance_injection(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Hedging prefixes on every ~4th sentence (humaniser-1 style.py)."""
        sents = _sentences(text)
        out = []
        for i, sent in enumerate(sents):
            if i % 4 == 0 and i > 0 and len(sent.split()) > 10 and rng.random() < 0.35 * intensity:
                prefix = rng.choice(cls.NUANCE_PREFIXES).capitalize()
                sent = prefix + " " + sent[0].lower() + sent[1:]
            out.append(sent)
        return _join_sentences(out)

    @classmethod
    def pass_morphological_shift(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Verb → noun phrase shifts (regex, humaniser-1 structural.py)."""
        verb_to_noun = {
            r"\butilize\b": "make use of",
            r"\butilizes\b": "makes use of",
            r"\butilized\b": "made use of",
            r"\bdemonstrate\b": "show",
            r"\bdemonstrates\b": "shows",
            r"\bdemonstrated\b": "showed",
            r"\bfacilitate\b": "support",
            r"\bfacilitates\b": "supports",
            r"\bfacilitated\b": "supported",
            r"\bimplement\b": "carry out",
            r"\bimplements\b": "carries out",
            r"\bimplemented\b": "carried out",
        }
        new_text = text
        for pattern, replacement in verb_to_noun.items():
            if rng.random() < intensity:
                new_text = re.sub(pattern, replacement, new_text, flags=re.IGNORECASE)
        return new_text

    @classmethod
    def pass_adversarial_punctuation(cls, text: str, intensity: float, rng: random.Random) -> str:
        """Punctuation variance — no invisible Unicode (humaniser-1 adversarial.py)."""
        if rng.random() < 0.4 * intensity:
            text = re.sub(
                r"([^,;]+),\s*([^,;]+),\s*and\s+([^,;.]+)",
                r"\1; \2; and \3",
                text,
            )
        text = re.sub(
            r",\s*(which|who|that|namely)\s+([^,.]+),",
            r" — \1 \2 — ",
            text,
        )
        return text

    @classmethod
    def pass_final_cleanup(cls, text: str) -> str:
        """Artifact repair (humaniser-1 cleanup.py, regex-only)."""
        text = re.sub(r"\b(a|an|the)\s+(a|an|the)\s+", r"\1 ", text, flags=re.IGNORECASE)
        text = re.sub(r"[\s,;]+([.!?])", r"\1", text)
        text = re.sub(r"\.\.+", ".", text)
        text = re.sub(r",,+", ",", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        return text.strip()

    @classmethod
    def apply_all(cls, text: str, intensity: float = 0.7, seed: Optional[int] = None) -> str:
        """Full post-LLM NLP pipeline."""
        if not text.strip():
            return text

        rng = random.Random(seed)
        i = max(0.3, min(1.0, float(intensity)))

        text = cls.pass_signature_phrase_breaker(text, rng)
        text = cls.pass_phrase_replacement(text, i, rng)
        text = cls.pass_morphological_shift(text, i * 0.8, rng)
        text = cls.pass_restructuring(text, i * 0.7, rng)
        text = cls.pass_burstiness(text, i, rng)
        text = cls.pass_nuance_injection(text, i * 0.6, rng)
        text = cls.pass_adversarial_punctuation(text, i * 0.5, rng)
        text = cls.pass_final_cleanup(text)
        return text
