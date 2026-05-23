"""Orchestrate Layer 0: run all detectors, apply config, emit a JSON-ready dict."""
import re
from . import metrics as M
from . import patterns as P
from . import concreteness as C
from .tokenize import split_paragraphs

SCHEMA_VERSION = "1"

# How heavily register-specific (marketing) tells count, by document genre. A
# "thrilled to announce" or hype emoji is a full smell in marketing copy, a lighter
# one in an essay, and barely worth flagging in technical docs. General tells (no
# register) are never scaled.
GENRE_MULT = {"marketing": 1.0, "prose": 0.5, "docs": 0.25}


def _apply_genre(findings, genre):
    mult = GENRE_MULT.get(genre, 0.5)
    if mult == 1.0:
        return findings
    for f in findings:
        if f.get("register") == "marketing":
            f["weight"] = round(f["weight"] * mult, 2)
    return findings


def _apply_allow(findings, allow_terms):
    if not allow_terms:
        return findings
    pats = [re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE) for t in allow_terms]
    kept = []
    for f in findings:
        hay = (f.get("term") or "") + " " + (f.get("span") or "")
        if any(p.search(hay) for p in pats):
            continue
        kept.append(f)
    return kept


def scan(text, cfg, stopwords=None, patterns=None, lexical=None, lexicon=None):
    stopwords = stopwords if stopwords is not None else M.load_stopwords()
    patterns = patterns if patterns is not None else P.load_patterns()
    lexical = lexical if lexical is not None else P.load_lexical()
    lexicon = lexicon if lexicon is not None else C.load_lexicon()

    findings = P.match_patterns(text, patterns) + P.match_lexical(text, lexical)

    # Rule toggles (em-dash off by default etc.).
    if not cfg["rules"].get("em_dash", False):
        findings = [f for f in findings if f.get("id") != "em-dash"]

    findings = _apply_allow(findings, cfg["allow"]["terms"])
    findings = _apply_genre(findings, cfg["genre"]["default"])

    burst = M.burstiness(text)
    para_conc = []
    for para in split_paragraphs(text):
        pc = C.paragraph_concreteness(para, lexicon)
        if pc["coverage"] > 0 and pc["mean_conc"] < cfg["concreteness"]["min_mean"]:
            para_conc.append({"paragraph": para[:80], "mean_conc": pc["mean_conc"]})

    metrics = {
        "word_count": M.word_count(text),
        "burstiness": burst,
        "lexical": M.lexical_metrics(text, stopwords),
        "opener_entropy": M.opener_entropy(text),
        "punctuation": M.punctuation_rates(text),
        "concreteness": {"low_paragraphs": para_conc},
    }

    # Density: total finding weight per 100 words, nudged by low burstiness.
    words = max(M.word_count(text), 1)
    weight = sum(f.get("weight", 0) for f in findings)
    density = weight / words * 100
    if burst and burst["cv"] < cfg["burstiness"]["min_cv"]:
        density += 1.0
    density += len(para_conc) * 0.5

    return {
        "schema_version": SCHEMA_VERSION,
        "findings": findings,
        "metrics": metrics,
        "density": round(density, 3),
    }
