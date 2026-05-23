import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "on_write.py"

SLOPPY = ("In today's fast-paced world, this isn't just text — it's a paradigm, "
          "leveraging cutting-edge AI, underscoring our commitment, moreover.")
CLEAN = ("The build took forty minutes. Now it takes six. We cached the dependency "
         "layer and cut three steps. That was the whole change.")


def _run(path):
    inp = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(path)}})
    return subprocess.run([sys.executable, str(HOOK)], input=inp,
                          capture_output=True, text=True)


def test_sloppy_md_flags(tmp_path):
    f = tmp_path / "s.md"; f.write_text(SLOPPY)
    r = _run(f)
    assert r.returncode == 2
    assert "plainly:" in r.stderr


def test_clean_md_silent(tmp_path):
    f = tmp_path / "c.md"; f.write_text(CLEAN)
    r = _run(f)
    assert r.returncode == 0 and r.stderr == ""


def test_non_prose_silent(tmp_path):
    f = tmp_path / "c.py"; f.write_text("x = 1  # not prose")
    assert _run(f).returncode == 0


def test_disabled_via_config_silent(tmp_path):
    (tmp_path / ".plainly.toml").write_text("[hook]\nenabled = false\n")
    f = tmp_path / "s.md"; f.write_text(SLOPPY)
    assert _run(f).returncode == 0
