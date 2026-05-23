"""Brysbaert-lexicon abstraction scoring. Low mean concreteness => vague 'tell' prose."""
import csv
import os

from .tokenize import WORD_RE

_DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def load_lexicon(path=None):
    path = path or os.path.join(_DATA, "concreteness.csv")
    lex = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                lex[row["word"]] = float(row["conc"])
            except (KeyError, ValueError):
                continue
    return lex


def paragraph_concreteness(text, lexicon):
    """mean_conc over in-lexicon content words; coverage = fraction matched."""
    words = [w.lower() for w in WORD_RE.findall(text)]
    scored = [lexicon[w] for w in words if w in lexicon]
    if not words:
        return {"mean_conc": 0.0, "coverage": 0.0, "n_words": 0}
    mean = sum(scored) / len(scored) if scored else 0.0
    return {
        "mean_conc": round(mean, 3),
        "coverage": round(len(scored) / len(words), 3),
        "n_words": len(words),
    }
