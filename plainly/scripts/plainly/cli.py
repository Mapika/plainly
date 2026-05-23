"""Command-line entry: scan a file, stdin, or git-diff hunks; emit JSON; gate via exit code."""
import argparse
import json
import os
import subprocess
import sys

from .compare import compare
from .config import load_config
from .scan import scan


def _find_config():
    cur = os.getcwd()
    while True:
        cand = os.path.join(cur, ".plainly.toml")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def _changed_prose_files():
    """Files changed vs HEAD with prose extensions."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"], text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    exts = (".md", ".markdown", ".txt", ".rst")
    return [p for p in out.splitlines() if p.lower().endswith(exts) and os.path.exists(p)]


def _fmt_scorecard(result):
    """Render a compare() result as a compact human-readable scorecard."""
    d = result["deltas"]
    lines = [f"verdict: {result['verdict'].upper()}", ""]
    rows = [
        ("density", d["density"]),
        ("tell weight", d["weight"]),
        ("findings", d["findings"]),
        ("burstiness cv", d["cv"]),
        ("low-concreteness paras", d["low_conc"]),
        ("word count", d["words"]),
    ]
    for label, val in rows:
        before, after = val["before"], val["after"]
        if "delta" in val:
            lines.append(f"  {label:24s} {before} -> {after}  ({val['delta']:+g})")
        else:  # cv may be None on short texts
            lines.append(f"  {label:24s} {before} -> {after}")
    if result["removed_ids"]:
        lines.append(f"  tells removed: {', '.join(result['removed_ids'])}")
    if result["added_ids"]:
        lines.append(f"  NEW tells introduced: {', '.join(result['added_ids'])}")
    return "\n".join(lines)


def _compare_mode(ap, args, cfg):
    before_path, after_path = args.compare
    try:
        with open(before_path, encoding="utf-8") as fh:
            before = json.load(fh)
        with open(after_path, encoding="utf-8") as fh:
            after = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        ap.error(str(e))
    result = compare(before, after, cfg["deslop"]["burstiness_tolerance"])
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_fmt_scorecard(result))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plainly", description="Detect prose style smells.")
    ap.add_argument("path", nargs="?", help="file path, or '-' for stdin")
    ap.add_argument("--diff", action="store_true", help="scan only prose changed vs HEAD")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--config", help="path to .plainly.toml")
    ap.add_argument("--fail-over", type=float, default=None,
                    help="exit 1 if any scanned doc density exceeds this")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                    help="diff two scan-result JSON files into a before->after scorecard")
    args = ap.parse_args(argv)

    cfg = load_config(args.config or _find_config())

    if args.compare:
        return _compare_mode(ap, args, cfg)

    targets = []  # list of (name, text)
    if args.diff:
        for p in _changed_prose_files():
            with open(p, encoding="utf-8") as fh:
                targets.append((p, fh.read()))
    elif args.path == "-" or (args.path is None and not sys.stdin.isatty()):
        targets.append(("<stdin>", sys.stdin.read()))
    elif args.path:
        try:
            with open(args.path, encoding="utf-8") as fh:
                targets.append((args.path, fh.read()))
        except OSError as e:
            ap.error(str(e))
    else:
        ap.error("provide a path, '-', or --diff")

    results = {name: scan(text, cfg) for name, text in targets}

    if args.json:
        payload = results[next(iter(results))] if len(results) == 1 else results
        print(json.dumps(payload, indent=2))

    if args.fail_over is not None:
        worst = max((r["density"] for r in results.values()), default=0.0)
        return 1 if worst > args.fail_over else 0
    return 0
