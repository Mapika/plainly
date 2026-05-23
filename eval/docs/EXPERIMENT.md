# Experiment: Catching and Reducing "AI Feel" Across Models

**Status:** design, pending review → then build.
**Question:** (1) *Catch* — how "AI-sounding" is each model's default non-fiction prose, by register? (2) *Improve* — which interventions move that output toward a human feel, measured independently?

## Design

### Factors
- **Models (~12)** via OpenRouter, spread across labs / sizes / eras. Candidate set (final list verified against the live OpenRouter model list at build time): GPT-4o, GPT-4o-mini, a GPT-5-class model; Claude Opus / Sonnet / Haiku; Gemini 2.5 Flash + a Pro; Llama 3.3 70B; Mistral Large; DeepSeek V3/R1; Qwen 2.5 72B.
- **Prompts (10)** across registers: blog/essay (×3), marketing/product (×2), how-to/docs (×2), scientific explainer (×2), encyclopedic overview (×1). Neutral, prose-eliciting, **no mention of AI-tells** (blind). Reuses the 5 existing blind prompts + 5 new.
- **Conditions (4):**
  1. **Baseline** — plain prompt (control).
  2. **Human system prompt** — prevention-skill guidance (concrete, vary rhythm, no boosters/participle-tails/antithesis) as a system message.
  3. **Few-shot** — 2–3 real human passages (from our corpus) prepended as style anchors.
  4. **Deslopper post-edit** — baseline output, then a fix pass (deslopper instructions applied via API) — re-measured.

Generation: conditions 1–3 = 12×10×3 = 360; condition 4 derives from the 120 baselines = 120. **≈480 short generations** + judge calls. Fixed temperature (0.7), capped length, logged token cost.

### Measures
- **Primary (independent): blind LLM-judge.** A strong model *not in the test set* does blind pairwise "which reads more like a human wrote it?" — for each (model × prompt): baseline vs each intervention, order randomized, source hidden. Report per-intervention **win-rate vs baseline** with bootstrap CIs.
- **Secondary (plainly): density, burstiness CV, concreteness, tell counts** — reported, but explicitly **not the optimization target** (avoids Goodharting our own tool). Triangulates with the judge.

### Analysis
- **Catch:** rank models by baseline density & CV; AUC of each model's baseline vs the human reference distribution; per-register breakdown.
- **Improve:** paired (per model×prompt) baseline→intervention deltas. Primary = judge win-rate; secondary = Δdensity / Δcv / Δconcreteness. Paired test = **Wilcoxon signed-rank** (stdlib). Which intervention helps most, and does it generalize across models/registers? Watch for a **plainly-vs-judge divergence** (intervention games plainly but the judge disagrees → evidence of Goodharting).
- Honest caveats: a model judging models (judge bias), temperature variance, prompt set size, OpenRouter model-version drift.

## Pipeline (to build)
```
eval/experiment/
├── prompts.json            # 10 prompts × register tags
├── models.json             # resolved OpenRouter model ids (verified at build)
├── openrouter.py           # thin client (reads key from eval/.secrets/openrouter.key)
├── generate.py             # (model × prompt × condition) -> eval/experiment/out/*.txt + meta
├── score.py                # run plainly prescan over outputs -> scores.csv
├── judge.py                # blind pairwise human-feel judging -> judgements.csv
└── analyze.py              # catch + improve stats -> EXPERIMENT_RESULTS.md
```
Stdlib + `urllib` only (no new deps). Costs logged; resumable (skip already-generated).

## Secrets
OpenRouter key read from `eval/.secrets/openrouter.key` (gitignored — never committed, never echoed).

## Out of scope
Fine-tuning models; training a classifier; image/non-text. This measures prompt/post-edit interventions only.
