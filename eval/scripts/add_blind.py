#!/usr/bin/env python3
"""Add the blind-writer corpus (Opus/Sonnet/Haiku, 2026) to the eval.

Runs the engine over /tmp/wsamples/<model>/*.md, copies texts into the corpus, and
appends rows to eval/data/metrics.csv. These are modern AI samples written by blind
subagents (no knowledge of the tool), tagged by model in `source` so we can compare tiers.
"""
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/mapika/projects/writer")
PRESCAN = ROOT / "plainly" / "scripts" / "prescan.py"
CSV = ROOT / "eval" / "data" / "metrics.csv"
CORPUS_AI = ROOT / "eval" / "data" / "corpus" / "ai"
SRC = Path("/tmp/wsamples")
MODELS = ["opus", "sonnet", "haiku"]
DOMAIN = {"01-reading": "general", "02-headphones": "general", "03-composting": "general",
          "04-mrna": "scientific", "05-silkroad": "general"}

WORD = re.compile(r"\b[\w'-]+\b")


def metrics_for(text_path):
    out = subprocess.check_output([sys.executable, str(PRESCAN), str(text_path), "--json"], text=True)
    d = json.loads(out)
    b = d["metrics"]["burstiness"]
    return {
        "density": d["density"],
        "cv": b["cv"] if b else "",
        "opener_entropy": d["metrics"]["opener_entropy"],
        "func_word_ratio": d["metrics"]["lexical"]["function_word_ratio"],
        "n_findings": len(d["findings"]),
        "low_conc_paras": len(d["metrics"]["concreteness"]["low_paragraphs"]),
    }


def main():
    rows = []
    for model in MODELS:
        for md in sorted((SRC / model).glob("*.md")):
            stem = md.stem
            text = md.read_text(encoding="utf-8")
            n_words = len(WORD.findall(text))
            # copy into corpus as plain text
            dest = CORPUS_AI / f"blind_{model}_{stem}.txt"
            shutil.copyfile(md, dest)
            m = metrics_for(md)
            rows.append({
                "id": f"a_blind_{model}_{stem}",
                "label": "ai",
                "domain": DOMAIN.get(stem, "general"),
                "source": f"blind-{model}-2026",
                "n_words": n_words,
                **m,
            })

    with open(CSV, newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    with open(CSV, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        for r in rows:
            w.writerow(r)
    print(f"appended {len(rows)} blind-writer rows to {CSV}")
    for r in rows:
        print(f"  {r['id']:<28} {r['domain']:<10} density={r['density']:<6} cv={r['cv']} findings={r['n_findings']}")


if __name__ == "__main__":
    main()
