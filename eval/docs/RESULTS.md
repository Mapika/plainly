# plainly — Evaluation Results

**What we measured:** how well plainly's deterministic `density` score separates human-written
from AI-generated non-fiction prose, across registers including scientific writing, using the
methodology in [`methodology.md`](methodology.md). The headline operating metric, per the
AI-text-detection literature (RAID, Binoculars), is **TPR at a fixed low (5%) false-positive
rate** — not accuracy or pooled AUC.

**Corpus** (`../data/metrics.csv`, 147 texts):
- **Real labeled set (132):** 70 human / 62 AI across general, QA, finance, medicine, scientific.
  Human = HC3 + pre-2022 arXiv abstracts. AI = HC3 ChatGPT answers + GPT-3.5 research abstracts
  (NicolaiSivesind/ChatGPT-Research-Abstracts). Era ≈ late-2022 GPT-3.5.
- **Modern blind set (15):** Claude Opus/Sonnet/Haiku (2026), each given the same 5 neutral
  writing prompts with **no knowledge** of plainly or what we measure — unbiased modern AI prose.

All AI text is genuine model output; none was written by the analyst. Stats are stdlib-only
(`../scripts/stats.py`): AUC = rank-sum/(n₁n₂), Cliff's δ = 2·AUC−1, Mann-Whitney U
(tie-corrected normal approx), TPR@5%FPR (threshold calibrated on human data), percentile
bootstrap CIs (B=4000).

## Result 1 — On ~2022-era AI, the tool separates classes strongly

| metric | value |
|---|---|
| mean density (human / AI) | 0.26 / 1.16 (~4.4×) |
| **AUC** | **0.822** (95% CI 0.750–0.889) |
| Cliff's δ | 0.644 — **large** effect (Romano: ≥0.474) |
| Mann-Whitney p | 8.2 × 10⁻¹² |
| human FPR at threshold | 4.3% |
| **TPR @ 5% FPR** | **41.9%** (95% CI 6–53%) |

Large, highly significant separation — **but** at a strict 5%-FPR operating point the tool
catches only ~42% of 2022 AI. This AUC-vs-TPR gap is the methodology's central lesson: a coarse
score can rank well (good AUC) yet detect modestly at low FPR. plainly is a **quality signal,
not a forensic detector** — and the low human FPR (4.3%) is the property we most wanted.

### Per-register (where the tells concentrate)
| domain | AUC | mean human / AI |
|---|---|---|
| medicine | 0.950 | 0.00 / 1.00 |
| scientific | 0.915 | 0.41 / 1.61 |
| qa | 0.858 | 0.08 / 0.96 |
| general | 0.806 | 0.33 / 1.34 |
| finance | 0.600 | 0.27 / 0.50 |

Strongest in **scientific/medical** writing — exactly the register the founding corpus study
(Kobak et al., PubMed) flagged, and the one the user asked us to cover. Critically, **human
scientific prose kept a low score** (0.41) despite its natural nominalizations and hedging, so
the genre does not trigger mass false positives.

### Length confound (honest caveat)
AI texts are longer (224 vs 178 words; AUC(words) = 0.665, p = 0.001). Length carries *some*
signal, but density's AUC (0.822) clearly exceeds length-only AUC (0.665), so density adds
real signal beyond length. Not length-adjusted here — a limitation.

## Result 2 — Modern frontier AI (2026) largely evades the tells

| | human | blind Claude 2026 |
|---|---|---|
| mean density | 0.26 | 0.67 |
| AUC | — | **0.671** (δ=0.343, medium; p=0.011) |
| TPR @ the 2022-calibrated threshold | — | **26.7%** |

Separation **drops from 0.82 → 0.67**, and only ~27% of modern AI pieces clear the
human-calibrated threshold. This is the **decline / human-LLM coevolution effect**
(arXiv 2502.09606) measured on our own corpus: the obvious surface tells have been trained out
of frontier models, so a tells-based score loses discriminative power with each generation.
It is the strongest possible argument for our **"quality, not detection"** framing — plainly
should never be sold as an AI detector, and this is why.

### Per model tier (blind, 2026)
| model | mean density | mean burstiness CV |
|---|---|---|
| Sonnet | 0.41 | 0.530 |
| Opus | 0.68 | 0.475 |
| Haiku | 0.93 | 0.615 |

Sonnet wrote cleanest; Haiku tripped the most tells (a Silk Road overview hit boosters +
tricolons). Opus had the most *uniform* sentence length (lowest CV) — mildly against the
research's prediction that Opus reads most varied, on this tiny n=5/model sample.

## Honest limitations
- **Small modern set** (15) and **first-N (not random) sampling** of the dataset.
- **Mixed eras** in the "AI" class (2022 GPT-3.5 vs 2026 Claude) — reported separately, never pooled.
- **Length not controlled** in the headline density comparison.
- A **single-snapshot** result: tells are non-stationary; re-run periodically.
- Bootstrap is percentile (slightly undercovers for AUC); DeLong variance would be tighter.

## Bottom line
plainly is a **strong quality linter and a good detector of older/obvious AI slop** (AUC 0.82,
large effect, low human FPR, best on scientific writing) — and a **deliberately poor detector of
modern frontier prose** (AUC 0.67, ~27% TPR), which validates both the design (cluster-weighted,
low-FPR, em-dash off) and the framing (a writing-quality tool, not an authorship verdict).
