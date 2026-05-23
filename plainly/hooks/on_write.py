#!/usr/bin/env python3
"""PostToolUse hook: after Claude writes/edits a prose file, flag it if it reads AI-generated.

Reads the hook JSON on stdin, runs the plainly engine on the edited file, and — only when the
style-smell density is high — feeds an actionable message back to Claude (exit 2) so it can
offer to deslop the file. Silent (exit 0) for non-prose, clean prose, errors, or when disabled
via `[hook] enabled = false` in .plainly.toml. Never blocks the write (the tool already ran).
"""
import json
import os
import sys

PROSE_EXT = (".md", ".markdown", ".txt", ".rst")
SKIP = ("/node_modules/", "/.git/", "/dist/", "/build/", "/vendor/", "/.venv/", "/__pycache__/")
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))


def _find_config(start):
    cur = os.path.abspath(start)
    if os.path.isfile(cur):
        cur = os.path.dirname(cur)
    while True:
        cand = os.path.join(cur, ".plainly.toml")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    path = (data.get("tool_input") or {}).get("file_path") or ""
    if not path or not path.lower().endswith(PROSE_EXT):
        return 0
    norm = "/" + path.replace("\\", "/").strip("/") + "/"
    if any(s in norm for s in SKIP) or not os.path.isfile(path):
        return 0
    try:
        from plainly.config import load_config
        from plainly.scan import scan
        cfg = load_config(_find_config(path))
        hook_cfg = cfg.get("hook", {})
        if not hook_cfg.get("enabled", True):
            return 0
        threshold = float(hook_cfg.get("density", 6))
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        result = scan(text, cfg)
        density = result["density"]
    except Exception:
        return 0  # never break the user's session
    if density <= threshold:
        return 0
    n = len(result["findings"])
    sys.stderr.write(
        f"plainly: '{os.path.basename(path)}' reads AI-generated "
        f"(style-smell density {density:.1f}, {n} flagged span(s); threshold {threshold:.0f}). "
        f"Offer to clean it with the deslopper agent, or run /plainly:check {path} for a report.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
