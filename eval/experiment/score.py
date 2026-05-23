"""
score.py — run plainly prescan over every out/*/*.txt and write scores.csv.

Output: eval/experiment/scores.csv
  model,prompt_id,register,condition,n_words,density,cv,opener_entropy,
  func_word_ratio,n_findings,low_conc_paras
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "out"
PROMPTS_FILE = HERE / "prompts.json"
SCORES_FILE = HERE / "scores.csv"
PRESCAN_SCRIPT = Path(__file__).parent.parent.parent / "plainly" / "scripts" / "prescan.py"

CONDITIONS = ["baseline", "human_system", "fewshot", "deslop"]

FIELDNAMES = [
    "model", "prompt_id", "register", "condition",
    "n_words", "density", "cv", "opener_entropy",
    "func_word_ratio", "n_findings", "low_conc_paras",
]


def run_prescan(txt_path: Path) -> dict | None:
    try:
        result = subprocess.run(
            [sys.executable, str(PRESCAN_SCRIPT), str(txt_path), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0 and not result.stdout.strip():
            print(f"  [score] prescan error for {txt_path.name}: {result.stderr[:100]}")
            return None
        data = json.loads(result.stdout)
        return data
    except subprocess.TimeoutExpired:
        print(f"  [score] prescan timed out: {txt_path.name}")
        return None
    except Exception as e:
        print(f"  [score] prescan failed: {txt_path.name}: {e}")
        return None


def extract_metrics(data: dict) -> dict:
    metrics = data.get("metrics", {})
    burstiness = metrics.get("burstiness", {})
    lexical = metrics.get("lexical", {})
    concreteness = metrics.get("concreteness", {})
    findings = data.get("findings", [])

    n_words = burstiness.get("n", 0)
    # n is sentence count from burstiness; try to get word count another way
    # prescan doesn't directly output word count, use n_words from sentence lengths
    # Actually let's compute from text directly — we'll do it in the caller

    cv = burstiness.get("cv", 0.0)
    opener_entropy = metrics.get("opener_entropy", 0.0)
    func_word_ratio = lexical.get("function_word_ratio", 0.0)
    density = data.get("density", 0.0)
    n_findings = len(findings)
    low_conc_paras = len(concreteness.get("low_paragraphs", []))

    return {
        "cv": cv,
        "opener_entropy": opener_entropy,
        "func_word_ratio": func_word_ratio,
        "density": density,
        "n_findings": n_findings,
        "low_conc_paras": low_conc_paras,
    }


def count_words(txt_path: Path) -> int:
    try:
        text = txt_path.read_text()
        return len(text.split())
    except Exception:
        return 0


def main():
    prompts = json.loads(PROMPTS_FILE.read_text())
    register_map = {p["id"]: p["register"] for p in prompts}

    rows = []
    total = 0
    errors = 0

    for cond in CONDITIONS:
        cond_dir = OUT_DIR / cond
        if not cond_dir.exists():
            continue
        txt_files = sorted(cond_dir.glob("*.txt"))
        print(f"[score] Condition '{cond}': {len(txt_files)} files")

        for txt_path in txt_files:
            stem = txt_path.stem  # <model_safe>__<prompt_id>
            if "__" not in stem:
                continue
            # Split on last __ that precedes a known prompt id
            parts = stem.rsplit("__", 1)
            if len(parts) != 2:
                continue
            msafe, pid = parts

            # Read meta to get original model id
            meta_path = txt_path.with_suffix(".meta.json")
            model_id = msafe  # fallback
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    model_id = meta.get("model", msafe)
                except Exception:
                    pass

            register = register_map.get(pid, "unknown")
            n_words = count_words(txt_path)

            data = run_prescan(txt_path)
            if data is None:
                errors += 1
                continue

            m = extract_metrics(data)
            rows.append({
                "model": model_id,
                "prompt_id": pid,
                "register": register,
                "condition": cond,
                "n_words": n_words,
                "density": m["density"],
                "cv": m["cv"],
                "opener_entropy": m["opener_entropy"],
                "func_word_ratio": m["func_word_ratio"],
                "n_findings": m["n_findings"],
                "low_conc_paras": m["low_conc_paras"],
            })
            total += 1

    print(f"\n[score] Scored {total} files, {errors} errors")

    with open(SCORES_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[score] Written: {SCORES_FILE}")


if __name__ == "__main__":
    main()
