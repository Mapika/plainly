"""
analyze.py — statistical analysis of the catch/improve experiment.

Reads:
  eval/experiment/scores.csv
  eval/experiment/judgements.csv
  eval/data/metrics.csv  (human reference distribution)

Writes:
  eval/docs/EXPERIMENT_RESULTS.md
"""
import csv
import json
import math
import statistics
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
SCORES_FILE = HERE / "scores.csv"
JUDGEMENTS_FILE = HERE / "judgements.csv"
METRICS_FILE = HERE.parent / "data" / "metrics.csv"
RESULTS_FILE = HERE.parent / "docs" / "EXPERIMENT_RESULTS.md"


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# AUC (Mann-Whitney U statistic normalised)
# ---------------------------------------------------------------------------

def auc_mann_whitney(ai_vals: list[float], human_vals: list[float]) -> float:
    """
    AUC = P(AI score > human score).
    = (#(ai > human) + 0.5 * #(ai == human)) / (n_ai * n_human)
    Higher AUC means AI has higher density (more tells) relative to human.
    """
    n1 = len(ai_vals)
    n2 = len(human_vals)
    if n1 == 0 or n2 == 0:
        return float("nan")
    gt = sum(1 for a in ai_vals for h in human_vals if a > h)
    tie = sum(1 for a in ai_vals for h in human_vals if a == h)
    return (gt + 0.5 * tie) / (n1 * n2)


# ---------------------------------------------------------------------------
# Wilcoxon signed-rank test (stdlib implementation)
# ---------------------------------------------------------------------------

