"""Pure-stdlib tokenization. Heuristic, good enough for metrics — no NLP deps."""
import re

# Split after . ! ? (optionally followed by quotes/brackets) when followed by whitespace.
_SENT_RE = re.compile(r'(?<=[.!?])["\')\]]*\s+')
WORD_RE = re.compile(r"\b[\w'-]+\b")


def split_sentences(text):
    """Return a list of non-empty, stripped sentences."""
    parts = _SENT_RE.split(text.strip())
    return [s.strip() for s in parts if s.strip()]


def word_count(text):
    """Count word-like tokens."""
    return len(WORD_RE.findall(text))


def split_paragraphs(text):
    """Split on blank lines; return stripped non-empty paragraphs."""
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def sentence_spans(text):
    """Return [{text, line}] where line is the 1-based line the sentence starts on."""
    spans = []
    offset = 0
    for sent in split_sentences(text):
        head = sent[:20]
        idx = text.find(head, offset)
        line = text.count("\n", 0, idx) + 1 if idx >= 0 else 1
        spans.append({"text": sent, "line": line})
        if idx >= 0:
            offset = idx + 1
    return spans
