"""lychee WebSocket 客户端占位。"""

from typing import Optional

TTS_WS_URL = "wss://shanhaistudio.lycheeai.com.cn/openapi/tts/ws_binary/v2"


def tts_synthesize(
    text: str,
    speaker_id: str,
    speed: float = 1.0,
    volume: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    raise NotImplementedError("tts-lychee skill 待实现；这一步只占位")
