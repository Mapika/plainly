#!/usr/bin/env python3
"""Render a horizontal bar chart of baseline 'AI-feel' (mean plainly density) per model.

Stdlib only — emits an SVG (text), no plotting dependency. Reads the experiment scores and
the model manifest; writes eval/assets/ai-feel-by-model.svg.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCORES = ROOT / "eval" / "experiment" / "scores.csv"
MODELS = ROOT / "eval" / "experiment" / "models.json"
OUT = ROOT / "eval" / "assets" / "ai-feel-by-model.svg"
HUMAN_REF = 0.26  # mean human-corpus density

TIER_COLOR = {"frontier": "#2563eb", "mid": "#0891b2", "small": "#64748b",
              "small/older": "#94a3b8"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    label = {m["id"]: m["label"] for m in json.load(open(MODELS))}
    tier = {m["id"]: m["tier"] for m in json.load(open(MODELS))}
    dens = defaultdict(list)
    for r in csv.DictReader(open(SCORES)):
        if r["condition"] == "baseline":
            dens[r["model"]].append(float(r["density"]))
    rows = [(label.get(m, m), sum(v) / len(v), tier.get(m, "mid"))
            for m, v in dens.items() if v]
    rows.sort(key=lambda x: x[1], reverse=True)

    W, rowh, top, left, right = 720, 34, 70, 170, 70
    H = top + rowh * len(rows) + 40
    maxd = max(d for _, d, _ in rows)
    plot_w = W - left - right
    x = lambda d: left + plot_w * (d / maxd)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13">']
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    s.append(f'<text x="{left}" y="28" font-size="17" font-weight="700" fill="#0f172a">'
             f'How "AI" does each model sound?</text>')
    s.append(f'<text x="{left}" y="48" fill="#64748b">Mean plainly density of default output '
             f'(higher = more AI tells) · 10 models, 10 prompts each</text>')
    # human reference line
    hx = x(HUMAN_REF)
    s.append(f'<line x1="{hx:.0f}" y1="{top-6}" x2="{hx:.0f}" y2="{H-30}" stroke="#16a34a" '
             f'stroke-width="1.5" stroke-dasharray="4 3"/>')
    s.append(f'<text x="{hx+4:.0f}" y="{H-18}" fill="#16a34a" font-size="11">human ≈ {HUMAN_REF}</text>')
    for i, (lab, d, t) in enumerate(rows):
        y = top + i * rowh
        bw = max(2, x(d) - left)
        c = TIER_COLOR.get(t, "#0891b2")
        s.append(f'<text x="{left-10}" y="{y+rowh/2+4:.0f}" text-anchor="end" fill="#0f172a">{esc(lab)}</text>')
        s.append(f'<rect x="{left}" y="{y+6:.0f}" width="{bw:.0f}" height="{rowh-14}" rx="3" fill="{c}"/>')
        s.append(f'<text x="{left+bw+6:.0f}" y="{y+rowh/2+4:.0f}" fill="#475569" font-size="12">{d:.2f}</text>')
    s.append('</svg>')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} models, max density {maxd:.2f})")


if __name__ == "__main__":
    main()
