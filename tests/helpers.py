"""Shared smoke-test helpers for lychee skills."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "shared"


def assert_required_files(skill_dir, required_files):
    for file_name in required_files:
        assert (skill_dir / file_name).is_file(), f"missing {file_name}"


def assert_skill_frontmatter(skill_dir, expected_name):
    content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---\n")
    end = content.find("\n---", 4)
    assert end > 0, "missing closing frontmatter marker"
    frontmatter = content[4:end]
    fields = {}
    for line in frontmatter.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    assert fields.get("name") == expected_name
    assert "description" in fields


def assert_script_help(skill_dir, script_name, expected_flags):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SHARED_DIR)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(skill_dir / "scripts" / script_name), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    for flag in expected_flags:
        assert flag in result.stdout


def _bash_path(path):
    text = str(path)
    if len(text) >= 3 and text[1:3] == ":\\":
        return "/" + text[0].lower() + "/" + text[3:].replace("\\", "/")
    return text.replace("\\", "/")


def assert_doctor_warns_without_api_key(skill_dir, tmp_path, monkeypatch):
    """Run doctor.sh without a real API key or network access."""
    monkeypatch.delenv("LYCHEE_API_KEY", raising=False)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    python_sh = bin_dir / "python3"
    python_sh.write_text(
        "#!/usr/bin/env bash\nexec \"{}\" \"$@\"\n".format(_bash_path(sys.executable)),
        encoding="utf-8",
    )
    curl_sh = bin_dir / "curl"
    curl_sh.write_text(
        "#!/usr/bin/env bash\nprintf '{\"status\":\"ok\"}'\n",
        encoding="utf-8",
    )
    python_sh.chmod(0o755)
    curl_sh.chmod(0o755)

    env = {
        "PATH": "{}:/usr/bin:/bin".format(_bash_path(bin_dir)),
        "HOME": _bash_path(skill_dir.parent),
        "PYTHONPATH": str(SHARED_DIR),
        "PYTHONIOENCODING": "utf-8",
    }
    result = subprocess.run(
        ["bash", str(skill_dir / "doctor.sh")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "WARN" in result.stdout


def assert_install_ps1_validates_source(skill_dir):
    content = (skill_dir / "install.ps1").read_text(encoding="utf-8")
    assert "Test-Path" in content or "missing" in content.lower()
