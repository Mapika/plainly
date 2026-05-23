"""Deterministic stylometric metrics — stdlib only."""
import math
import os
import statistics
from collections import Counter

from .tokenize import split_sentences, word_count, WORD_RE

_DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def burstiness(text):
    """Sentence-length variation. Returns None if fewer than 2 sentences.

    cv               = coefficient of variation (sd/mean) — primary signal.
    var_over_mean    = index of dispersion (Fano factor).
    mean_consec_diff = average |len(i+1) - len(i)| — local short<->long rhythm.
    Low cv AND low mean_consec_diff together indicate AI-like uniformity.
    """
    lengths = [word_count(s) for s in split_sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return None
    mu = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    cv = sd / mu if mu else 0.0
    mcd = sum(abs(lengths[i + 1] - lengths[i]) for i in range(len(lengths) - 1)) / (
        len(lengths) - 1
    )
    return {
        "cv": round(cv, 4),
        "var_over_mean": round((sd * sd / mu) if mu else 0.0, 4),
        "mean_consec_diff": round(mcd, 4),
        "n": len(lengths),
    }


def load_stopwords(path=None):
    path = path or os.path.join(_DATA, "stopwords.txt")
    with open(path, encoding="utf-8") as fh:
        return {w.strip().lower() for w in fh.read().split() if w.strip()}


def _words(text):
    return [w.lower() for w in WORD_RE.findall(text)]


def lexical_metrics(text, stopwords):
    """type-token ratio, hapax rate, repetition rate, function-word ratio."""
    words = _words(text)
    total = len(words)
    if total == 0:
        return {"ttr": 0.0, "hapax_rate": 0.0, "repetition_rate": 0.0, "function_word_ratio": 0.0}
    counts = Counter(words)
    hapax = sum(1 for w, c in counts.items() if c == 1)
    bigrams = list(zip(words, words[1:]))
    uniq_bi = len(set(bigrams))
    rep = 1 - (uniq_bi / len(bigrams)) if bigrams else 0.0
    func = sum(1 for w in words if w in stopwords)
    return {
        "ttr": round(len(counts) / total, 4),
        "hapax_rate": round(hapax / total, 4),
        "repetition_rate": round(rep, 4),
        "function_word_ratio": round(func / total, 4),
    }


def opener_entropy(text):
    """Shannon entropy (bits) of the first word of each sentence. Low = templated openers."""
    openers = []
    for s in split_sentences(text):
        w = WORD_RE.findall(s)
        if w:
            openers.append(w[0].lower())
    if not openers:
        return 0.0
    counts = Counter(openers)
    n = len(openers)
    return round(-sum((c / n) * math.log2(c / n) for c in counts.values()), 4)


def punctuation_rates(text):
    words = max(word_count(text), 1)
    em = text.count("—") + text.count(" -- ")
    return {
        "em_dash_per_1k_words": round(em / words * 1000, 2),
        "em_dash_count": em,
        "semicolons": text.count(";"),
        "comma_count": text.count(","),
    }
