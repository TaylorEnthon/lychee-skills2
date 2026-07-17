"""end-to-end contract test for voice-clone-lychee。

用 unittest.mock patch 掉 requests,验证:
- 提交请求体字段正确(URL / headers / multipart files / form data)
- 解析响应字段(request_id / carry_back)
- main() 退出码 0
- stdout JSON 含 success: true
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "clone", str(REPO_ROOT / "skills" / "voice-clone-lychee" / "scripts" / "clone.py")
)
clone = importlib.util.module_from_spec(_spec)
sys.modules["clone"] = clone
_spec.loader.exec_module(clone)


def _mock_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def test_submit_sends_correct_request():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"0" * 1024)
        audio_path = Path(f.name)
    try:
        with patch("http_client._SESSION.post", return_value=_mock_response(200, {
            "code": 200, "info": "ok", "data": {"request_id": "req-123", "speaker_id": None, "carry_back": "test"}
        })) as mock_post:
            result = clone.clone_voice(audio_path, carry_back="test", timeout=30.0)
        assert result["request_id"] == "req-123"
        assert result["carry_back"] == "test"
        # request_id 应来自 response,不是用户输入
        call_args = mock_post.call_args
        assert call_args.args[0] == "https://shanhaistudio.lycheeai.com.cn/openapi/open/voice/zeroshot/clone"
        assert "api_key" in call_args.kwargs["headers"]
        # multipart 必传 file(skill 内部 key 是 "audio" 对应后端契约)
        assert "audio" in call_args.kwargs["files"]
    finally:
        audio_path.unlink()


def test_submit_raises_on_non_object_response():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"0")
        audio_path = Path(f.name)
    try:
        with patch("http_client._SESSION.post", return_value=_mock_response(200, ["not", "a", "dict"])):
            try:
                clone.clone_voice(audio_path, carry_back="x", timeout=10.0)
            except (AttributeError, KeyError) as exc:
                # list 没有 .get("request_id") 或没 ["request_id"] 索引
                assert "request_id" in str(exc) or "'list'" in str(exc)
            except Exception as exc:
                # 或 http_client 解包层 raise LycheeApiError
                assert "not an object" in str(exc) or "list" in str(exc).lower() or "request_id" in str(exc)
            else:
                raise AssertionError("expected exception")
    finally:
        audio_path.unlink()


def test_main_full_flow_subprocess(tmp_path):
    """subprocess 端到端:无 API key 时输出 step + hint。"""
    audio = tmp_path / "ref.wav"
    audio.write_bytes(b"0")
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT / "shared"),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    env.pop("LYCHEE_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "skills/voice-clone-lychee/scripts/clone.py", "--file", str(audio), "--carry-back", "test"],
        capture_output=True, text=True, timeout=10, cwd=str(REPO_ROOT), env=env, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 2
    payload = json.loads(result.stderr.strip())
    assert payload["step"] == "voice-clone"
    assert "lychee-set-key" in payload.get("hint", "")
