"""shared/errors.py 单测。"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))


def _run_skill(skill_name, *args):
    """跑 skill 脚本,返回 (returncode, stdout, stderr)。"""
    return subprocess.run(
        [sys.executable, f"skills/{skill_name}/scripts/{skill_name.replace('-lychee', '').replace('voice-clone', 'clone').replace('voice-infer', 'infer').replace('voice-separate', 'separate').replace('speaker-classify', 'classify').replace('subtitle-erase', 'erase').replace('video-compose', 'compose').replace('tts-', 'synthesize')}.py", *args],
        capture_output=True, text=True, timeout=30,
    )


def test_format_error_minimal():
    from shared.errors import format_error
    out = format_error(ValueError("boom"))
    assert out == {"success": False, "error": "boom"}


def test_format_error_with_step():
    from shared.errors import format_error
    out = format_error(ValueError("x"), step="submit")
    assert out == {"success": False, "error": "x", "step": "submit"}


def test_format_error_with_hint():
    from shared.errors import format_error
    out = format_error(ValueError("x"), step="submit", hint="check api key")
    assert out["hint"] == "check api key"


def test_format_error_no_hint_omits_field():
    from shared.errors import format_error
    out = format_error(RuntimeError("x"), step="poll")
    assert "hint" not in out


def test_skill_missing_api_key_includes_step_and_hint(tmp_path, monkeypatch):
    """无 LYCHEE_API_KEY 时,skill 应输出带 step 和 hint 的 JSON。"""
    monkeypatch.delenv("LYCHEE_API_KEY", raising=False)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    audio = tmp_path / "x.wav"
    audio.write_bytes(b"0")
    result = subprocess.run(
        [sys.executable, "skills/voice-clone-lychee/scripts/clone.py", "--file", str(audio), "--carry-back", "test"],
        capture_output=True, text=True, timeout=10, cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "shared"), "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    assert result.returncode == 2
    payload = json.loads(result.stderr.strip())
    assert payload["success"] is False
    assert payload["step"] == "voice-clone"
    assert "hint" in payload
    assert "API" in payload["hint"] or "lychee-set-key" in payload["hint"]
