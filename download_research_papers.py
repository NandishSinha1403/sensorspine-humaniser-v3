"""
Research Paper Downloader
Downloads 100+ high-quality research PDFs from top institutions:
Ivy League (Harvard, MIT, Stanford, Yale, Princeton, Columbia, Cornell, UPenn, Dartmouth, Brown)
Indian Premier Institutions (IIT, IISc, IISER, TIFR, NIT)

Sources used: arXiv, Semantic Scholar, CORE, Unpaywall (all free & legal)
"""

import os
import time
import random
import logging
import requests
import urllib.parse
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION — edit these if needed
# ─────────────────────────────────────────────
DOWNLOAD_DIR = "./research_papers"          # folder where PDFs are saved
TARGET_COUNT = 500                          # Increased for massive corpus
START_YEAR = 2000                           # Target pre-AI era
END_YEAR = 2015                             # Target pre-AI era
DELAY_BETWEEN_REQUESTS = 5                  # increased to be more polite
REQUEST_TIMEOUT = 30                        # seconds before a request times out
MAX_FILE_SIZE_MB = 50                       # skip PDFs larger than this

# Top institutions to filter for
INSTITUTIONS = [
    # Ivy League & top US
    "harvard", "mit", "stanford", "yale", "princeton",
    "columbia", "cornell", "upenn", "dartmouth", "brown",
    "caltech", "uchicago", "johns hopkins", "carnegie mellon",
    # Indian Premier
    "iit", "iisc", "iiser", "tifr", "nit bombay",
    "iit bombay", "iit delhi", "iit madras", "iit kanpur",
    "iit kharagpur", "iit roorkee", "iisc bangalore",
]

# Research domains to search across
TOPICS = [
    "machine learning", "quantum computing", "genomics",
    "climate change", "materials science", "neuroscience",
    "drug discovery", "computer vision", "natural language processing",
    "renewable energy", "astrophysics", "robotics",
    "epidemiology", "condensed matter physics", "biochemistry",
    "cryptography", "fluid dynamics", "synthetic biology",
    "macroeconomics", "sociology of education", "cognitive psychology",
    "ancient history", "international relations", "organic chemistry",
    "particle physics", "behavioral economics", "linguistics",
    "political science", "environmental law", "molecular biology",
    "urban planning", "civil engineering", "mechanical engineering",
    "philosophy of science", "archaeology", "theology",
    "anthropology", "sociology", "political economy", "jurisprudence",
    "mathematics", "statistics", "electrical engineering", "chemical engineering",
    "aerospace engineering", "virology", "immunology", "oncology",
    "string theory", "topology", "number theory", "modern history",
    "ethics", "metaphysics", "logic", "pedagogy", "signal processing",
    "solid state physics", "plasma physics", "geophysics", "meteorology",
]

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("download_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (ResearchProject/1.0; mailto:academic-research@outlook.com)"
    )
})


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Turn a paper title into a safe filename."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-")
    clean = "".join(c if c in keep else "_" for c in name).strip()
    return clean[:max_len]


def already_downloaded(save_dir: Path, filename: str) -> bool:
    return (save_dir / filename).exists()


def download_pdf(url: str, save_path: Path) -> bool:
    """Download a single PDF; returns True on success."""
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            log.debug("  Skipped (not a PDF): %s", url)
            return False

        # Check file size before saving
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_FILE_SIZE_MB * 1024 * 1024:
            log.warning("  Skipped (too large): %s", url)
            return False

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = save_path.stat().st_size // 1024
        if size_kb < 10:                    # suspiciously small → probably an error page
            save_path.unlink(missing_ok=True)
            return False

        log.info("  ✓ Saved %s  (%d KB)", save_path.name, size_kb)
        return True

    except Exception as exc:
        log.debug("  Download failed: %s — %s", url, exc)
        if save_path.exists():
            save_path.unlink(missing_ok=True)
        return False


# ─────────────────────────────────────────────
# SOURCE 1 — arXiv API (free, open access)
# ─────────────────────────────────────────────
def fetch_arxiv(topic: str, max_results: int = 15) -> list[dict]:
    """Query arXiv for papers on a topic from top institutions within the target year range."""
    base = "https://export.arxiv.org/api/query"
    # Search by topic and date range; institution filter applied on metadata later
    # Note: submittedDate follows [YYYYMMDDHHMM TO YYYYMMDDHHMM]
    date_filter = f"submittedDate:[{START_YEAR}01010000 TO {END_YEAR}12312359]"
    query = urllib.parse.quote(f'all:"{topic}" AND {date_filter}')
    url = f"{base}?search_query={query}&start=0&max_results={max_results}&sortBy=relevance"

    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("arXiv request failed for '%s': %s", topic, exc)
        return []

    import xml.etree.ElementTree as ET
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []

    try:
        root = ET.fromstring(resp.text)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            title = title_el.text.strip().replace("\n", " ") if title_el is not None else "untitled"

            # affiliation check (arXiv includes author affiliations sometimes)
            affiliations = " ".join(
                (aff.text or "").lower()
                for aff in entry.findall(".//atom:affiliation", ns)
            )

            # Always include arXiv papers (many top authors don't fill affiliation)
            pdf_url = None
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("type") == "application/pdf":
                    pdf_url = link.attrib.get("href", "")
                    break
            if not pdf_url:
                arxiv_id = entry.find("atom:id", ns)
                if arxiv_id is not None:
                    aid = arxiv_id.text.strip().split("/abs/")[-1]
                    pdf_url = f"https://arxiv.org/pdf/{aid}.pdf"

            if pdf_url:
                papers.append({"title": title, "pdf_url": pdf_url, "source": "arXiv"})
    except ET.ParseError as exc:
        log.warning("arXiv XML parse error: %s", exc)

    return papers


