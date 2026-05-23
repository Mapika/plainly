#!/usr/bin/env python3
"""Measure plainly's discrimination on a labeled mini-corpus.

Runs the real engine (scripts/prescan.py) over eval/samples/{ai,human}/*.md and reports,
per sample: density, burstiness CV, finding count, and the distinct tells fired. Then
summarizes separation between classes and the false-positive rate on the human set at a
given density gate (the same --fail-over gate used by CI).

This is an illustrative eval, not a validated benchmark: the AI samples are representative
hand-written slop and the human samples mix public-domain excerpts (Ecclesiastes/KJV,
Orwell) with realistic human prose. It demonstrates behavior and FPR, not population accuracy.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESCAN = ROOT / "plainly" / "scripts" / "prescan.py"
SAMPLES = Path(__file__).resolve().parent / "samples"
GATE = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0


def scan_file(path):
    out = subprocess.check_output([sys.executable, str(PRESCAN), str(path), "--json"], text=True)
    return json.loads(out)


def tells(result):
    ids = []
    for f in result["findings"]:
        ids.append(f.get("id") if f.get("id") != "lexical" else f"lex:{f.get('term')}")
    # distinct, order-stable
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i); out.append(i)
    return out


def run():
    rows = []
    for label in ("ai", "human"):
        for path in sorted((SAMPLES / label).glob("*.md")):
            r = scan_file(path)
            cv = r["metrics"]["burstiness"]["cv"] if r["metrics"]["burstiness"] else None
            rows.append({
                "label": label,
                "name": path.stem,
                "density": r["density"],
                "cv": cv,
                "n": len(r["findings"]),
                "tells": tells(r),
            })

    w = max(len(r["name"]) for r in rows)
    print(f"\n{'sample':<{w}}  label  density   cv     n  tells")
    print("-" * (w + 50))
    for r in rows:
        cv = f"{r['cv']:.3f}" if r["cv"] is not None else "  -  "
        print(f"{r['name']:<{w}}  {r['label']:<5}  {r['density']:>6.1f}  {cv}  {r['n']:>3}  "
              + ", ".join(r["tells"][:5]))

    ai = [r for r in rows if r["label"] == "ai"]
    hu = [r for r in rows if r["label"] == "human"]
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0

    print(f"\n--- summary (density gate = {GATE}) ---")
    print(f"AI    : n={len(ai):>2}  mean density {mean([r['density'] for r in ai]):6.1f}  "
          f"mean cv {mean([r['cv'] for r in ai if r['cv'] is not None]):.3f}")
    print(f"Human : n={len(hu):>2}  mean density {mean([r['density'] for r in hu]):6.1f}  "
          f"mean cv {mean([r['cv'] for r in hu if r['cv'] is not None]):.3f}")

    ai_flagged = sum(1 for r in ai if r["density"] > GATE)
    hu_flagged = sum(1 for r in hu if r["density"] > GATE)
    print(f"\nAI flagged (recall)        : {ai_flagged}/{len(ai)} = {ai_flagged/len(ai)*100:.0f}%")
    print(f"Human flagged (FALSE POS)  : {hu_flagged}/{len(hu)} = {hu_flagged/len(hu)*100:.0f}%")
    sep = mean([r['density'] for r in ai]) - mean([r['density'] for r in hu])
    print(f"Density separation (AI-Human): {sep:.1f}")


if __name__ == "__main__":
    run()
