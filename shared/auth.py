"""lychee OpenAPI 鉴权配置。"""

import os

API_KEY_HEADER = "api_key"


class MissingApiKeyError(Exception):
    """未配置 lychee API key。"""


def get_api_key() -> str:
    """优先读取 LYCHEE_API_KEY，并兼容旧的 TTS_API_KEY。"""
    api_key = os.environ.get("LYCHEE_API_KEY") or os.environ.get("TTS_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "未设置 LYCHEE_API_KEY（兼容旧 TTS_API_KEY）。"
            "运行 /lychee-set-key 配置。"
        )
    return api_key
