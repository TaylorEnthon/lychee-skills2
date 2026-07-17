"""lychee OpenAPI 鉴权配置。"""

import os

API_KEY_HEADER = "api_key"


class MissingApiKeyError(Exception):
    """未配置 lychee API key。"""


def get_api_key() -> str:
    """从环境变量 LYCHEE_API_KEY 读取鉴权 key。"""
    api_key = os.environ.get("LYCHEE_API_KEY")
    if not api_key:
        raise MissingApiKeyError(
            "未设置 LYCHEE_API_KEY。运行 /lychee-set-key 配置。"
        )
    return api_key
