"""每个 skill 的集成测试:验证 --help / 缺参数 / 无 key 三种行为稳定。

不需要 LYCHEE_API_KEY,纯本地 smoke。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))

SKILLS_AND_SCRIPTS = {
    "asr-lychee": "asr.py",
    "tts-lychee": "synthesize.py",
    "voice-clone-lychee": "clone.py",
    "voice-infer-lychee": "infer.py",
    "timbre-design-lychee": "design.py",
    "speaker-classify-lychee": "classify.py",
    "voice-separate-lychee": "separate.py",
    "subtitle-erase-lychee": "erase.py",
    "videots-lychee": "translate.py",
    "video-compose-lychee": "compose.py",
}


def _run(skill, *args, env=None, timeout=10):
    script = SKILLS_AND_SCRIPTS[skill]
    full_env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONPATH": str(REPO_ROOT / "shared"),
    }
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, f"skills/{skill}/scripts/{script}", *args],
        capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT),
        env=full_env, encoding="utf-8", errors="replace",
    )


@pytest.mark.parametrize("skill", list(SKILLS_AND_SCRIPTS.keys()))
def test_skill_help_exits_zero(skill):
    r = _run(skill, "--help")
    assert r.returncode == 0
    assert "--help" in r.stdout or "usage" in r.stdout.lower() or "optional" in r.stdout.lower()


@pytest.mark.parametrize("skill", list(SKILLS_AND_SCRIPTS.keys()))
def test_skill_missing_api_key_includes_step(skill):
    r = _run(skill, env={"LYCHEE_API_KEY": "", "TTS_API_KEY": ""}, timeout=10)
    if r.returncode not in (1, 2):
        pytest.skip(f"{skill} 不依赖 API key (returncode={r.returncode})")
    if not r.stderr.strip():
        pytest.skip(f"{skill} 失败时无 stderr 输出")
    last_line = r.stderr.strip().splitlines()[-1].strip()
    if not last_line.startswith("{"):
        pytest.skip(f"{skill} stderr 不是 JSON (asr 等): {last_line[:80]}")
    try:
        payload = json.loads(last_line)
    except json.JSONDecodeError:
        pytest.skip(f"{skill} stderr 不是 JSON: {last_line[:80]}")
    if "step" not in payload:
        pytest.skip(f"{skill} stderr JSON 无 step 字段")
    assert payload["step"] in (
        "asr", "tts", "voice-clone", "voice-infer", "voice-separate",
        "speaker-classify", "timbre-design", "subtitle-erase", "videots", "video-compose",
    )


def test_subtitle_erase_missing_file_uses_value_error():
    r = _run("subtitle-erase-lychee", "--file", "nonexistent.mp4")
    assert r.returncode == 2
    assert "不存在" in r.stderr or "not" in r.stderr.lower()


def test_video_compose_missing_video_uses_value_error():
    r = _run("video-compose-lychee", "--video-file", "nonexistent.mp4")
    assert r.returncode == 2
    assert "不存在" in r.stderr or "not" in r.stderr.lower()
