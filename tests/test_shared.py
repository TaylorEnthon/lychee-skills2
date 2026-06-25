import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


def test_auth_module_imports():
    from auth import API_KEY_HEADER, MissingApiKeyError, get_api_key

    assert API_KEY_HEADER == "api_key"
    assert callable(get_api_key)
    assert issubclass(MissingApiKeyError, Exception)


def test_auth_missing_key_raises():
    saved_lychee = os.environ.pop("LYCHEE_API_KEY", None)
    saved_tts = os.environ.pop("TTS_API_KEY", None)
    try:
        from auth import MissingApiKeyError, get_api_key

        with pytest.raises(MissingApiKeyError):
            get_api_key()
    finally:
        if saved_lychee:
            os.environ["LYCHEE_API_KEY"] = saved_lychee
        if saved_tts:
            os.environ["TTS_API_KEY"] = saved_tts


def test_http_client_module_imports():
    from http_client import (
        BASE_URL,
        LycheeApiError,
        get_json,
        poll_status,
        post_json,
        post_multipart,
    )

    assert BASE_URL == "https://shanhaistudio.lycheeai.com.cn/openapi"
    assert issubclass(LycheeApiError, Exception)
    assert callable(post_multipart)
    assert callable(post_json)
    assert callable(get_json)
    assert callable(poll_status)


def test_ws_client_module_imports():
    from ws_client import TTS_WS_URL

    assert TTS_WS_URL == "wss://shanhaistudio.lycheeai.com.cn/openapi/tts/ws_binary/v2"
