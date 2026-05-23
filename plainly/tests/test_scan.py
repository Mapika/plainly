from plainly.scan import scan
from plainly.config import load_config


def test_scan_emits_schema():
    cfg = load_config(None)
    text = "It's not just a tool, it's a movement. We leverage synergy, underscoring our impact."
    result = scan(text, cfg)
    assert set(result) >= {"findings", "metrics", "density", "schema_version"}
    assert isinstance(result["findings"], list)
    assert "burstiness" in result["metrics"]
    assert "concreteness" in result["metrics"]


def test_scan_exposes_word_count():
    cfg = load_config(None)
    result = scan("The cat sat on the warm mat.", cfg)
    assert result["metrics"]["word_count"] == 7


def test_em_dash_off_by_default_but_toggleable():
    text = "A sentence — with a dash. Another one here, which is fine."
    off = load_config(None)  # rules.em_dash defaults to False
    assert all(f.get("id") != "em-dash" for f in scan(text, off)["findings"])
    on = load_config(None)
    on["rules"]["em_dash"] = True
    assert any(f.get("id") == "em-dash" for f in scan(text, on)["findings"])


def test_allowlist_drops_lexical_hit():
    cfg = load_config(None)
    cfg["allow"]["terms"] = ["leverage"]
    result = scan("We leverage things.", cfg)
    assert all(f.get("term") != "leverage" for f in result["findings"])


def test_density_rises_with_clustered_tells():
    cfg = load_config(None)
    clean = scan("The cat sat. The dog ran. Birds flew home.", cfg)["density"]
    sloppy = scan(
        "It's not just X, it's Y, underscoring synergy. Moreover, we leverage robust tapestry.",
        cfg,
    )["density"]
    assert sloppy > clean
