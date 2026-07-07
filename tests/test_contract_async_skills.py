"""contract tests for 3 async skills: speaker-classify / video-compose / videots.

验证 submit 走对的 URL、必带 multipart fields、必带 form fields,响应解析 request_id。
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))


def _load(module_name, script_path):
    spec = importlib.util.spec_from_file_location(module_name, str(script_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mock_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _tmp_audio(suffix=".wav"):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(b"0")
    f.close()
    return Path(f.name)


class TestSpeakerClassifyContract:
    @staticmethod
    def _mod():
        return _load(
            "classify",
            REPO_ROOT / "skills" / "speaker-classify-lychee" / "scripts" / "classify.py",
        )

    def test_submit_url_and_file(self):
        m = self._mod()
        audio = _tmp_audio()
        try:
            with patch("http_client._SESSION.post", return_value=_mock_response(200, {
                "code": 200, "info": "ok", "data": {"request_id": "req-cls-001", "task_name": "x", "audio_path": "p"}
            })) as mock_post:
                result = m.submit(file_path=audio, timeout=10.0)
            assert result["request_id"] == "req-cls-001"
            call = mock_post.call_args
            assert call.args[0] == "https://shanhaistudio.lycheeai.com.cn/openapi/open/speaker-classify/submit"
            assert "api_key" in call.kwargs["headers"]
            assert "file" in call.kwargs["files"]
        finally:
            audio.unlink()


class TestVideoComposeContract:
    @staticmethod
    def _mod():
        return _load(
            "compose",
            REPO_ROOT / "skills" / "video-compose-lychee" / "scripts" / "compose.py",
        )

    def test_submit_url_and_minimal_form(self):
        m = self._mod()
        video = _tmp_audio(".mp4")
        try:
            args = SimpleNamespace(
                video_file=video, audio_file=None, subtitle_file=None,
                target_language=None, subtitle_x=None, subtitle_y=None,
                subtitle_font_size=None, coordinate_width=None, coordinate_height=None,
                timeout=600.0,
            )
            with patch("http_client._SESSION.post", return_value=_mock_response(200, {
                "code": 200, "info": "ok", "data": {"task_id": "task-vc-001"}
            })) as mock_post:
                result = m.submit(args)
            assert result["task_id"] == "task-vc-001"
            call = mock_post.call_args
            assert call.args[0] == "https://shanhaistudio.lycheeai.com.cn/openapi/open/video-compose/tasks"
            # multipart 必传 video_file,不能传 form(没传 language/subtitle 时)
            assert "video_file" in call.kwargs["files"]
            assert call.kwargs.get("data") in (None, {})
        finally:
            video.unlink()

    def test_submit_with_subtitle_requires_target_language(self):
        m = self._mod()
        video = _tmp_audio(".mp4")
        sub = _tmp_audio(".srt")
        try:
            args = SimpleNamespace(
                video_file=video, audio_file=None, subtitle_file=sub,
                target_language=None,  # 必填,缺则 ValueError 或后端拒绝
                subtitle_x=None, subtitle_y=None, subtitle_font_size=None,
                coordinate_width=None, coordinate_height=None,
                timeout=600.0,
            )
            import pytest
            with pytest.raises((ValueError, Exception)) as excinfo:
                m.submit(args)
            assert "target-language" in str(excinfo.value) or "target_language" in str(excinfo.value)
        finally:
            video.unlink()
            sub.unlink()


class TestVideotsContract:
    @staticmethod
    def _mod():
        return _load(
            "translate",
            REPO_ROOT / "skills" / "videots-lychee" / "scripts" / "translate.py",
        )

    def test_submit_translate_url_and_form(self):
        m = self._mod()
        srt = _tmp_audio(".srt")
        try:
            args = SimpleNamespace(
                action="translate",
                file=srt, tos_path=None,
                file_original=None, file_translated=None,
                tos_path_original=None, tos_path_translated=None,
                target_language="en", user_prompt=None, mode=None,
                retranslation_items=None,
                timeout=600.0,
            )
            with patch("http_client._SESSION.post", return_value=_mock_response(200, {
                "code": 200, "info": "ok", "data": {"task_id": "task-vt-001"}
            })) as mock_post:
                result = m.submit(args)
            assert result["task_id"] == "task-vt-001"
            call = mock_post.call_args
            assert call.args[0] == "https://shanhaistudio.lycheeai.com.cn/openapi/open/videots/translate"
            # multipart 必带 file
            assert "file" in call.kwargs["files"]
            # form 必带 target_language
            data = call.kwargs.get("data") or {}
            assert data.get("target_language") == "en"
        finally:
            srt.unlink()
