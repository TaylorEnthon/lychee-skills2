"""voice-lychee 合成脚本的本地契约测试。"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "voice-lychee" / "scripts" / "synthesize.py"


def load_module():
    assert SCRIPT.is_file(), "synthesize.py is missing"
    spec = importlib.util.spec_from_file_location("voice_lychee_synthesize", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        ([], "text"),
        (["--voice-ids", "1"], "voices"),
        (["--audio-urls", "https://example.com/ref.wav"], "audio_url"),
    ],
)
def test_json_modes_send_expected_reference_type(monkeypatch, tmp_path, extra, expected):
    module = load_module()
    output = tmp_path / "out.wav"
    post_json = MagicMock(return_value={"audio_url": "https://example.com/out.wav", "duration_ms": 1200})
    monkeypatch.setattr(module, "post_json", post_json)
    response = MagicMock(content=b"audio")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    code = module.main(["--text", "你好", "--output", str(output), *extra])

    assert code == 0
    assert post_json.call_args.kwargs["body"]["reference_type"] == expected
    assert output.read_bytes() == b"audio"


def test_image_mode_uses_multipart(monkeypatch, tmp_path):
    module = load_module()
    image = tmp_path / "face.png"
    image.write_bytes(b"png")
    output = tmp_path / "out.mp3"
    post_multipart = MagicMock(return_value={"audio_url": "https://example.com/out.mp3", "duration_ms": 8})
    monkeypatch.setattr(module, "post_multipart", post_multipart)
    response = MagicMock(content=b"mp3")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    assert module.main(["--text", "你好", "--image", str(image), "--format", "mp3", "--output", str(output)]) == 0
    assert post_multipart.call_args.kwargs["data"]["reference_type"] == "image"
    assert "image" in post_multipart.call_args.kwargs["files"]


def test_duration_response_is_exposed_as_duration_ms(monkeypatch, tmp_path, capsys):
    module = load_module()
    output = tmp_path / "out.wav"
    monkeypatch.setattr(module, "post_json", MagicMock(return_value={
        "audio_url": "https://example.com/out.wav",
        "duration": 1200,
    }))
    response = MagicMock(content=b"audio")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    assert module.main(["--text", "你好", "--output", str(output)]) == 0

    assert json.loads(capsys.readouterr().out)["duration_ms"] == 1200


def test_text_mode_rejects_voice_mention(capsys):
    module = load_module()
    assert module.main(["--text", "{{voice:1}}你好"]) == 2
    payload = json.loads(capsys.readouterr().err)
    assert payload["step"] == "voice-lychee"
    assert "mention" in payload["error"]


def test_missing_api_key_returns_two(tmp_path):
    env = {**os.environ, "LYCHEE_API_KEY": "", "TTS_API_KEY": "", "PYTHONUTF8": "1"}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "test", "--output", str(tmp_path / "out.wav")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    assert result.returncode == 2
    assert json.loads(result.stderr)["step"] == "voice-lychee"
