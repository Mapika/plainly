# Tells Catalog — The Negative Standard (2026)

> **These are writing-quality signals, not authorship verdicts.** A tell is worth fixing
> whoever wrote it. `plainly` never claims to detect "AI"; it flags prose that reads as
> generic, vague, or templated.

Weights and tiers here are kept **in sync with** `scripts/data/patterns.json` and
`scripts/data/lexical-tells.json`. Severity is assigned by *clustering* (total finding
weight per paragraph), not by any single hit — see `.plainly.toml` (`critical = 6`,
`moderate = 3`). Structural tells carry the weight because they are durable across model
generations; lexical tells are low-weight and decay once publicized.

Key sources: Wikipedia *Signs of AI writing*
(<https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>); Kobak et al., excess
vocabulary (<https://arxiv.org/abs/2406.07016>); the burstiness/stylometry literature; and
the corpus "decline effect" work (<https://arxiv.org/abs/2502.09606>).

---

## Critical — durable structural tells (fix first)

### Trailing significance participle  ·  weight 3  ·  current  ·  `participle-tail`
Main clause + comma + present-participle that asserts vague importance: *…, underscoring its
role…*, *…, highlighting the significance of…*, *…, reflecting the continued relevance of…*.
Measured at 2–5× the human rate. Manufactures analysis while adding zero information.
- Before: *We opened three offices, underscoring our commitment to growth.*
- After: *We opened three offices last year, adding 400 jobs.*

### "It's not just X — it's Y" antithesis  ·  weight 3  ·  current  ·  `antithesis-not-just`
Explicit antithesis and negative parallelism (*not only … but …*) used as a *default* rather
than for effect. Concedes a position nobody held to sound nuanced.
- Before: *It's not just a tool, it's a movement.*
- After: *The tool links your notes so you can find old ideas later.*

### Booster / puffery register  ·  weight 3 (phrase) / 2 (word)  ·  current  ·  `stands as a testament`, `transformative`, `game-changing`
Inflates the mundane into the momentous: *stands as a testament*, *serves as*, *marks a
pivotal moment*, *transformative*, *game-changing*. Reads like ad copy regardless of topic.
- Before: *This tool stands as a testament to the transformative power of innovation.*
- After: *The tool cut our build time from 40 minutes to 6.*

### Hollow-profundity ending  ·  current  ·  (LLM-judged)
Unearned uplift that closes on abstract nouns (*authenticity, connection, the journey*) with
no concrete anchor. "Something shifted." "It was never about the code."
- Fix: cut it, or land a concrete takeaway.

---

## Moderate — single strong tells / pervasive patterns

### Compulsive tricolon / rule-of-three  ·  weight 1  ·  current  ·  `tricolon`
*fast, reliable, and scalable*. The tell is the *relentless regularity*, not the device.
Humans vary list lengths; flag when clustered.
- Before: *It's fast, reliable, and scalable.* → After: *It handles 50k requests a second.*

### Formulaic intro / conclusion  ·  weight 2  ·  current  ·  `formulaic-intro`
*In today's fast-paced world…*, *At its core…*, *When it comes to…*; closers *In conclusion*,
*Ultimately*, *At the end of the day*.
- Before: *In today's fast-paced digital landscape, businesses must adapt.*
- After: *Three competitors shut down this year. Here's what they missed.*

### Pervasive hedging / both-sidesing  ·  current  ·  (LLM-judged)
Every claim softened (*often, typically, generally, can be, may, tends to*). If every third
sentence carries a qualifier, it reads as machine output. Commit to a position.

### Copula avoidance  ·  current  ·  (LLM-judged)
Substituting *serves as / functions as / represents / boasts* for plain *is/has*. Inflates
register. Prefer *is*.

### Chronically abstract paragraph  ·  (deterministic: low concreteness)
Flagged by the Brysbaert concreteness scorer when a paragraph's mean concreteness falls below
`.plainly.toml`'s `concreteness.min_mean` (default 2.6). The *leverage-synergies-to-drive-
impactful-outcomes* register. Fix with concrete nouns and specific facts.

### Inline bold-header bullets  ·  weight 1  ·  current  ·  `bold-header-bullet`
`- **Header**: one sentence`, repeated mechanically. Templated listicle formatting (markdown
leaking into prose). Prose should flow; reserve lists for genuine enumerations.

---

## Minor / Stylistic — low-confidence, contextual

### Stale lexical set  ·  weight 1  ·  stale  ·  *delve, tapestry, underscore, pivotal*
The famous 2023 list. **Declining since April 2024** once publicized, so a hit today is as
likely a human who missed the memo as an LLM. Low weight; meaningful only in clusters.

### Current lexical set  ·  weight 1–2  ·  current  ·  *nuanced, robust, leverage, utilize, seamless*
Still over-produced by frontier models (especially RLHF artifacts like *nuanced*). Prefer
plain equivalents: *leverage/utilize → use*, *robust → strong/reliable*, *seamless → (cut)*.

### Connectives  ·  weight 1  ·  current  ·  *moreover, furthermore*; *it's worth noting / it's important to note* (weight 2)
Throat-clearing and metadiscourse. Usually cuttable with no loss.

### Em-dash overuse  ·  weight 1  ·  current  ·  `em-dash`  ·  **OFF by default**
OpenAI suppressed it (Nov 2025) and the human baseline overlaps AI entirely, so raw em-dash
count is a noisy, model-dependent signal with high false-positive risk. Disabled unless you
opt in via `.plainly.toml` (`rules.em_dash = true`), and even then weak — surface only
alongside other signals.

### Formatting / typography leakage  ·  current  ·  (LLM-judged)
Curly quotes where a person typing plainly would use straight ones; reflexive boldface;
Title Case In Every Heading; emoji as section dividers. Markdown habits leaking into prose.

---

## Two cross-cutting rules for the judge

- **Score on co-occurrence, not single hits.** A cluster of *underscore* + *pivotal* + a
  participle tail in one paragraph is far more diagnostic than any one of them alone.
- **Low burstiness is the strongest measurable tell.** Uniform sentence length (coefficient
  of variation below `.plainly.toml`'s `burstiness.min_cv`, default 0.35) signals AI cadence.
  But fine-tuned/"humanized" text can fake it, so treat it as necessary, not sufficient.
