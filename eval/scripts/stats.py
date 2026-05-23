#!/usr/bin/env python3
"""Statistical analysis of plainly's density score, per the methodology in eval/docs.

Stdlib only. Implements: AUC (= rank-sum U / n1n2), Cliff's delta (= 2*AUC-1),
Mann-Whitney U with tie-corrected normal approx + continuity correction, TPR at a
fixed 5% FPR (threshold calibrated on human data), and percentile bootstrap CIs.
Reports primary dataset comparison, per-domain stratification, a length-confound check,
modern blind-writer AI vs human, and per-model tiers.
"""
import csv
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

random.seed(1234)
CSV = Path(__file__).resolve().parents[2] / "eval" / "data" / "metrics.csv"
B = 4000  # bootstrap iterations


def load():
    rows = []
    with open(CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r["density"] = float(r["density"])
            r["n_words"] = int(r["n_words"])
            r["blind"] = r["source"].startswith("blind-")
            rows.append(r)
    return rows


def auc_delta(human, ai):
    """AUC = P(ai > human) with 0.5 for ties; Cliff's delta = 2*AUC-1. Higher score = more AI."""
    if not human or not ai:
        return None, None
    gt = eq = 0
    for a in ai:
        for h in human:
            if a > h:
                gt += 1
            elif a == h:
                eq += 1
    auc = (gt + 0.5 * eq) / (len(human) * len(ai))
    return auc, 2 * auc - 1


def mann_whitney_p(human, ai):
    """Two-sided p via tie-corrected normal approximation with continuity correction."""
    n1, n2 = len(human), len(ai)
    if n1 == 0 or n2 == 0:
        return None
    pooled = sorted([(v, "h") for v in human] + [(v, "a") for v in ai])
    # average ranks
    ranks = [0.0] * len(pooled)
    i = 0
    tie_term = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[k] = avg
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    R1 = sum(rk for rk, (_, lab) in zip(ranks, pooled) if lab == "h")
    U1 = R1 - n1 * (n1 + 1) / 2.0
    U = min(U1, n1 * n2 - U1)
    N = n1 + n2
    mu = n1 * n2 / 2.0
    var = (n1 * n2 / 12.0) * ((N + 1) - tie_term / (N * (N - 1)))
    if var <= 0:
        return 1.0
    z = (abs(U - mu) - 0.5) / math.sqrt(var)
    return 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))


def tpr_at_fpr(human, ai, fpr=0.05):
    """Calibrate threshold on human to the target FPR, report TPR (AI flagged) + threshold."""
    h = sorted(human)
    # smallest threshold s.t. fraction of humans strictly above it <= fpr
    idx = max(0, math.ceil((1 - fpr) * len(h)) - 1)
    thr = h[idx]
    # ensure FPR <= target: bump above ties at thr
    above = sum(1 for v in human if v > thr) / len(human)
    tpr = sum(1 for v in ai if v > thr) / len(ai)
    return thr, above, tpr


def boot_ci(func, human, ai, repeats=B):
    vals = []
    for _ in range(repeats):
        hb = [random.choice(human) for _ in human]
        ab = [random.choice(ai) for _ in ai]
        v = func(hb, ab)
        if v is not None:
            vals.append(v)
    vals.sort()
    lo = vals[int(0.025 * len(vals))]
    hi = vals[int(0.975 * len(vals)) - 1]
    return lo, hi


def summ(xs):
    if not xs:
        return "n=  0 mean=nan median=nan"
    return f"n={len(xs):>3} mean={statistics.mean(xs):.3f} median={statistics.median(xs):.3f}"


def main():
    rows = load()
    dn = lambda rs: [r["density"] for r in rs]
    H = [r for r in rows if r["label"] == "human"]
    AI_ds = [r for r in rows if r["label"] == "ai" and not r["blind"]]
    AI_blind = [r for r in rows if r["label"] == "ai" and r["blind"]]

    print("=" * 72)
    print("PRIMARY: dataset human vs dataset AI (matched era ~2022 GPT-3.5)  [density]")
    print("=" * 72)
    h, a = dn(H), dn(AI_ds)
    print("  human:", summ(h)); print("  ai   :", summ(a))
    auc, delta = auc_delta(h, a)
    p = mann_whitney_p(h, a)
    thr, fpr_real, tpr = tpr_at_fpr(h, a, 0.05)
    auc_lo, auc_hi = boot_ci(lambda x, y: auc_delta(x, y)[0], h, a)
    tpr_lo, tpr_hi = boot_ci(lambda x, y: tpr_at_fpr(x, y, 0.05)[2], h, a)
    print(f"  AUC = {auc:.3f}  (95% CI {auc_lo:.3f}-{auc_hi:.3f})   Cliff's delta = {delta:.3f}")
    print(f"  Mann-Whitney two-sided p = {p:.2e}")
    print(f"  threshold@5%FPR = {thr:.3f} (actual human FPR {fpr_real*100:.1f}%)  "
          f"TPR(AI flagged) = {tpr*100:.1f}%  (95% CI {tpr_lo*100:.0f}-{tpr_hi*100:.0f}%)")

    print("\n--- per-domain (dataset only): AUC, n_human/n_ai ---")
    for dom in sorted({r["domain"] for r in H + AI_ds}):
        hh = dn([r for r in H if r["domain"] == dom])
        aa = dn([r for r in AI_ds if r["domain"] == dom])
        if hh and aa:
            ac, _ = auc_delta(hh, aa)
            print(f"  {dom:<11} AUC={ac:.3f}  n={len(hh)}/{len(aa)}  "
                  f"meanH={statistics.mean(hh):.2f} meanAI={statistics.mean(aa):.2f}")

    print("\n--- length confound check: n_words, human vs dataset AI ---")
    hw = [r["n_words"] for r in H]; aw = [r["n_words"] for r in AI_ds]
    lac, _ = auc_delta(hw, aw); lp = mann_whitney_p(hw, aw)
    print(f"  words human mean={statistics.mean(hw):.0f}  AI mean={statistics.mean(aw):.0f}  "
          f"AUC(words)={lac:.3f}  p={lp:.2e}")
    print("  (AUC(words) near 0.5 => length is NOT driving the density separation)")

    print("\n" + "=" * 72)
    print("MODERN: blind-writer AI (Claude 2026) vs human  [density]")
    print("=" * 72)
    ab = dn(AI_blind)
    print("  human    :", summ(h)); print("  blind AI :", summ(ab))
    auc2, d2 = auc_delta(h, ab)
    p2 = mann_whitney_p(h, ab)
    _, _, tpr2 = tpr_at_fpr(h, ab, 0.05)
    print(f"  AUC = {auc2:.3f}   Cliff's delta = {d2:.3f}   MW p = {p2:.2e}")
    print(f"  TPR(modern AI flagged) at the 5%-FPR human threshold ({thr:.3f}) = {tpr2*100:.1f}%")
    print("  --> low TPR means modern frontier prose largely evades the tells (expected).")

    print("\n--- per-model tier (blind, 2026): density + burstiness ---")
    bym = defaultdict(list)
    for r in AI_blind:
        bym[r["source"]].append(r)
    for src in sorted(bym):
        ds = dn(bym[src])
        cvs = [float(r["cv"]) for r in bym[src] if r["cv"]]
        print(f"  {src:<18} {summ(ds)}  mean_cv={statistics.mean(cvs):.3f}")


if __name__ == "__main__":
    main()