def wilcoxon_signed_rank(diffs: list[float]) -> tuple[float, float]:
    """
    Two-sided Wilcoxon signed-rank test.
    Returns (W_statistic, p_value) using normal approximation.
    """
    # Remove zeros
    nonzero = [d for d in diffs if d != 0.0]
    n = len(nonzero)
    if n < 4:
        return (float("nan"), float("nan"))

    abs_diffs = [abs(d) for d in nonzero]
    signs = [1 if d > 0 else -1 for d in nonzero]

    # Rank the absolute differences
    indexed = sorted(enumerate(abs_diffs), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j

    W_plus = sum(r for r, s in zip(ranks, signs) if s > 0)
    W_minus = sum(r for r, s in zip(ranks, signs) if s < 0)
    W = min(W_plus, W_minus)

    # Normal approximation
    mean_W = n * (n + 1) / 4.0
    var_W = n * (n + 1) * (2 * n + 1) / 24.0
    if var_W <= 0:
        return (W, float("nan"))
    z = (W - mean_W) / math.sqrt(var_W)
    # Two-sided p-value using normal CDF approximation
    p = 2.0 * _norm_cdf(z)  # z is negative for W < mean, so use abs
    return (W, p)


def _norm_cdf(z: float) -> float:
    """Standard normal CDF via error function."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _norm_sf(z: float) -> float:
    return 1.0 - _norm_cdf(z)


def wilcoxon_p(diffs: list[float]) -> tuple[float, float]:
    W, p = wilcoxon_signed_rank(diffs)
    # Recalculate properly: z should use abs(W - mean_W)
    nonzero = [d for d in diffs if d != 0.0]
    n = len(nonzero)
    if n < 4:
        return W, p
    mean_W = n * (n + 1) / 4.0
    var_W = n * (n + 1) * (2 * n + 1) / 24.0
    z_abs = abs(W - mean_W) / math.sqrt(var_W)
    p_corrected = 2.0 * _norm_sf(z_abs)
    return W, p_corrected


# ---------------------------------------------------------------------------
# Judge win-rate with CI
# ---------------------------------------------------------------------------

def judge_win_rate(judgements: list[dict], condition: str) -> dict:
    """Return win_rate, ci_lo, ci_hi, n for the given intervention condition."""
    relevant = [j for j in judgements if j["condition"] == condition and j["winner"] != "invalid"]
    n = len(relevant)
    if n == 0:
        return {"win_rate": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"), "n": 0}
    wins = sum(1 for j in relevant if j["winner"] == "intervention")
    p = wins / n
    margin = 1.96 * math.sqrt(p * (1 - p) / n) if n > 0 else float("nan")
    return {"win_rate": p, "ci_lo": max(0.0, p - margin), "ci_hi": min(1.0, p + margin), "n": n}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fmt(v, decimals=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.{decimals}f}"


def main():
    scores = load_csv(SCORES_FILE)
    judgements = load_csv(JUDGEMENTS_FILE) if JUDGEMENTS_FILE.exists() else []
    ref_metrics = load_csv(METRICS_FILE)

    # Cast numeric fields
    for row in scores:
        for field in ["n_words", "density", "cv", "opener_entropy",
                      "func_word_ratio", "n_findings", "low_conc_paras"]:
            try:
                row[field] = float(row[field])
            except (ValueError, KeyError):
                row[field] = 0.0

    # Human reference densities
    human_densities = [float(r["density"]) for r in ref_metrics if r.get("label") == "human"]
    print(f"[analyze] Human reference rows: {len(human_densities)}")

    # -----------------------------------------------------------------------
    # CATCH section
    # -----------------------------------------------------------------------
    baseline_rows = [r for r in scores if r["condition"] == "baseline"]

    # Per-model baseline stats
    model_stats: dict[str, dict] = defaultdict(lambda: {"densities": [], "cvs": [], "label": "", "lab": "", "tier": ""})
    for row in baseline_rows:
        m = row["model"]
        model_stats[m]["densities"].append(row["density"])
        model_stats[m]["cvs"].append(row["cv"])

    # Load label/tier info from models.json
    models_file = HERE / "models.json"
    models_list = json.loads(models_file.read_text())
    model_info = {m["id"]: m for m in models_list}
    for m_id, info in model_info.items():
        if m_id in model_stats:
            model_stats[m_id]["label"] = info.get("label", m_id)
            model_stats[m_id]["lab"] = info.get("lab", "")
            model_stats[m_id]["tier"] = info.get("tier", "")

    # Compute mean density, cv per model + AUC
    model_summary = []
    for m_id, s in model_stats.items():
        if not s["densities"]:
            continue
        mean_density = statistics.mean(s["densities"])
        mean_cv = statistics.mean(s["cvs"])
        auc = auc_mann_whitney(s["densities"], human_densities)
        model_summary.append({
            "model_id": m_id,
            "label": s["label"] or m_id,
            "lab": s["lab"],
            "tier": s["tier"],
            "mean_density": mean_density,
            "mean_cv": mean_cv,
            "auc": auc,
            "n": len(s["densities"]),
        })
    model_summary.sort(key=lambda x: x["mean_density"], reverse=True)

    # By tier
    tier_groups: dict[str, list[float]] = defaultdict(list)
    for row in baseline_rows:
        tier = model_info.get(row["model"], {}).get("tier", "unknown")
        tier_groups[tier].append(row["density"])

    # By register
    register_groups: dict[str, list[float]] = defaultdict(list)
    for row in baseline_rows:
        register_groups[row["register"]].append(row["density"])

    # -----------------------------------------------------------------------
    # IMPROVE section
    # -----------------------------------------------------------------------
    INTERVENTIONS = ["human_system", "fewshot", "deslop"]

    # Index baseline scores by (model, prompt_id)
    baseline_index: dict[tuple, float] = {}
    baseline_cv_index: dict[tuple, float] = {}
    for row in baseline_rows:
        key = (row["model"], row["prompt_id"])
        baseline_index[key] = row["density"]
        baseline_cv_index[key] = row["cv"]

    improve_stats: dict[str, dict] = {}
    for interv in INTERVENTIONS:
        interv_rows = [r for r in scores if r["condition"] == interv]
        density_diffs = []
        cv_diffs = []
        for row in interv_rows:
            key = (row["model"], row["prompt_id"])
            if key in baseline_index:
                density_diffs.append(row["density"] - baseline_index[key])
                cv_diffs.append(row["cv"] - baseline_cv_index[key])

        W_d, p_d = wilcoxon_p(density_diffs) if len(density_diffs) >= 4 else (float("nan"), float("nan"))
        W_cv, p_cv = wilcoxon_p(cv_diffs) if len(cv_diffs) >= 4 else (float("nan"), float("nan"))

        mean_dd = statistics.mean(density_diffs) if density_diffs else float("nan")
        mean_dcv = statistics.mean(cv_diffs) if cv_diffs else float("nan")

        judge_stats = judge_win_rate(judgements, interv)

        improve_stats[interv] = {
            "n_pairs": len(density_diffs),
            "mean_delta_density": mean_dd,
            "mean_delta_cv": mean_dcv,
            "wilcoxon_W_density": W_d,
            "wilcoxon_p_density": p_d,
            "wilcoxon_W_cv": W_cv,
            "wilcoxon_p_cv": p_cv,
            "judge_win_rate": judge_stats["win_rate"],
            "judge_ci_lo": judge_stats["ci_lo"],
            "judge_ci_hi": judge_stats["ci_hi"],
            "judge_n": judge_stats["n"],
        }

    # Goodharting divergence check
    # Flag where intervention lowers density (negative delta_density) but judge doesn't prefer it (win_rate < 0.5)
    divergence_flags = []
    for interv, s in improve_stats.items():
        dd = s["mean_delta_density"]
        wr = s["judge_win_rate"]
        if not math.isnan(dd) and not math.isnan(wr):
            lowers_density = dd < 0
            judge_prefers = wr > 0.5
            if lowers_density and not judge_prefers:
                divergence_flags.append(
                    f"**{interv}**: lowers density (Δ={dd:.3f}) but judge win-rate={wr:.2f} < 0.5 → possible Goodharting"
                )
            elif not lowers_density and judge_prefers:
                divergence_flags.append(
                    f"**{interv}**: raises density (Δ={dd:.3f}) but judge prefers it (win-rate={wr:.2f}) → PLAINLY and judge disagree"
                )

    # -----------------------------------------------------------------------
    # Write results markdown
    # -----------------------------------------------------------------------
    lines = []
    lines.append("# Experiment Results: Catching and Reducing AI-Feel\n")
    lines.append(f"*Generated by analyze.py*\n")

    lines.append("## 1. CATCH — Baseline AI-Feel by Model\n")
    lines.append("Models ranked by mean plainly density score (higher = more AI tells).\n")
    lines.append("| Rank | Model | Lab | Tier | Mean Density | Mean CV | AUC vs Human | N |")
    lines.append("|------|-------|-----|------|-------------|---------|-------------|---|")
    for i, m in enumerate(model_summary, 1):
        lines.append(
            f"| {i} | {m['label']} | {m['lab']} | {m['tier']} "
            f"| {fmt(m['mean_density'])} | {fmt(m['mean_cv'])} "
            f"| {fmt(m['auc'])} | {m['n']} |"
        )

    lines.append("\n### By Tier\n")
    lines.append("| Tier | Mean Density | N |")
    lines.append("|------|-------------|---|")
    for tier, vals in sorted(tier_groups.items()):
        lines.append(f"| {tier} | {fmt(statistics.mean(vals) if vals else float('nan'))} | {len(vals)} |")

    lines.append("\n### By Register\n")
    lines.append("| Register | Mean Density | N |")
    lines.append("|----------|-------------|---|")
    for reg, vals in sorted(register_groups.items()):
        lines.append(f"| {reg} | {fmt(statistics.mean(vals) if vals else float('nan'))} | {len(vals)} |")

    lines.append("\n### Human Reference Distribution\n")
    if human_densities:
        lines.append(f"- N = {len(human_densities)}")
        lines.append(f"- Mean density = {fmt(statistics.mean(human_densities))}")
        lines.append(f"- Median density = {fmt(statistics.median(human_densities))}")
        lines.append(f"- Stdev = {fmt(statistics.stdev(human_densities) if len(human_densities) > 1 else float('nan'))}")
    else:
        lines.append("*No human reference data found.*")

    lines.append("\n## 2. IMPROVE — Intervention Effectiveness\n")
    lines.append(
        "Δdensity and Δcv are **paired** differences (intervention − baseline) per model×prompt. "
        "Negative Δdensity = fewer AI tells. Wilcoxon p < 0.05 indicates significant change.\n"
    )
    lines.append(
        "| Condition | N pairs | Δdensity (mean) | p(Wilcoxon) | Δcv (mean) | p(Wilcoxon) | "
        "Judge win-rate | 95% CI |"
    )
    lines.append(
        "|-----------|---------|----------------|-------------|-----------|-------------|"
        "--------------|--------|"
    )
    for interv in INTERVENTIONS:
        s = improve_stats[interv]
        ci = f"[{fmt(s['judge_ci_lo'], 2)}, {fmt(s['judge_ci_hi'], 2)}]"
        lines.append(
            f"| {interv} | {s['n_pairs']} "
            f"| {fmt(s['mean_delta_density'])} | {fmt(s['wilcoxon_p_density'])} "
            f"| {fmt(s['mean_delta_cv'])} | {fmt(s['wilcoxon_p_cv'])} "
            f"| {fmt(s['judge_win_rate'], 2)} ({s['judge_n']} pairs) | {ci} |"
        )

    lines.append("\n### PLAINLY vs Judge Divergence (Goodharting Check)\n")
    if divergence_flags:
        for flag in divergence_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("No divergence detected: PLAINLY and judge agree on direction for all interventions.")

    lines.append("\n## 3. Limitations\n")
    lines.append("""
- **LLM judge bias:** The judge model may have its own stylistic preferences that don't represent the full range of human readers. Its training data may overlap with or bias toward certain models.
- **Temperature variance:** Each text is generated at temperature 0.7, so repeated sampling would yield different outputs. The reported statistics reflect a single sample per model×prompt×condition.
- **Prompt set size:** 10 prompts is a small sample. Register effects and model rankings may not generalise.
- **OpenRouter model drift:** Model identifiers on OpenRouter may point to updated versions over time, meaning "GPT-4o" today may differ from GPT-4o at experiment time. The `raw_model` field in `.meta.json` records what was actually served.
- **Plainly density metric:** The `density` score counts specific pattern matches; it can be gamed by an intervention that removes those exact patterns without actually making the text read as more human.
- **Deslop circular dependency:** The fixer model (claude-sonnet-4.6) is also an LLM, and its edits may introduce new LLM tells even while removing the targeted ones.
- **Judge call count:** Approximately 3 interventions × 12 models × 10 prompts = 360 judge calls, which is a manageable but still limited sample.
""")

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text("\n".join(lines))
    print(f"[analyze] Written: {RESULTS_FILE}")

    # Print summary to stdout
    print("\n=== CATCH: Model ranking by mean density ===")
    for i, m in enumerate(model_summary[:5], 1):
        print(f"  {i}. {m['label']:30s}  density={m['mean_density']:.3f}  AUC={m['auc']:.3f}")

    print("\n=== IMPROVE: Judge win-rates ===")
    for interv in INTERVENTIONS:
        s = improve_stats[interv]
        print(f"  {interv:15s} win-rate={fmt(s['judge_win_rate'], 2)}  "
              f"Δdensity={fmt(s['mean_delta_density'])}  p={fmt(s['wilcoxon_p_density'])}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    main()
