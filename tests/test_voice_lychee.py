"""voice-lychee skill 的结构 smoke 测试。"""

from pathlib import Path
import os
import subprocess
import sys

import pytest

from helpers import assert_doctor_warns_without_api_key, assert_install_ps1_validates_source


SKILL_DIR = Path(__file__).resolve().parents[1] / "skills" / "voice-lychee"
REQUIRED_FILES = [
    "SKILL.md",
    "install.sh",
    "install.ps1",
    "doctor.sh",
    "doctor.ps1",
    "scripts/synthesize.py",
    "scripts/list_voices.py",
    "scripts/list_tasks.py",
    "references/mode-decision-tree.md",
    "references/error-codes.md",
    "references/mention-rules.md",
    "data/voices-cache.example.json",
]


@pytest.fixture
def skill_name():
    return "voice-lychee"


def test_required_files_exist():
    missing = [name for name in REQUIRED_FILES if not (SKILL_DIR / name).is_file()]
    assert not missing, "missing voice-lychee files: {}".format(", ".join(missing))


def test_skill_frontmatter_and_triggers():
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---\nname: voice-lychee\n")
    assert "触发：" in content
    assert "AI 配音" in content
    assert "voice generation" in content


def test_scripts_expose_help():
    for script in ("synthesize.py", "list_voices.py", "list_tasks.py"):
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / script), "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
            timeout=10,
        )
        assert result.returncode == 0, result.stderr


def test_doctor_runs_without_api_key(skill_dir, tmp_workspace_path, monkeypatch):
    assert_doctor_warns_without_api_key(skill_dir, tmp_workspace_path, monkeypatch)


def test_doctor_falls_back_when_python3_is_broken(skill_dir, tmp_workspace_path):
    bin_dir = tmp_workspace_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    python_path = str(Path(sys.executable)).replace("\\", "/")
    if len(python_path) > 2 and python_path[1] == ":":
        python_path = "/{}/{}".format(python_path[0].lower(), python_path[3:])
    (bin_dir / "python").write_text('#!/usr/bin/env bash\nexec "{}" "$@"\n'.format(python_path), encoding="utf-8")
    (bin_dir / "python3").chmod(0o755)
    (bin_dir / "python").chmod(0o755)
    bin_path = str(bin_dir).replace("\\", "/")
    if len(bin_path) > 2 and bin_path[1] == ":":
        bin_path = "/{}/{}".format(bin_path[0].lower(), bin_path[3:])
    result = subprocess.run(
        ["bash", str(skill_dir / "doctor.sh")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={"PATH": bin_path + ":/usr/bin:/bin", "HOME": str(tmp_workspace_path)},
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_install_ps1_validates_source(skill_dir):
    assert_install_ps1_validates_source(skill_dir)
