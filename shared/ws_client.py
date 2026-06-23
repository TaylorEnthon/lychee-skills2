"""lychee TTS WebSocket 客户端。"""

import json
import struct
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import websocket

from auth import API_KEY_HEADER, get_api_key
from http_client import LycheeApiError

TTS_WS_URL = "wss://shanhaistudio.lycheeai.com.cn/openapi/tts/ws_binary/v2"

PROTOCOL_VERSION = 0x1
DEFAULT_HEADER_SIZE = 0x1
FULL_CLIENT_REQUEST = 0x1
AUDIO_ONLY_RESPONSE = 0xB
ERROR_INFORMATION = 0xF
MSG_TYPE_FLAG_WITH_EVENT = 0x4
JSON_SERIALIZATION = 0x1
COMPRESSION_NO = 0x0

EVENT_START_CONNECTION = 1
EVENT_FINISH_CONNECTION = 2
EVENT_CONNECTION_STARTED = 50
EVENT_CONNECTION_FAILED = 51
EVENT_CONNECTION_FINISHED = 52
EVENT_START_SESSION = 100
EVENT_FINISH_SESSION = 102
EVENT_SESSION_STARTED = 150
EVENT_SESSION_FINISHED = 152
EVENT_SESSION_FAILED = 153
EVENT_TASK_REQUEST = 200
EVENT_TTS_RESPONSE = 352


def _int_to_bytes(value: int) -> bytes:
    return struct.pack(">I", value)


def _bytes_to_int(data: bytes) -> int:
    if len(data) != 4:
        raise ValueError("invalid four-byte integer")
    return struct.unpack(">I", data)[0]


def _make_header(message_type: int, serialization: int = JSON_SERIALIZATION) -> bytes:
    return bytes(
        [
            (PROTOCOL_VERSION << 4) | DEFAULT_HEADER_SIZE,
            (message_type << 4) | MSG_TYPE_FLAG_WITH_EVENT,
            (serialization << 4) | COMPRESSION_NO,
            0,
        ]
    )


def _make_optional(event: int, session_id: Optional[str] = None) -> bytes:
    optional = _int_to_bytes(event)
    if session_id is not None:
        session_bytes = session_id.encode("utf-8")
        optional += _int_to_bytes(len(session_bytes)) + session_bytes
    return optional


def _make_packet(
    event: int, payload: Dict[str, Any], session_id: Optional[str] = None
) -> bytes:
    payload_bytes = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return (
        _make_header(FULL_CLIENT_REQUEST)
        + _make_optional(event, session_id)
        + _int_to_bytes(len(payload_bytes))
        + payload_bytes
    )


def _read_sized_bytes(data: bytes, offset: int) -> Tuple[bytes, int]:
    if offset + 4 > len(data):
        raise ValueError("response is missing a size field")
    size = _bytes_to_int(data[offset : offset + 4])
    offset += 4
    end = offset + size
    if end > len(data):
        raise ValueError("response payload is truncated")
    return data[offset:end], end


def _parse_response(data: bytes) -> Dict[str, Any]:
    if len(data) < 4:
        raise ValueError("response too short")

    message_type = (data[1] >> 4) & 0x0F
    flags = data[1] & 0x0F
    offset = 4
    event = 0
    session_id = None
    payload = b""
    meta = None

    if message_type == ERROR_INFORMATION:
        if offset + 4 > len(data):
            raise ValueError("error response is missing an error code")
        error_code = _bytes_to_int(data[offset : offset + 4])
        offset += 4
        payload, _ = _read_sized_bytes(data, offset)
        return {
            "message_type": message_type,
            "event": event,
            "payload": payload,
            "error_code": error_code,
        }

    if flags == MSG_TYPE_FLAG_WITH_EVENT:
        if offset + 4 > len(data):
            raise ValueError("response is missing an event")
        event = _bytes_to_int(data[offset : offset + 4])
        offset += 4

    if event == EVENT_CONNECTION_STARTED:
        connection_id, offset = _read_sized_bytes(data, offset)
        if offset < len(data):
            payload, offset = _read_sized_bytes(data, offset)
        return {
            "message_type": message_type,
            "event": event,
            "connection_id": connection_id.decode("utf-8", "replace"),
            "payload": payload,
        }

    if event in (EVENT_SESSION_STARTED, EVENT_SESSION_FINISHED, EVENT_SESSION_FAILED):
        session_raw, offset = _read_sized_bytes(data, offset)
        session_id = session_raw.decode("utf-8", "replace")
        if offset < len(data):
            meta_raw, offset = _read_sized_bytes(data, offset)
            meta = meta_raw.decode("utf-8", "replace")
        return {
            "message_type": message_type,
            "event": event,
            "session_id": session_id,
            "meta": meta,
        }

    if event:
        if offset + 4 <= len(data):
            possible_size = _bytes_to_int(data[offset : offset + 4])
            if offset + 4 + possible_size <= len(data):
                session_raw, offset = _read_sized_bytes(data, offset)
                session_id = session_raw.decode("utf-8", "replace")
        if offset + 4 <= len(data):
            payload, offset = _read_sized_bytes(data, offset)

    return {
        "message_type": message_type,
        "event": event,
        "session_id": session_id,
        "payload": payload,
    }


