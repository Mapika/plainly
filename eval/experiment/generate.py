"""
generate.py — produce texts for all model × prompt × condition combinations.

Conditions:
  baseline       — plain user prompt
  human_system   — system prompt with human-writing guidance
  fewshot        — user prompt with two human samples prepended
  deslop         — baseline text post-edited by a fixer model

Output layout:
  eval/experiment/out/<condition>/<model_safe>__<prompt_id>.txt
  eval/experiment/out/<condition>/<model_safe>__<prompt_id>.meta.json

Resumable: skips if .txt already exists.
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).parent
SAMPLES_DIR = HERE.parent / "samples" / "human"
OUT_DIR = HERE / "out"

PROMPTS_FILE = HERE / "prompts.json"
MODELS_FILE = HERE / "models.json"

# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

HUMAN_GUIDANCE = (
    "Write the way a thoughtful human writer would. Be concrete and specific; "
    "prefer real detail over vague significance. Vary sentence length — mix "
    "short punchy sentences with longer ones, and never write three similar-length "
    "sentences in a row. Use plain words (say 'use', not 'utilize' or 'leverage'). "
    "Avoid: 'in today's world' style openers; 'not just X — it's Y' constructions; "
    "trailing '-ing' clauses that assert significance (underscoring, highlighting, "
    "reflecting); rule-of-three lists; booster words (transformative, game-changing, "
    "seamless, robust); and tidy 'in conclusion' wrap-ups. Commit to a point of view. "
    "Output only the piece, no preamble."
)

DESLOP_INSTRUCTIONS = (
    "You are an editor that removes AI writing tells. Rewrite the text to read as "
    "natural human prose: cut filler and booster words, break up rule-of-three lists, "
    "remove 'not just X — it's Y' constructions and trailing '-ing significance' clauses, "
    "replace vague significance with concrete statements, and vary sentence length. "
    "Preserve the original meaning and roughly the length. Output only the rewritten "
    "text, no preamble."
)

# ---------------------------------------------------------------------------
# Load human samples for fewshot
# ---------------------------------------------------------------------------

def _load_sample(name: str) -> str:
    p = SAMPLES_DIR / name
    return p.read_text().strip()


def build_fewshot_prefix() -> str:
    twain = _load_sample("twain-roughingit.md")
    orwell = _load_sample("orwell.md")
    return (
        "Here are two examples of natural human writing:\n\n"
        "EXAMPLE 1:\n" + twain + "\n\n"
        "EXAMPLE 2:\n" + orwell + "\n\n"
        "Now, in a similarly human style, do this:\n"
    )


# ---------------------------------------------------------------------------
# Safe filename component from model id
# ---------------------------------------------------------------------------

def model_safe(model_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", model_id)


# ---------------------------------------------------------------------------
# Fixer model resolution
# ---------------------------------------------------------------------------

FIXER_PREFERRED = "anthropic/claude-sonnet-4.6"
FIXER_FALLBACK = "mistralai/mistral-large-2411"


def resolve_fixer(models_endpoint_ids: set) -> str:
    if FIXER_PREFERRED in models_endpoint_ids:
        return FIXER_PREFERRED
    return FIXER_FALLBACK


def _fetch_available_models(key: str) -> set:
    url = "https://openrouter.ai/api/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return {m["id"] for m in body.get("data", [])}
    except Exception as e:
        print(f"[generate] Could not fetch model list: {e}")
        return set()


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def load_key() -> str:
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key.strip()
    key_path = HERE.parent / ".secrets" / "openrouter.key"
    if key_path.exists():
        return key_path.read_text().strip()
    raise RuntimeError("No OpenRouter API key found.")


def main():
    from openrouter import chat_completion, account_usage

    prompts = json.loads(PROMPTS_FILE.read_text())
    models = json.loads(MODELS_FILE.read_text())

    key = load_key()
    available_ids = _fetch_available_models(key)
    fixer_model = resolve_fixer(available_ids)
    print(f"[generate] Fixer model: {fixer_model}")

    fewshot_prefix = build_fewshot_prefix()

    SPEND_LIMIT_USD = 15.0
    start_usage = account_usage()
    print(f"[generate] Account usage at start: ${start_usage:.4f}")

    conditions = ["baseline", "human_system", "fewshot", "deslop"]
    for cond in conditions:
        (OUT_DIR / cond).mkdir(parents=True, exist_ok=True)

    total_generated = 0
    total_skipped = 0
    errors = []

    def check_spend():
        current = account_usage()
        spent = current - start_usage
        if spent > SPEND_LIMIT_USD:
            print(f"\n[generate] SAFETY STOP: spent ${spent:.4f} exceeds ${SPEND_LIMIT_USD:.2f}. Halting.")
            sys.exit(1)
        return current

    # Pass 1: baseline, human_system, fewshot
    for model in models:
        model_id = model["id"]
        msafe = model_safe(model_id)

        for prompt in prompts:
            pid = prompt["id"]
            ptext = prompt["prompt"]

            for cond in ("baseline", "human_system", "fewshot"):
                txt_path = OUT_DIR / cond / f"{msafe}__{pid}.txt"
                meta_path = OUT_DIR / cond / f"{msafe}__{pid}.meta.json"

                if txt_path.exists():
                    total_skipped += 1
                    continue

                if cond == "baseline":
                    messages = [{"role": "user", "content": ptext}]
                elif cond == "human_system":
                    messages = [
                        {"role": "system", "content": HUMAN_GUIDANCE},
                        {"role": "user", "content": ptext},
                    ]
                elif cond == "fewshot":
                    messages = [{"role": "user", "content": fewshot_prefix + ptext}]
                else:
                    continue

                print(f"[generate] {cond:14s} {model_id:45s} {pid} ...", end=" ", flush=True)
                result = chat_completion(model_id, messages, temperature=0.7, max_tokens=500)

                if "error" in result:
                    print(f"ERROR: {result['error'][:80]}")
                    errors.append({"model": model_id, "prompt": pid, "condition": cond, "error": result["error"]})
                    continue

                txt_path.write_text(result["text"])
                meta = {
                    "model": model_id,
                    "prompt_id": pid,
                    "condition": cond,
                    "usage": result["usage"],
                    "raw_model": result["raw_model"],
                }
                meta_path.write_text(json.dumps(meta, indent=2))
                total_generated += 1

                cost_str = ""
                usage = result.get("usage", {})
                if usage:
                    cost_str = f"  (in={usage.get('prompt_tokens',0)} out={usage.get('completion_tokens',0)})"
                print(f"OK{cost_str}")

                # Check spend every 20 generations
                if total_generated % 20 == 0:
                    check_spend()

    # Pass 2: deslop (depends on baseline)
    for model in models:
        model_id = model["id"]
        msafe = model_safe(model_id)

        for prompt in prompts:
            pid = prompt["id"]

            txt_path = OUT_DIR / "deslop" / f"{msafe}__{pid}.txt"
            meta_path = OUT_DIR / "deslop" / f"{msafe}__{pid}.meta.json"

            if txt_path.exists():
                total_skipped += 1
                continue

            baseline_txt_path = OUT_DIR / "baseline" / f"{msafe}__{pid}.txt"
            if not baseline_txt_path.exists():
                print(f"[generate] deslop SKIP (no baseline): {model_id} {pid}")
                continue

            baseline_text = baseline_txt_path.read_text()
            messages = [
                {"role": "system", "content": DESLOP_INSTRUCTIONS},
                {"role": "user", "content": baseline_text},
            ]

            print(f"[generate] {'deslop':14s} {model_id:45s} {pid} ...", end=" ", flush=True)
            result = chat_completion(fixer_model, messages, temperature=0.7, max_tokens=500)

            if "error" in result:
                print(f"ERROR: {result['error'][:80]}")
                errors.append({"model": model_id, "prompt": pid, "condition": "deslop", "error": result["error"]})
                continue

            txt_path.write_text(result["text"])
            meta = {
                "model": model_id,
                "prompt_id": pid,
                "condition": "deslop",
                "fixer_model": fixer_model,
                "usage": result["usage"],
                "raw_model": result["raw_model"],
            }
            meta_path.write_text(json.dumps(meta, indent=2))
            total_generated += 1

            cost_str = ""
            usage = result.get("usage", {})
            if usage:
                cost_str = f"  (in={usage.get('prompt_tokens',0)} out={usage.get('completion_tokens',0)})"
            print(f"OK{cost_str}")

            if total_generated % 20 == 0:
                check_spend()

    end_usage = account_usage()
    spent = end_usage - start_usage
    print(f"\n[generate] Done. Generated: {total_generated}, Skipped: {total_skipped}, Errors: {len(errors)}")
    print(f"[generate] Account usage at end: ${end_usage:.4f} (delta: ${spent:.4f})")

    if errors:
        print(f"\n[generate] Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e['model']} / {e['prompt']} / {e['condition']}: {e['error'][:100]}")


if __name__ == "__main__":
    # Add parent dir so we can import openrouter
    sys.path.insert(0, str(Path(__file__).parent))
    main()
