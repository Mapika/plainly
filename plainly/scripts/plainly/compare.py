"""Diff two scan results into a before->after scorecard and a verdict.

The deslopper edits prose, then asks: did this actually help? compare() answers
deterministically from two `scan()` results. Verdict precedence: any regression
signal wins, then improvement, else neutral.
"""

WORD_BALLOON = 1.15  # >15% growth at lower density usually means padding, not a fix


def _delta(before, after):
    return {"before": before, "after": after, "delta": round(after - before, 4)}


def _ids(result):
    return [f.get("id") for f in result.get("findings", [])]


def _cv(result):
    burst = result.get("metrics", {}).get("burstiness")
    return burst.get("cv") if burst else None


def _low_conc(result):
    conc = result.get("metrics", {}).get("concreteness", {})
    return len(conc.get("low_paragraphs", []))


def _words(result):
    return result.get("metrics", {}).get("word_count", 0)


def compare(before, after, burstiness_tolerance=0.9):
    before_ids, after_ids = _ids(before), _ids(after)
    before_set, after_set = set(before_ids), set(after_ids)
    removed_ids = sorted(before_set - after_set)
    added_ids = sorted(after_set - before_set)

    cv_b, cv_a = _cv(before), _cv(after)
    words_b, words_a = _words(before), _words(after)
    density_b, density_a = before["density"], after["density"]

    deltas = {
        "density": _delta(density_b, density_a),
        "weight": _delta(
            sum(f.get("weight", 0) for f in before.get("findings", [])),
            sum(f.get("weight", 0) for f in after.get("findings", [])),
        ),
        "findings": _delta(len(before_ids), len(after_ids)),
        "cv": {"before": cv_b, "after": cv_a},
        "low_conc": _delta(_low_conc(before), _low_conc(after)),
        "words": _delta(words_b, words_a),
    }

    # Regression: density rose, a new tell appeared, or rhythm flattened past tolerance.
    cv_flattened = (
        cv_b is not None and cv_a is not None and cv_a < cv_b * burstiness_tolerance
    )
    regressed = density_a > density_b or bool(added_ids) or cv_flattened

    # Improvement: density fell, nothing new, rhythm held, and text didn't balloon.
    cv_held = not (cv_b is not None and cv_a is not None) or cv_a >= cv_b * burstiness_tolerance
    not_ballooned = words_b == 0 or words_a <= words_b * WORD_BALLOON
    improved = density_a < density_b and not added_ids and cv_held and not_ballooned

    if regressed:
        verdict = "regressed"
    elif improved:
        verdict = "improved"
    else:
        verdict = "neutral"

    return {
        "deltas": deltas,
        "removed_ids": removed_ids,
        "added_ids": added_ids,
        "verdict": verdict,
    }
