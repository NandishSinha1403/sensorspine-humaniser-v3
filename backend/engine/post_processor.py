import re
import random


class AdversarialPostProcessor:
    """
    Deterministic lexical passes that reduce paraphraser fingerprints
    without Unicode manipulation (which modern detectors flag).
    """

    PHRASE_REPLACEMENTS = {
        "paradigm shift": ["shift in approach", "change in framework"],
        "it is worth noting that": ["", "notably,"],
        "it is important to note that": ["", "notably,"],
        "in conclusion": ["overall", "taken together"],
        "furthermore": ["also", "and"],
        "moreover": ["also", "besides"],
        "additionally": ["also", "and"],
        "demonstrates": ["shows", "indicates"],
        "demonstrate": ["show", "indicate"],
        "utilizing": ["using"],
        "utilize": ["use"],
        "facilitates": ["supports", "allows"],
        "facilitate": ["support", "allow"],
        "significant": ["clear", "marked"],
        "substantial": ["considerable", "large"],
        "comprehensive": ["broad", "wide-ranging"],
        "robust": ["solid", "stable"],
        "leverage": ["use", "apply"],
        "in order to": ["to"],
        "due to the fact that": ["because"],
        "plays a crucial role": ["matters", "is central"],
        "sheds light on": ["clarifies", "explains"],
    }

    AI_TRANSITIONS = [
        r"\bfirstly\b", r"\bsecondly\b", r"\bthirdly\b",
        r"\bin summary\b", r"\bto summarize\b",
        r"\bas a result\b", r"\bconsequently\b",
    ]

    @staticmethod
    def pass_phrase_replacement(text: str) -> str:
        new_text = text
        for phrase, replacements in AdversarialPostProcessor.PHRASE_REPLACEMENTS.items():
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)

            def replace_fn(match):
                original = match.group(0)
                replacement = random.choice(replacements)
                if not replacement:
                    return ""
                if original[0].isupper():
                    return replacement[0].upper() + replacement[1:]
                return replacement

            new_text = pattern.sub(replace_fn, new_text)
        return re.sub(r"\s{2,}", " ", new_text).strip()

    @staticmethod
    def pass_transition_diversification(text: str) -> str:
        """Remove stacked AI transition openers from sentence starts."""
        new_text = text
        for pattern in AdversarialPostProcessor.AI_TRANSITIONS:
            new_text = re.sub(pattern, "", new_text, flags=re.IGNORECASE)
        return re.sub(r"\s{2,}", " ", new_text).strip()

    @staticmethod
    def pass_punctuation_humanize(text: str) -> str:
        """Occasionally break long comma chains — humans use shorter clauses."""
        if random.random() < 0.35:
            pattern = re.compile(r"([^,;]{25,}),\s+([^,;]{25,}),\s+and\s+([^,;.]{10,})")
            text = pattern.sub(r"\1. \2, and \3", text)
        return text

    @classmethod
    def apply_all(cls, text: str) -> str:
        text = cls.pass_phrase_replacement(text)
        text = cls.pass_transition_diversification(text)
        text = cls.pass_punctuation_humanize(text)
        return text.strip()
