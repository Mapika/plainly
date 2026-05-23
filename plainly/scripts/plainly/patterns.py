"""Load and apply the structural and lexical manifests."""
import json
import os
import re

_DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def load_patterns(path=None):
    path = path or os.path.join(_DATA, "patterns.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["patterns"]


def load_lexical(path=None):
    path = path or os.path.join(_DATA, "lexical-tells.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["tells"]


def match_patterns(text, patterns):
    out = []
    for p in patterns:
        flags = 0
        if p.get("ignorecase"):
            flags |= re.IGNORECASE
        if p.get("multiline"):
            flags |= re.MULTILINE
        for m in re.finditer(p["regex"], text, flags):
            out.append({
                "id": p["id"],
                "name": p["name"],
                "kind": p["kind"],
                "span": m.group(0).strip(),
                "line": _line_of(text, m.start()),
                "weight": p["weight"],
                "tier": p["tier"],
                "register": p.get("register"),
                "why": p["why"],
            })
    return out


def match_lexical(text, tells):
    out = []
    for t in tells:
        if t.get("stem"):
            stem = t["term"].rstrip("e") if t["term"].endswith("e") else t["term"]
            pat = r"\b" + stem + r"\w*\b"
        else:
            pat = r"\b" + t["term"] + r"\b"
        for m in re.finditer(pat, text, re.IGNORECASE):
            out.append({
                "id": "lexical",
                "term": re.sub(r"[\\?']", "", t["term"]),
                "kind": "lexical",
                "span": m.group(0),
                "line": _line_of(text, m.start()),
                "weight": t["weight"],
                "tier": t["tier"],
                "register": t.get("register"),
                "suggest": t.get("suggest", ""),
            })
    return out
