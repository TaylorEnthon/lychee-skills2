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


def test_voice_names_partial_missing_falls_back_to_text(monkeypatch, tmp_path, capsys):
    """--voice-names 包含池里有的 + 池里没有的 → 应整体降级 text 模式 + 输出 fallback_reason"""
    module = load_module()
    output = tmp_path / "out.wav"
    # mock http_client 的 get_json（list_voices 调它）
    pool = [
        {"id": "1", "name": "Vivi", "description": "通用场景", "type": "builtin", "gender": "female", "lang_code": None},
        {"id": "2", "name": "小何", "description": "通用场景", "type": "builtin", "gender": "female", "lang_code": None},
    ]
    import sys
    http_client = sys.modules["http_client"]
    get_json_mock = MagicMock(return_value=pool)
    monkeypatch.setattr(http_client, "get_json", get_json_mock)
    post_json = MagicMock(return_value={"audio_url": "https://example.com/out.wav", "duration": 1500})
    monkeypatch.setattr(module, "post_json", post_json)
    response = MagicMock(content=b"audio")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    code = module.main([
        "--text", "测试", "--voice-names", "Vivi", "--voice-names", "温柔女声",
        "--output", str(output),
    ])
    assert code == 0

    captured = json.loads(capsys.readouterr().out)
    assert captured["mode"] == "text"
    assert "fallback_reason" in captured
    assert "温柔女声" in captured["fallback_reason"]
    body = post_json.call_args.kwargs["body"]
    assert body["reference_type"] == "text"
    assert "voice_ids" not in body


def test_voice_names_all_missing_falls_back_to_text(monkeypatch, tmp_path, capsys):
    """--voice-names 全部缺失 → 整体降级 text 模式"""
    module = load_module()
    output = tmp_path / "out.wav"
    pool = [
        {"id": "1", "name": "Vivi", "description": "通用场景", "type": "builtin", "gender": "female", "lang_code": None},
    ]
    import sys
    http_client = sys.modules["http_client"]
    get_json_mock = MagicMock(return_value=pool)
    monkeypatch.setattr(http_client, "get_json", get_json_mock)
    post_json = MagicMock(return_value={"audio_url": "https://example.com/out.wav", "duration": 1500})
    monkeypatch.setattr(module, "post_json", post_json)
    response = MagicMock(content=b"audio")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    code = module.main([
        "--text", "测试", "--voice-names", "温柔男声", "--voice-names", "未知音色",
        "--output", str(output),
    ])
    assert code == 0

    captured = json.loads(capsys.readouterr().out)
    assert captured["mode"] == "text"
    assert "温柔男声" in captured["fallback_reason"]
    assert "未知音色" in captured["fallback_reason"]


def test_voice_names_all_resolved_uses_voices_mode(monkeypatch, tmp_path, capsys):
    """--voice-names 全部命中 → 用 voices 模式 + 正确传 voice_ids"""
    module = load_module()
    output = tmp_path / "out.wav"
    pool = [
        {"id": "1", "name": "Vivi", "description": "通用场景", "type": "builtin", "gender": "female", "lang_code": None},
        {"id": "2", "name": "小何", "description": "通用场景", "type": "builtin", "gender": "female", "lang_code": None},
    ]
    import sys
    http_client = sys.modules["http_client"]
    get_json_mock = MagicMock(return_value=pool)
    monkeypatch.setattr(http_client, "get_json", get_json_mock)
    post_json = MagicMock(return_value={"audio_url": "https://example.com/out.wav", "duration": 1500})
    monkeypatch.setattr(module, "post_json", post_json)
    response = MagicMock(content=b"audio")
    response.raise_for_status.return_value = None
    monkeypatch.setattr(module.requests, "get", MagicMock(return_value=response))

    code = module.main([
        "--text", "测试", "--voice-names", "Vivi", "--voice-names", "小何",
        "--output", str(output),
    ])
    assert code == 0

    captured = json.loads(capsys.readouterr().out)
    assert captured["mode"] == "voices"
    assert "fallback_reason" not in captured
    body = post_json.call_args.kwargs["body"]
    assert body["reference_type"] == "voices"
    assert body["voice_ids"] == ["1", "2"]


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
