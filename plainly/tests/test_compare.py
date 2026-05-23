from plainly.compare import compare


def _result(density, ids, cv, words, low_conc=0):
    """Minimal scan-result shape that compare() reads."""
    return {
        "density": density,
        "findings": [{"id": i, "weight": 1} for i in ids],
        "metrics": {
            "word_count": words,
            "burstiness": None if cv is None else {"cv": cv},
            "concreteness": {"low_paragraphs": [{}] * low_conc},
        },
    }


def test_density_drop_no_new_tells_is_improved():
    before = _result(5.0, ["antithesis", "booster"], cv=0.50, words=100)
    after = _result(2.0, ["booster"], cv=0.50, words=100)
    out = compare(before, after)
    assert out["verdict"] == "improved"
    assert out["removed_ids"] == ["antithesis"]
    assert out["added_ids"] == []


def test_new_tell_id_is_regressed():
    before = _result(5.0, ["antithesis"], cv=0.50, words=100)
    after = _result(2.0, ["antithesis", "tricolon"], cv=0.50, words=100)
    out = compare(before, after)
    assert out["verdict"] == "regressed"
    assert out["added_ids"] == ["tricolon"]


def test_density_rise_is_regressed():
    before = _result(2.0, ["booster"], cv=0.50, words=100)
    after = _result(5.0, ["booster"], cv=0.50, words=100)
    assert compare(before, after)["verdict"] == "regressed"


def test_flattened_burstiness_is_regressed():
    # after.cv 0.40 < before.cv 0.50 * 0.9 tolerance (0.45)
    before = _result(5.0, ["booster"], cv=0.50, words=100)
    after = _result(2.0, [], cv=0.40, words=100)
    assert compare(before, after)["verdict"] == "regressed"


def test_burstiness_within_tolerance_is_not_regressed():
    # after.cv 0.46 >= 0.45 tolerance floor → fine
    before = _result(5.0, ["booster"], cv=0.50, words=100)
    after = _result(2.0, [], cv=0.46, words=100)
    assert compare(before, after)["verdict"] == "improved"


def test_word_count_balloon_is_not_improved():
    # density dropped but text grew 20% (>15%): padding, not a real fix
    before = _result(5.0, ["booster"], cv=0.50, words=100)
    after = _result(2.0, [], cv=0.50, words=120)
    assert compare(before, after)["verdict"] == "neutral"


def test_unchanged_is_neutral():
    before = _result(3.0, ["booster"], cv=0.50, words=100)
    after = _result(3.0, ["booster"], cv=0.50, words=100)
    assert compare(before, after)["verdict"] == "neutral"


def test_missing_burstiness_does_not_block_improved():
    # short texts have cv=None; absence must not count as regression
    before = _result(5.0, ["antithesis"], cv=None, words=20)
    after = _result(1.0, [], cv=None, words=20)
    assert compare(before, after)["verdict"] == "improved"


def test_deltas_report_before_after_and_change():
    before = _result(5.0, ["a", "b"], cv=0.50, words=100, low_conc=2)
    after = _result(2.0, ["a"], cv=0.55, words=90, low_conc=1)
    d = compare(before, after)["deltas"]
    assert d["density"] == {"before": 5.0, "after": 2.0, "delta": -3.0}
    assert d["findings"] == {"before": 2, "after": 1, "delta": -1}
    assert d["words"] == {"before": 100, "after": 90, "delta": -10}
    assert d["low_conc"] == {"before": 2, "after": 1, "delta": -1}
    assert d["cv"]["before"] == 0.50 and d["cv"]["after"] == 0.55
