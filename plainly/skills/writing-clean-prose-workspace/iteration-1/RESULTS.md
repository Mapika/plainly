# writing-clean-prose — iteration-1 benchmark

3 prompts (blog intro, README section, Series-A post), with-skill vs no-skill baseline,
Opus 4.7 subagents. Quality scored two ways: plainly `density` (deterministic) and a
blind `prose-judge` (haiku) that never saw the metrics or which text was the edit.

## Quality

| eval | with-skill density | baseline density | blind judge |
|---|---|---|---|
| blog-intro | 0.00 | 0.00 | **with-skill** |
| readme-why | 0.00 | 0.36 (tricolon) | **with-skill** |
| marketing-seriesa | 0.00 | 0.00 | **with-skill** |

- **Density is flat.** On fresh Opus prose, baseline output already scores ~0 — the obvious
  surface tells are gone. The metric can't discriminate. (Exactly the "tells fade on modern
  models" effect the eval documents: AUC 0.82 → 0.67.)
- **The blind judge discriminates cleanly: 3/3 for the skill.** Where the deterministic
  score is blind, the judge sees the difference — concrete specifics, varied rhythm, no
  rule-of-three padding, no booster/emoji slop.

## Efficiency (mean per run)

| | with-skill | baseline | delta |
|---|---|---|---|
| tokens | 19,832 | 12,457 | **+7,375 (+59%)** |
| wall-clock | 20.5 s | 12.7 s | +7.8 s (+61%) |

The skill reads 3 reference files, so it costs ~60% more tokens and time. The payoff is a
judge-visible quality gain the metric misses.

## Actionable finding for the engine

The marketing **baseline** — "I'm thrilled to share", "double down on what matters",
"This is just the beginning", "The best is yet to come 🚀" — is textbook LinkedIn slop and
scored **0.00 density**. plainly's patterns miss hype/cliché phrases and emoji. This is a
concrete gap to close in `data/patterns.json` / `data/lexical-tells.json`.

## Takeaways

1. The skill works — a blind judge prefers it every time — but its value is **qualitative**,
   not visible to the density metric on frontier-model prose.
2. This is the strongest argument yet for the `prose-judge` we added to the deslopper:
   metrics alone under-credit good edits; the judge is the half that still works.
3. Next engine improvement: add a hype/cliché lexical tier (and emoji) so density catches
   marketing slop the way a reader does.
