#!/usr/bin/env python3
"""Render the README's "marketing blind spot" chart as a stdlib SVG (no deps).

Story: before v0.5 the density score read the same LinkedIn announcement and the
skill-written version as identical (both ~0). After teaching plainly the marketing
register (v0.5), it separates the slop from the clean version. A blind judge,
outside the test, had already preferred the clean version 3 times out of 3.

Numbers are the measured densities recorded in
plainly/skills/writing-clean-prose-workspace/iteration-1/RESULTS.md
(marketing-genre scoring for the Series-A post pair).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "assets" / "blindspot-marketing.svg"

# (group label, slop density, clean density)
GROUPS = [
    ("Before v0.5", 0.00, 0.00),
    ("After v0.5 (marketing-aware)", 7.63, 0.00),
]
SLOP = "#dc2626"   # red
CLEAN = "#16a34a"  # green


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    W, H = 720, 360
    left, right, top = 60, 40, 96
    plot_w = W - left - right
    maxd = 8.0
    base_y = H - 60
    plot_h = base_y - top
    y = lambda d: base_y - plot_h * (d / maxd)

    group_w = plot_w / len(GROUPS)
    bar_w = 70
    gap = 26

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'font-family="-apple-system,Segoe UI,Roboto,sans-serif" font-size="13">']
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    s.append(f'<text x="{left}" y="30" font-size="17" font-weight="700" fill="#0f172a">'
             f'The same LinkedIn post, before and after I taught plainly marketing</text>')
    s.append(f'<text x="{left}" y="52" fill="#64748b">plainly density (higher = more slop). '
             f'A blind judge preferred the clean version 3 out of 3.</text>')

    # baseline axis
    s.append(f'<line x1="{left}" y1="{base_y}" x2="{W-right}" y2="{base_y}" stroke="#cbd5e1"/>')

    for gi, (glabel, slop, clean) in enumerate(GROUPS):
        cx = left + group_w * gi + group_w / 2
        x_slop = cx - bar_w - gap / 2
        x_clean = cx + gap / 2
        for x0, d, color, tag in ((x_slop, slop, SLOP, "slop draft"),
                                  (x_clean, clean, CLEAN, "written with skill")):
            bh = base_y - y(d)
            if bh < 2:  # zero bar: draw a thin stub so it is visible
                s.append(f'<rect x="{x0:.0f}" y="{base_y-2:.0f}" width="{bar_w}" height="2" '
                         f'rx="1" fill="{color}" opacity="0.45"/>')
                s.append(f'<text x="{x0+bar_w/2:.0f}" y="{base_y-8:.0f}" text-anchor="middle" '
                         f'fill="#64748b" font-size="12">{d:.2f}</text>')
            else:
                s.append(f'<rect x="{x0:.0f}" y="{y(d):.0f}" width="{bar_w}" height="{bh:.0f}" '
                         f'rx="3" fill="{color}"/>')
                s.append(f'<text x="{x0+bar_w/2:.0f}" y="{y(d)-6:.0f}" text-anchor="middle" '
                         f'fill="#0f172a" font-size="13" font-weight="700">{d:.2f}</text>')
            s.append(f'<text x="{x0+bar_w/2:.0f}" y="{base_y+16:.0f}" text-anchor="middle" '
                     f'fill="#475569" font-size="11">{tag}</text>')
        s.append(f'<text x="{cx:.0f}" y="{base_y+38:.0f}" text-anchor="middle" '
                 f'fill="#0f172a" font-size="13" font-weight="600">{esc(glabel)}</text>')

    # annotation on the "before" group
    s.append(f'<text x="{left + group_w*0.5:.0f}" y="{base_y-26:.0f}" text-anchor="middle" '
             f'fill="#94a3b8" font-size="11" font-style="italic">could not tell them apart</text>')

    s.append('</svg>')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(s), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
