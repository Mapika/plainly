from plainly.config import load_config, DEFAULTS


def test_defaults_present():
    cfg = load_config(None)
    assert cfg["severity"]["critical"] == DEFAULTS["severity"]["critical"]
    assert cfg["rules"]["em_dash"] is False


def test_user_override_merges(tmp_path):
    p = tmp_path / ".plainly.toml"
    p.write_text("[rules]\nem_dash = true\n[allow]\nterms = ['Tapestry']\n")
    cfg = load_config(str(p))
    assert cfg["rules"]["em_dash"] is True
    assert "Tapestry" in cfg["allow"]["terms"]
    # Untouched keys keep defaults.
    assert cfg["severity"]["critical"] == DEFAULTS["severity"]["critical"]
