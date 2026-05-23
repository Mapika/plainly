import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESCAN = ROOT / "scripts" / "prescan.py"


def _run(args, **kw):
    return subprocess.run(
        [sys.executable, str(PRESCAN), *args],
        capture_output=True, text=True, **kw
    )


def test_cli_json_on_file(tmp_path):
    f = tmp_path / "draft.md"
    f.write_text("It's not just a tool, it's a movement. We leverage synergy.")
    res = _run([str(f), "--json"])
    data = json.loads(res.stdout)
    assert data["schema_version"] == "1"
    assert len(data["findings"]) >= 1


def test_cli_exit_code_gates_on_density(tmp_path):
    f = tmp_path / "bad.md"
    f.write_text(
        "It's not just X, it's Y, underscoring synergy. Moreover we leverage robust tapestry."
    )
    res = _run([str(f), "--json", "--fail-over", "0.1"])
    assert res.returncode == 1  # density exceeds threshold → gate fails

    clean = tmp_path / "ok.md"
    clean.write_text("The cat sat on the warm mat. Rain fell on the glass roof all night.")
    res2 = _run([str(clean), "--json", "--fail-over", "5"])
    assert res2.returncode == 0


def test_cli_reads_stdin():
    res = _run(["-", "--json"], input="We must leverage synergy.")
    data = json.loads(res.stdout)
    assert any(fd.get("term") == "leverage" for fd in data["findings"])


def _scan_result(density, ids, cv, words):
    return {
        "density": density,
        "findings": [{"id": i, "weight": 1} for i in ids],
        "metrics": {
            "word_count": words,
            "burstiness": {"cv": cv},
            "concreteness": {"low_paragraphs": []},
        },
    }


def test_cli_compare_json(tmp_path):
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(_scan_result(5.0, ["antithesis", "booster"], 0.50, 100)))
    after.write_text(json.dumps(_scan_result(2.0, ["booster"], 0.50, 100)))
    res = _run(["--compare", str(before), str(after), "--json"])
    data = json.loads(res.stdout)
    assert data["verdict"] == "improved"
    assert data["removed_ids"] == ["antithesis"]
    assert "deltas" in data


def test_cli_compare_human_prints_verdict(tmp_path):
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(_scan_result(5.0, ["antithesis"], 0.50, 100)))
    after.write_text(json.dumps(_scan_result(1.0, [], 0.52, 100)))
    res = _run(["--compare", str(before), str(after)])
    assert "improved" in res.stdout.lower()
