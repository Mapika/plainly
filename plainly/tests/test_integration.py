from pathlib import Path
from plainly.scan import scan
from plainly.config import load_config

FIX = Path(__file__).parent / "fixtures"


def test_sloppy_fixture_flags_structural_tells():
    cfg = load_config(None)
    result = scan((FIX / "sloppy.md").read_text(), cfg)
    ids = {f.get("id") for f in result["findings"]}
    assert "antithesis-not-just" in ids
    assert "participle-tail" in ids
    assert "formulaic-intro" in ids
    assert result["density"] > 4


def test_clean_fixture_is_quiet():
    cfg = load_config(None)
    result = scan((FIX / "clean.md").read_text(), cfg)
    # No structural tells; em-dash present but suppressed by default.
    assert all(f.get("id") != "antithesis-not-just" for f in result["findings"])
    assert all(f.get("id") != "em-dash" for f in result["findings"])
    assert result["density"] < 4
    # Varied rhythm → healthy burstiness.
    assert result["metrics"]["burstiness"]["cv"] > 0.3
