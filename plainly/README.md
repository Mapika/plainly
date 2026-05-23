# plainly

Catch and fix the patterns that make non-fiction prose read as LLM-generated — overused
words, "AI" sentence shapes, discourse tics, and vague abstraction — and replace them with
clear, concrete, human writing.

**plainly reports writing-quality "style smells," not an "is this AI?" verdict.** The same
tics are bad writing whoever produced them. This framing is honest, it sidesteps the
detector-evasion arms race, and it avoids the documented harm of AI detectors (which
false-flag non-native writers ~60% of the time). plainly is a clarity assistant, not a
detector.

Domains: essays/blog/general prose, technical docs/READMEs, and marketing/copy. Fiction is
out of scope.

## What's different

Most "humanizer" tools are a list of patterns plus a one-shot rewrite, and none of them ship
actual detection code. plainly's edge:

- **A real, dependency-free detection engine** (`scripts/prescan.py`) that computes genuine
  metrics — sentence-length variation (burstiness), stylometry, punctuation rates,
  concreteness — with line numbers. Not prose instructions; code.
- **Three coordinated capabilities** over one shared knowledge base: diagnose, fix, prevent.
- **Cluster-based severity** — no single tell is decisive; weight is assigned by
  co-occurrence and density.
- **An affirmative style standard** (Strunk, Orwell, Williams, Zinsser, Pinker) — fixes aim
  *at* good writing, not just away from tells.
- **A concreteness engine** (Brysbaert lexicon) — a deterministic "show, don't tell" check.

## The three capabilities

| | What it does |
|---|---|
| **`/plainly:check [file]`** | Audits prose and reports tiered findings (Critical → Moderate → Minor) with line, reason, and a suggested rewrite. Diagnose only — no edits. Pass `--diff` to check only changed prose. |
| **`deslopper` agent** | Fixes a draft via targeted, paragraph-scoped edits (not full regeneration), preserves your voice, keeps rhythm varied, and shows a before/after diff. |
| **`writing-clean-prose` skill** | Loads automatically when Claude writes prose for you, so output avoids the tells in the first place. |

## How detection works (hybrid)

1. `scripts/prescan.py` runs first — a pure-stdlib pass that emits structured JSON: findings
   (with spans + line numbers + weights), burstiness, stylometry, low-concreteness
   paragraphs, and a document-level tell-density score.
2. Claude judges the engine output against the catalog: confirms real tells, dismisses false
   positives, applies your genre profile, and assigns severity by clustering.

Lexical word-lists are intentionally low-weight and **dated/versioned** (`scripts/data/`) —
they decay once publicized, so structural tells carry the weight. The **em-dash is off by
default** (a noisy, model-dependent signal); enable it in config if you want it.

## Prose-as-code

Treat style smells like a lint step:

- `python scripts/prescan.py --diff --fail-over 4` checks only changed prose and exits
  non-zero past a density threshold.
- `ci/pre-commit` — a git pre-commit hook that gates staged prose.
- `ci/github-action.yml` — an example CI gate for pull requests.

CI/hook mode gates or annotates only; it never auto-rewrites. Auto-fix belongs to the
interactive `deslopper` agent.

## Configuration — `.plainly.toml`

Copy the shipped `.plainly.toml` into your repo root and edit. Keys:

| Section | Key | Meaning |
|---|---|---|
| `[severity]` | `critical`, `moderate` | Cluster weight per paragraph to reach each tier. |
| `[rules]` | `em_dash` | Enable the (off-by-default) em-dash tell. |
| `[burstiness]` | `min_cv` | Flag documents whose sentence-length variation falls below this. |
| `[concreteness]` | `min_mean` | Flag paragraphs below this mean concreteness (1=abstract, 5=concrete). |
| `[genre]` | `default` | `prose` \| `docs` \| `marketing`. |
| `[allow]` | `terms` | Words never flagged (e.g. a product literally named "Tapestry"). |

## Requirements

- **Python 3.11+** (uses stdlib `tomllib`). **Zero third-party dependencies** — runs wherever
  Claude Code runs.

## Concreteness data

`scripts/data/concreteness.csv` ships with a minimal stand-in. For full coverage, obtain the
Brysbaert et al. (2014) 40k concreteness norms and run `scripts/build_concreteness.py` to
regenerate the CSV.

## Roadmap (v2)

- **Learn-your-voice rewrite** — rewrite toward *your* style (from a sample corpus) instead
  of a generic "human" voice.
- **Teaching loop** — track your recurring tics over time; opt-in coach mode.
- **Optional "deep" extras** — Vale shell-out for POS-based detection, and local GPT-2/KenLM
  perplexity. Both gracefully no-op when absent.

Never planned: an AI-detector / "bypass detection" score.

## Credits

Built from current corpus studies and editor consensus (Wikipedia's *Signs of AI writing*,
Kobak et al. on excess vocabulary, the burstiness/stylometry literature) and the classic
style authorities (Strunk & White, Orwell, Williams, Zinsser, Pinker). Sources are cited
inline in `skills/writing-clean-prose/references/`.
