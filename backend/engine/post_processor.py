import re
import random

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
        """Run the adversarial post-processing pipeline (Structural & Token disruption only)."""
        # DISABLED: These ruin perplexity by making the text artificially simple, triggering Turnitin.
        # text = cls.pass_phrase_replacement(text)
        # text = cls.pass_de_jargonization(text)
        
        # Keep structural and token-level disruption
        text = cls.pass_zwj_jitter(text)
        text = cls.pass_adversarial_punctuation(text)
        text = cls.pass_invisible_padding(text)
        return text