def _send_packet(
    ws: Any, event: int, payload: Dict[str, Any], session_id: Optional[str] = None
) -> None:
    ws.send(
        _make_packet(event, payload, session_id),
        opcode=websocket.ABNF.OPCODE_BINARY,
    )


def _error_detail(response: Dict[str, Any]) -> str:
    detail = response.get("meta") or response.get("payload") or ""
    if isinstance(detail, bytes):
        return detail.decode("utf-8", "replace")
    return str(detail)


def tts_synthesize(
    text: str,
    speaker_id: str,
    speed: float = 1.0,
    volume: float = 1.0,
    output_path: Optional[str] = None,
    timeout: float = 90.0,
) -> str:
    """通过 lychee TTS WebSocket 合成 MP3，返回输出文件的绝对路径。"""
    if not text or not text.strip():
        raise ValueError("text is required")
    if not speaker_id:
        raise ValueError("speaker_id is required")
    if not output_path:
        raise ValueError("output_path is required")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    session_id = uuid.uuid4().hex
    audio = bytearray()
    started = time.monotonic()
    ws = None

    try:
        ws = websocket.create_connection(
            TTS_WS_URL,
            header=["{}: {}".format(API_KEY_HEADER, get_api_key())],
            timeout=timeout,
        )
        _send_packet(ws, EVENT_START_CONNECTION, {})

        while True:
            if time.monotonic() - started > timeout:
                raise LycheeApiError(504, "TTS timed out")

            raw = ws.recv()
            if isinstance(raw, str):
                continue
            if not isinstance(raw, (bytes, bytearray)):
                raise LycheeApiError(500, "unexpected TTS WebSocket response")

            try:
                response = _parse_response(bytes(raw))
            except ValueError as exc:
                raise LycheeApiError(500, "invalid TTS response: {}".format(exc))

            event = response.get("event")
            message_type = response.get("message_type")

            if message_type == ERROR_INFORMATION:
                raise LycheeApiError(
                    response.get("error_code", 500),
                    _error_detail(response) or "TTS WebSocket error",
                )
            if event in (EVENT_CONNECTION_FAILED, EVENT_SESSION_FAILED):
                raise LycheeApiError(
                    event,
                    _error_detail(response) or "TTS failed at event {}".format(event),
                )

            if event == EVENT_CONNECTION_STARTED:
                _send_packet(
                    ws,
                    EVENT_START_SESSION,
                    {
                        "event": EVENT_START_SESSION,
                        "codec": "mp3",
                        "sample_rate": 24000,
                        "text": text,
                        "speaker_id": speaker_id,
                        "speed": speed,
                        "volume": volume,
                        "ref_audio": "digitalVoice/clone/{}/ref_audio.wav".format(
                            speaker_id
                        ),
                        "ref_text": "digitalVoice/clone/{}/ref_text.txt".format(
                            speaker_id
                        ),
                    },
                    session_id,
                )
            elif event == EVENT_SESSION_STARTED:
                _send_packet(
                    ws,
                    EVENT_TASK_REQUEST,
                    {"event": EVENT_TASK_REQUEST, "text": text},
                    session_id,
                )
                _send_packet(ws, EVENT_FINISH_SESSION, {}, session_id)
            elif event == EVENT_TTS_RESPONSE:
                payload = response.get("payload") or b""
                if message_type == AUDIO_ONLY_RESPONSE and payload:
                    audio.extend(payload)
            elif event == EVENT_SESSION_FINISHED:
                _send_packet(ws, EVENT_FINISH_CONNECTION, {})
            elif event == EVENT_CONNECTION_FINISHED:
                break

    except websocket.WebSocketTimeoutException:
        raise LycheeApiError(504, "TTS timed out")
    except websocket.WebSocketException as exc:
        raise LycheeApiError(502, "TTS WebSocket error: {}".format(exc))
    finally:
        if ws is not None:
            ws.close()

    if not audio:
        raise LycheeApiError(500, "TTS completed without audio payload")

    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(audio))
    return str(path)
