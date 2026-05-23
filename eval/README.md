# plainly evaluation

This is where I check whether [plainly](../plainly/) actually works. Three studies, the
data behind them, and the scripts to rerun it all.

Short version: it tells human prose from older AI prose well and rarely false-flags real
writing. The fixes it suggests read more human to an independent judge. It is much weaker
against today's frontier models, because they have mostly stopped writing the way it
watches for. That is the honest result, and it is why I treat plainly as a quality linter
rather than an AI detector.

## The three studies

### 1. Corpus and calibration (`docs/RESULTS.md`)
147 texts scored by the engine. The human side is real: HC3 answers, pre-2022 arXiv
abstracts, and public-domain passages (Twain, Thoreau, the KJV). The AI side is real model
output, not hand-written slop: HC3 ChatGPT answers, GPT-3.5 research abstracts, and a small
modern set written blind by Claude Opus, Sonnet, and Haiku.

Against 2022-era AI the engine hits AUC 0.82 while flagging only 4.3% of human texts. It
does best on scientific writing (0.92), the register where formal human prose and AI prose
look most alike. Against the modern blind set it falls to 0.67. The obvious tells are
leaving frontier models, so a tells-based score fades with them. I measured that decline on
my own corpus.

### 2. Methodology (`docs/methodology.md`)
The stats I trust, and why. The headline number is not accuracy or AUC. It is the
true-positive rate at a fixed 5% false-positive rate, calibrated on human data. Telling a
human their writing is "AI" is the expensive mistake, so I hold that rate down first and
report detection second. Everything runs in pure Python: Mann-Whitney U, Cliff's delta, AUC
from ranks, bootstrap confidence intervals.

### 3. Catch and improve (`docs/EXPERIMENT_RESULTS.md`)
10 models, via OpenRouter, each wrote the same 10 prompts. Then I tested whether three
interventions made the output read more human. A blind LLM judge from outside the test set
picked which of two texts read more human, with plainly's score kept as a check so I would
notice the tool gaming itself.

Catch: Claude Opus 4.7 wrote the most human prose, Llama 3.3 70B the least. Bigger and newer
models scored lower. Register mattered more than the model: encyclopedic overviews were the
worst offenders at 3.58, how-to guides the cleanest at 0.63.

Improve: all three interventions cut the tell count and won with the judge.

| intervention | judge win-rate vs baseline | change in density |
|---|---|---|
| deslop post-edit | 0.95 | -0.81 |
| "write human" system prompt | 0.93 | -0.54 |
| few-shot human examples | 0.77 | -0.53 |

The deslop edit won most, and it was the only one that raised sentence-length variation
instead of flattening it. The judge and plainly never disagreed about which way an edit
moved the text, so the score is tracking something a reader notices, not a quirk of its own
checklist. The whole experiment cost $2.97.

## Layout

```
eval/
├── README.md            # this file
├── docs/                # RESULTS, methodology, EXPERIMENT_RESULTS
├── data/                # the 147-text corpus + metrics.csv + MANIFEST
├── samples/             # small qualitative human/AI set
├── scripts/             # build_corpus, run_metrics, add_blind, stats, make_*_charts
├── experiment/          # OpenRouter pipeline: prompts, models, generate/score/judge/analyze
└── run_eval.py          # quick qualitative pass over samples/
```

## Reproduce

```bash
# qualitative pass over the small sample set
python3 eval/run_eval.py

# statistics over the full corpus
python3 eval/scripts/stats.py

# the model experiment (needs eval/.secrets/openrouter.key)
cd eval/experiment && python3 generate.py && python3 score.py && python3 judge.py && python3 analyze.py
```

## What to trust, and what not to

The judge is itself an LLM with its own taste, so I only ever ask it to compare two versions
of the same model's text. Two of the twelve planned models (Grok 4.3, Mistral Large) errored
on my account, so the frontier tier is thinner than I wanted. Ten prompts is a small set, one
sample per cell at temperature 0.7. The tells drift over time, so any single number here is
dated. Read it as a snapshot of mid-2026, not a permanent verdict.
