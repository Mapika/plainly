"""
judge.py — blind pairwise LLM judge for human-feel comparison.

For each model × prompt, compare baseline vs {human_system, fewshot, deslop}.
Order (A/B assignment) is randomized. Judge replies A or B.

Output: eval/experiment/judgements.csv
  model,prompt_id,condition,winner(intervention|baseline|invalid)

Judge model candidates (NOT in models.json):
  google/gemini-2.5-pro → anthropic/claude-opus-4.6 → openai/gpt-5.5
"""
import csv
import json
import os
import random
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "out"
MODELS_FILE = HERE / "models.json"
PROMPTS_FILE = HERE / "prompts.json"
JUDGEMENTS_FILE = HERE / "judgements.csv"

JUDGE_CANDIDATES = [
    "anthropic/claude-opus-4.6",
    "openai/gpt-5.5",
    "google/gemini-2.5-flash",
]

JUDGE_PROMPT_TEMPLATE = (
    "Below are two short texts, A and B, on the same topic. "
    "Which reads more like it was genuinely written by a human (not AI-generated)? "
    "Reply with exactly one character: A or B."
    "\n\nText A:\n{text_a}\n\nText B:\n{text_b}"
)

INTERVENTIONS = ["human_system", "fewshot", "deslop"]

FIELDNAMES = ["model", "prompt_id", "condition", "winner"]


def load_key() -> str:
    env_key = os.environ.get("OPENROUTER_API_KEY", "")
    if env_key:
        return env_key.strip()
    key_path = HERE.parent / ".secrets" / "openrouter.key"
    if key_path.exists():
        return key_path.read_text().strip()
    raise RuntimeError("No OpenRouter API key found.")


def _fetch_available_models(key: str) -> set:
    url = "https://openrouter.ai/api/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return {m["id"] for m in body.get("data", [])}
    except Exception as e:
        print(f"[judge] Could not fetch model list: {e}")
        return set()


def resolve_judge(available: set) -> str:
    for candidate in JUDGE_CANDIDATES:
        if candidate in available:
            print(f"[judge] Using judge model: {candidate}")
            return candidate
    # Fallback: try all anyway (maybe available set was incomplete)
    print(f"[judge] WARNING: none of the judge candidates in available list; trying first")
    return JUDGE_CANDIDATES[0]


def model_safe(model_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", model_id)


def read_txt(condition: str, msafe: str, pid: str) -> str | None:
    p = OUT_DIR / condition / f"{msafe}__{pid}.txt"
    if p.exists():
        return p.read_text().strip()
    return None


def main():
    from openrouter import chat_completion, account_usage

    random.seed(42)

    models = json.loads(MODELS_FILE.read_text())
    prompts = json.loads(PROMPTS_FILE.read_text())

    key = load_key()
    available = _fetch_available_models(key)
    judge_model = resolve_judge(available)

    # Load already-done judgements for resumability
    done_keys: set = set()
    existing_rows: list = []
    if JUDGEMENTS_FILE.exists():
        with open(JUDGEMENTS_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                done_keys.add((row["model"], row["prompt_id"], row["condition"]))
    print(f"[judge] Already judged: {len(done_keys)} pairs")

    start_usage = account_usage()
    print(f"[judge] Account usage at start: ${start_usage:.4f}")

    rows = list(existing_rows)
    total_new = 0
    errors = 0

    for model in models:
        model_id = model["id"]
        msafe = model_safe(model_id)

        for prompt in prompts:
            pid = prompt["id"]

            baseline_text = read_txt("baseline", msafe, pid)
            if baseline_text is None:
                continue

            for interv in INTERVENTIONS:
                if (model_id, pid, interv) in done_keys:
                    continue

                interv_text = read_txt(interv, msafe, pid)
                if interv_text is None:
                    continue

                # Randomize A/B assignment
                if random.random() < 0.5:
                    text_a, text_b = baseline_text, interv_text
                    a_is_baseline = True
                else:
                    text_a, text_b = interv_text, baseline_text
                    a_is_baseline = False

                judge_content = JUDGE_PROMPT_TEMPLATE.format(text_a=text_a, text_b=text_b)
                messages = [{"role": "user", "content": judge_content}]

                print(f"[judge] {model_id:45s} {pid} vs {interv} ...", end=" ", flush=True)
                result = chat_completion(judge_model, messages, temperature=0.0, max_tokens=10)

                if "error" in result:
                    print(f"ERROR: {result['error'][:80]}")
                    errors += 1
                    rows.append({
                        "model": model_id,
                        "prompt_id": pid,
                        "condition": interv,
                        "winner": "invalid",
                    })
                    total_new += 1
                    continue

                text = result.get("text")
                if not text:
                    print("EMPTY")
                    errors += 1
                    rows.append({
                        "model": model_id,
                        "prompt_id": pid,
                        "condition": interv,
                        "winner": "invalid",
                    })
                    total_new += 1
                    continue
                answer = text.strip().upper()
                # Extract just A or B
                match = re.search(r"\b([AB])\b", answer)
                if match:
                    choice = match.group(1)
                else:
                    # Try first non-space char
                    clean = re.sub(r"[^AB]", "", answer)
                    choice = clean[0] if clean else "?"

                if choice == "A":
                    winner = "baseline" if a_is_baseline else "intervention"
                elif choice == "B":
                    winner = "intervention" if a_is_baseline else "baseline"
                else:
                    winner = "invalid"

                print(f"{choice} → {winner}")

                rows.append({
                    "model": model_id,
                    "prompt_id": pid,
                    "condition": interv,
                    "winner": winner,
                })
                done_keys.add((model_id, pid, interv))
                total_new += 1

                # Write incrementally every 10 new judgements
                if total_new % 10 == 0:
                    _write_csv(rows)

    _write_csv(rows)
    end_usage = account_usage()
    spent = end_usage - start_usage
    print(f"\n[judge] New judgements: {total_new}, Errors: {errors}")
    print(f"[judge] Account usage at end: ${end_usage:.4f} (delta: ${spent:.4f})")
    print(f"[judge] Written: {JUDGEMENTS_FILE}")


def _write_csv(rows: list):
    with open(JUDGEMENTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
