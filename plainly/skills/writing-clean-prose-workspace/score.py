#!/usr/bin/env python3
"""Grade writing-clean-prose eval outputs with plainly's own engine.

For each eval-*/ in an iteration dir, scan with_skill and without_skill outputs,
report density / word_count / findings, and the with-vs-baseline delta. Also emit
grading.json per run (viewer schema: expectations[].{text,passed,evidence}).
"""
import json
import sys
from pathlib import Path

# score.py lives at .../plainly/skills/writing-clean-prose-workspace/score.py
PLUGIN_ROOT = Path(__file__).resolve().parents[2]  # .../plainly
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))   # where the `plainly` package lives

from plainly.scan import scan          # noqa: E402
from plainly.config import load_config  # noqa: E402

CFG = load_config(None)
NEAR_HUMAN = 1.0   # density at/under this reads close to the human range (eval: human ~0.26)
PAD_LIMIT = 1.25   # with_skill words must not exceed baseline * this (no padding to dodge)


def score_text(text):
    r = scan(text, CFG)
    return {
        "density": r["density"],
        "word_count": r["metrics"]["word_count"],
        "findings": len(r["findings"]),
        "tells": sorted({f.get("id") for f in r["findings"]}),
    }


def run(iteration_dir):
    iteration = Path(iteration_dir)
    rows = []
    for eval_dir in sorted(iteration.glob("eval-*")):
        name = eval_dir.name
        scores = {}
        for cond in ("with_skill", "without_skill"):
            out = eval_dir / cond / "outputs" / "output.md"
            if out.exists():
                scores[cond] = score_text(out.read_text(encoding="utf-8"))
        rows.append((name, scores))

        # Per-run grading.json for the with_skill run (comparative + absolute checks).
        ws, ns = scores.get("with_skill"), scores.get("without_skill")
        if ws and ns:
            exps = [
                {
                    "text": "density lower than no-skill baseline (same prompt)",
                    "passed": ws["density"] < ns["density"],
                    "evidence": f"with_skill {ws['density']} vs baseline {ns['density']}",
                },
                {
                    "text": f"density in human range (<= {NEAR_HUMAN})",
                    "passed": ws["density"] <= NEAR_HUMAN,
                    "evidence": f"with_skill density {ws['density']}",
                },
                {
                    "text": f"no padding (words <= baseline x {PAD_LIMIT})",
                    "passed": ws["word_count"] <= ns["word_count"] * PAD_LIMIT,
                    "evidence": f"with_skill {ws['word_count']}w vs baseline {ns['word_count']}w",
                },
            ]
            grad_dir = eval_dir / "with_skill"
            (grad_dir / "grading.json").write_text(
                json.dumps({"expectations": exps}, indent=2)
            )

    # Console comparison table.
    print(f"{'eval':24s} {'cond':14s} {'density':>8s} {'words':>6s} {'finds':>6s}  tells")
    for name, scores in rows:
        for cond in ("with_skill", "without_skill"):
            s = scores.get(cond)
            if s:
                print(f"{name:24s} {cond:14s} {s['density']:8.2f} {s['word_count']:6d} "
                      f"{s['findings']:6d}  {','.join(s['tells']) or '-'}")
        ws, ns = scores.get("with_skill"), scores.get("without_skill")
        if ws and ns:
            delta = round(ws["density"] - ns["density"], 2)
            print(f"{'':24s} {'-> delta':14s} {delta:8.2f}  (with_skill minus baseline)")
        print()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else ".")
