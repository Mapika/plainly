---
description: Audit prose for LLM style smells and report tiered findings with rewrites (no edits).
argument-hint: "[file path] | --diff"
allowed-tools: Read, Bash, Task
---

# /plainly check

Audit the target prose and produce a tiered, trustworthy report. **Diagnose only — make no edits.**

## Steps
1. Resolve the target from `$ARGUMENTS`: a file path, or `--diff` for prose changed vs HEAD. If neither is given, ask which file to check.
2. Run the deterministic engine and capture JSON (the fast, free floor):
   - File: `python "${CLAUDE_PLUGIN_ROOT}/scripts/prescan.py" <path> --json`
   - Diff: `python "${CLAUDE_PLUGIN_ROOT}/scripts/prescan.py" --diff --json`
3. **Semantic pass — dispatch the `tell-matcher` agent** (a cheap `haiku` subagent) on the same target. It catches the tells the regex engine cannot: contraction antithesis ("isn't just X — it's Y"), inflected boosters, pervasive hedging, copula-avoidance, formulaic intros/conclusions, and vague abstraction. It returns JSON findings (`rule`, verbatim `span`, `why`). This runs in-session — no API key needed.
4. Load `references/tells-catalog.md` and `references/positive-standard.md` from the `writing-clean-prose` skill for judgment criteria.
5. **Merge and judge (token-efficient):**
   - Combine the engine findings with the `tell-matcher` findings; **de-duplicate** where they overlap (locate each matcher `span` in the text for its `file:line`).
   - If `density` is low and matcher findings are few, reason only about the flagged spans plus ±1 sentence of context; if either is high, read the whole document for systemic rhythm/flow.
   - **Dismiss false positives** (a single justified em-dash, a legitimate nominalization, a real three-item list). Apply the genre profile.
   - Mark **Critical** when signals agree or a tell is unambiguous.
6. **Emit the report**, grouped Critical → Moderate → Minor. For each finding: `file:line`, the offending text, a one-line **why**, and a concrete suggested rewrite.
7. Close with a one-paragraph read on concreteness, rhythm (burstiness), and voice, plus the engine's `density` and burstiness `cv`.

## Rules
- Frame everything as writing quality, never as an "AI detection" verdict.
- Never nag on a single justified instance; respect `.plainly.toml` allowlist/toggles (the engine already applied them).