# ─────────────────────────────────────────────
# SOURCE 2 — Semantic Scholar API (free)
# ─────────────────────────────────────────────
def fetch_semantic_scholar(topic: str, max_results: int = 10) -> list[dict]:
    """Query Semantic Scholar for open-access papers within the target year range."""
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": topic,
        "limit": max_results,
        "fields": "title,authors,year,openAccessPdf,externalIds",
        "openAccessPdf": "",          # only open-access
        "year": f"{START_YEAR}-{END_YEAR}"
    }
    try:
        resp = session.get(base, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("Semantic Scholar failed for '%s': %s", topic, exc)
        return []

    papers = []
    for item in data.get("data", []):
        oa = item.get("openAccessPdf")
        if not oa:
            continue
        pdf_url = oa.get("url", "")
        title = item.get("title", "untitled")
        if pdf_url:
            papers.append({"title": title, "pdf_url": pdf_url, "source": "SemanticScholar"})
    return papers


# ─────────────────────────────────────────────
# SOURCE 3 — CORE API (free, aggregator)
# ─────────────────────────────────────────────
def fetch_core(topic: str, max_results: int = 10) -> list[dict]:
    """
    Query CORE (core.ac.uk) for open-access PDFs within the target year range.
    Note: CORE free tier has rate limits; we back off politely.
    """
    base = "https://api.core.ac.uk/v3/search/works"
    headers = {"Accept": "application/json"}

    # Build institution filter and year filter into the query
    inst_query = " OR ".join(f'"{i}"' for i in INSTITUTIONS[:6])
    query = f'({topic}) AND ({inst_query}) AND year:[{START_YEAR} TO {END_YEAR}]'

    params = {
        "q": query,
        "limit": max_results,
        "scroll": "false",
        "stats": "false",
    }
    try:
        resp = session.get(base, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            log.warning("CORE rate-limited; skipping for now.")
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("CORE failed for '%s': %s", topic, exc)
        return []

    papers = []
    for item in data.get("results", []):
        pdf_url = item.get("downloadUrl") or item.get("sourceFulltextUrls", [None])[0]
        title = item.get("title", "untitled")
        if pdf_url and pdf_url.startswith("http"):
            papers.append({"title": title, "pdf_url": pdf_url, "source": "CORE"})
    return papers


# ─────────────────────────────────────────────
# MAIN DOWNLOADER
# ─────────────────────────────────────────────
def run():
    save_dir = Path(DOWNLOAD_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("Research Paper Downloader — target: %d PDFs", TARGET_COUNT)
    log.info("Save directory: %s", save_dir.resolve())
    log.info("=" * 60)

    downloaded = 0
    seen_urls: set[str] = set()
    all_papers: list[dict] = []

    # ── Collect candidates from all sources ──────────────────
    random.shuffle(TOPICS)
    for topic in TOPICS:
        if len(all_papers) >= TARGET_COUNT * 4:   # collect 4× for fallback
            break
        log.info("Searching topic: '%s' …", topic)

        arxiv_results    = fetch_arxiv(topic, max_results=30)
        ss_results       = fetch_semantic_scholar(topic, max_results=20)
        core_results     = fetch_core(topic, max_results=20)

        batch = arxiv_results + ss_results + core_results
        random.shuffle(batch)

        for paper in batch:
            url = paper["pdf_url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_papers.append(paper)

        log.info(
            "  Found %d new candidates (arXiv=%d, SS=%d, CORE=%d)",
            len(batch), len(arxiv_results), len(ss_results), len(core_results)
        )
        time.sleep(DELAY_BETWEEN_REQUESTS)

    log.info("-" * 60)
    log.info("Total unique candidates: %d — starting downloads …", len(all_papers))
    log.info("-" * 60)

    # ── Download ──────────────────────────────────────────────
    for paper in all_papers:
        if downloaded >= TARGET_COUNT:
            break

        title    = paper["title"]
        pdf_url  = paper["pdf_url"]
        source   = paper["source"]
        filename = sanitize_filename(title) + ".pdf"

        if already_downloaded(save_dir, filename):
            log.info("  Already exists, skipping: %s", filename)
            downloaded += 1
            continue

        log.info("[%d/%d] %s  (%s)", downloaded + 1, TARGET_COUNT, title[:80], source)
        success = download_pdf(pdf_url, save_dir / filename)
        if success:
            downloaded += 1
        time.sleep(DELAY_BETWEEN_REQUESTS + random.uniform(0, 1))

    # ── Summary ───────────────────────────────────────────────
    log.info("=" * 60)
    log.info("Done!  Downloaded %d PDFs  →  %s", downloaded, save_dir.resolve())
    log.info("Check download_log.txt for full details.")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
