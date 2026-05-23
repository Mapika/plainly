#!/usr/bin/env python3
"""Run the prescan engine over every corpus text and emit eval/data/metrics.csv.

Stdlib only. Reads the row manifest produced by build_corpus.py
(/tmp/corpus_rows.json), runs prescan.py --json per file, parses metrics.
"""
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESCAN = os.path.join(ROOT, "plainly/scripts/prescan.py")
OUT = os.path.join(ROOT, "eval/data/metrics.csv")
ROWS = "/tmp/corpus_rows.json"

COLS = ["id", "label", "domain", "source", "n_words", "density", "cv",
        "opener_entropy", "func_word_ratio", "n_findings", "low_conc_paras"]


def scan(path):
    try:
        out = subprocess.run([sys.executable, PRESCAN, path, "--json"],
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        print(f"WARNING: skipping {path}: {e}", file=sys.stderr)
        return None
    d = json.loads(out)
    m = d.get("metrics") or {}
    burst = m.get("burstiness") or {}
    lex = m.get("lexical") or {}
    conc = m.get("concreteness") or {}
    return dict(
        density=d.get("density"),
        cv=burst.get("cv"),
        opener_entropy=m.get("opener_entropy"),
        func_word_ratio=lex.get("function_word_ratio"),
        n_findings=len(d.get("findings") or []),
        low_conc_paras=len(conc.get("low_paragraphs") or []),
    )


def main():
    with open(ROWS) as f:
        rows = json.load(f)
    out_rows = []
    for r in rows:
        met = scan(r["path"])
        if met is None:
            continue
        out_rows.append({
            "id": r["id"], "label": r["label"], "domain": r["domain"],
            "source": r["source"], "n_words": r["n_words"], **met,
        })
    out_rows.sort(key=lambda x: (x["label"], x["domain"], x["id"]))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    print("wrote %d rows -> %s" % (len(out_rows), OUT), file=sys.stderr)

    # summary
    for lbl in ("human", "ai"):
        ds = [r["density"] for r in out_rows if r["label"] == lbl]
        print("%s: n=%d mean_density=%.3f" % (lbl, len(ds), sum(ds) / len(ds)),
              file=sys.stderr)


if __name__ == "__main__":
    main()
