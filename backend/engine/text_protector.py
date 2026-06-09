import re
from dataclasses import dataclass


@dataclass
class ProtectedText:
    text: str
    spans: dict[str, str]


# (pattern, flags). Ordered most-specific → least-specific. Works for any domain.
_I = re.IGNORECASE
_PROTECTED_PATTERNS: list[tuple[str, int]] = [
    # TeX delimiters
    (r"\$\$[^$]+\$\$", _I),
    (r"\$[^$\n]+\$", _I),
    # LaTeX environments
    (r"\\begin\{[a-zA-Z*]+\}[\s\S]*?\\end\{[a-zA-Z*]+\}", _I),
    # LaTeX commands with braced arguments
    (r"\\(?:frac|sqrt|sum|int|prod|lim|log|ln|sin|cos|tan|exp|det|dim|max|min|sup|inf)"
     r"\s*(?:\{[^{}]*\}){1,2}", _I),
    (r"\\[a-zA-Z]+\s*(?:\{[^{}]*\})+", _I),
    (r"\\[a-zA-Z]+", _I),
    # Named laws / theorems (case-sensitive type word — avoids matching "of identity")
    (r"\b[A-Z][A-Za-z'’-]*(?:'s|'s)?\s+"
     r"(?:Law|Theorem|Principle|Equation|Rule|Hypothesis|Postulate)\b", 0),
    (r"\bthe\s+[A-Z][A-Za-z'’-]+\s+(?:law|theorem|principle|equation|rule)\b", _I),
    (r"\b[A-Z][A-Za-z'’-]*'s\s+(?:law|theorem|principle|equation|rule)\b", _I),
    # Scientific notation, units, equations, citations
    (r"\b\d+(?:\.\d+)?\s*[×x]\s*10\s*\^\s*[+-]?\d+\b", _I),
    (r"\b\d+(?:\.\d+)?\s*(?:±|\+/-)\s*\d+(?:\.\d+)?", _I),
    (r"\b\d+(?:\.\d+)?\s*(?:%|°C|°F|K|Hz|kHz|MHz|GHz|Pa|kPa|MPa|GPa|nm|μm|mm|cm|m|kg|mg|g|ml|mL|L|mol|s|ms|μs|ns|eV|keV|MeV|bp|kb|Mb|GB)\b", _I),
    (r"\b[A-Za-z][\w]*\s*[=≈≤≥]\s*(?:\\[a-zA-Z]+[^\s,;.]+|\d[\d.\s+\-*/^]*\S*)", _I),
    (r"\b(?:Fig(?:ure)?|Table|Eq(?:uation)?|Tab\.)\s*\d+(?:\.\d+)?[a-z]?\b", _I),
    (r"\[(?:[^\[\]]{1,120})\]", _I),
    (r"\([A-Z][A-Za-z]+(?:\s+(?:et\s+al\.|&|and)\s+[A-Z][A-Za-z]+)?,?\s*\d{4}[a-z]?\)", _I),
    (r"\bhttps?://\S+", _I),
    (r"\bdoi:\s*\S+", _I),
    (r"[α-ωΑ-Ω∑∫∂∇∞±×÷∝°‰]+", 0),
]


def has_technical_content(text: str) -> bool:
    """True when AMR round-trip is likely to corrupt notation, formulas, or citations."""
    markers = [
        r"\\[a-zA-Z]+",
        r"\$[^$]+\$",
        r"[=≈≤≥≠∝]\s*\S",
        r"[α-ωΑ-Ω∑∫∂∇∞±×÷°]",
        r"\b\d+(?:\.\d+)?\s*(?:%|±|×|x10|\^)",
        r"'s\s+(?:Law|Theorem|Principle|Equation|Rule)\b",
        r"\b(?:Fig(?:ure)?|Table|Eq(?:uation)?)\.\s*\d+",
        r"\bdoi:",
        r"https?://",
        r"\[\d+(?:[,\s-]+\d+)*\]",  # [1], [2-5], [1, 3]
    ]
    return any(re.search(m, text, re.IGNORECASE) for m in markers)


def protect_spans(text: str) -> ProtectedText:
    """Replace fragile spans with placeholders before rewriting."""
    spans: dict[str, str] = {}
    counter = [0]

    def _mask(match: re.Match) -> str:
        key = f"⟦PROT{counter[0]}⟧"
        counter[0] += 1
        spans[key] = match.group(0)
        return key

    protected = text
    for pattern, flags in _PROTECTED_PATTERNS:
        protected = re.sub(pattern, _mask, protected, flags=flags)

    return ProtectedText(text=protected, spans=spans)


def restore_spans(text: str, spans: dict[str, str]) -> str:
    restored = text
    for key, value in spans.items():
        restored = restored.replace(key, value)
    return restored


def extract_locked_terms(text: str) -> list[str]:
    """
    Domain-agnostic terms to preserve during rewriting.
    Derived from the input text — not a hardcoded vocabulary.
    """
    terms: set[str] = set()

    # Named laws, theorems, principles (any field)
    for m in re.finditer(
        r"\b[A-Z][A-Za-z'’-]*(?:'s|'s)?\s+"
        r"(?:Law|Theorem|Principle|Equation|Rule|Hypothesis|Postulate)\b",
        text,
    ):
        terms.add(m.group(0))
    for m in re.finditer(
        r"\bthe\s+[A-Z][A-Za-z'’-]+\s+(?:law|theorem|principle|equation|rule)\b",
        text,
        re.IGNORECASE,
    ):
        terms.add(m.group(0))
    for m in re.finditer(
        r"\b[A-Z][A-Za-z'’-]*'s\s+(?:law|theorem|principle|equation|rule)\b",
        text,
        re.IGNORECASE,
    ):
        terms.add(m.group(0))

    # Acronyms and initialisms (DNA, MRI, HTTP, pH-style excluded if single cap)
    for m in re.finditer(r"\b[A-Za-z0-9]*[A-Z][A-Za-z0-9\-]*[A-Z][A-Za-z0-9\-]*\b", text):
        token = m.group(0)
        if len(re.findall(r"[A-Z]", token)) >= 2:
            terms.add(token)

    # Hyphenated technical compounds (e.g. fiber-optic, machine-learning, intra-articular)
    for m in re.finditer(r"\b[A-Za-z]{3,}(?:-[A-Za-z0-9]{2,})+\b", text):
        terms.add(m.group(0))

    # Alphanumeric identifiers (model names, genes, chemical labels: H2O, CRISPR-Cas9, GPT-4)
    for m in re.finditer(r"\b(?:[A-Za-z]+\d+[A-Za-z0-9\-]*|\d+[A-Za-z]+[A-Za-z0-9\-]*)\b", text):
        terms.add(m.group(0))

    # Quoted technical terms
    for m in re.finditer(r'"([^"]{2,80})"', text):
        terms.add(m.group(1))

    # Terms defined in parentheses: "long form (ABBR)"
    for m in re.finditer(r"\(([A-Z][A-Za-z0-9\-]{1,15})\)", text):
        terms.add(m.group(1))

    # Capitalized multi-word proper nouns (each word must start uppercase)
    for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", text):
        terms.add(m.group(0))

    return sorted(terms, key=len, reverse=True)[:50]
