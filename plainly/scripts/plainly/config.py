"""Load .plainly.toml (stdlib tomllib) and deep-merge over defaults."""
import copy
import os
import tomllib

DEFAULTS = {
    "severity": {"critical": 6, "moderate": 3},
    "rules": {"em_dash": False},
    "burstiness": {"min_cv": 0.35},
    "concreteness": {"min_mean": 2.6},
    "genre": {"default": "prose"},
    "allow": {"terms": []},
    "hook": {"enabled": True, "density": 6},
    "deslop": {"judge": True, "burstiness_tolerance": 0.9},
}


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path):
    """path=None or missing → defaults. Otherwise merge file over defaults."""
    if path and os.path.exists(path):
        with open(path, "rb") as fh:
            user = tomllib.load(fh)
        return _merge(DEFAULTS, user)
    return _merge(DEFAULTS, {})
