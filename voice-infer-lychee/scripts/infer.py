#!/usr/bin/env python3
"""lychee 克隆音色语音推理客户端。"""

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import BASE_URL, LycheeApiError
from auth import API_KEY_HEADER, MissingApiKeyError, get_api_key

SUPPORTED_AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024
MAX_TEXT_LENGTH = 3000


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="调用 lychee OpenAPI 进行克隆音色语音推理（仅返回算法元数据）。"
    )
    parser.add_argument("--text", required=True, help="待推理文本（最多 3000 字符）")
    parser.add_argument(
        "--speaker-id",
        required=True,
        help="克隆音色 ID，使用 voice-clone 返回的 request_id",
    )
    parser.add_argument("--speed", type=float, default=1.0, help="语速（默认 1.0）")
    parser.add_argument("--volume", type=float, default=1.0, help="音量（默认 1.0）")
    parser.add_argument("--sample-rate", type=int, default=44100, help="采样率（默认 44100）")
    parser.add_argument("--ref-text", help="参考音频对应文本")
    parser.add_argument(
        "--audio",
        type=Path,
        help="可选参考音频（wav/mp3/m4a，不超过 10MB）；提供时服务端先克隆",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP 超时秒数（默认 120）")
    parser.add_argument("--output", type=Path, help="将完整响应 JSON 写入文件")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.text.strip():
        raise ValueError("--text 不能为空")
    if len(args.text) > MAX_TEXT_LENGTH:
        raise ValueError("--text 不能超过 3000 字符")
    if not args.speaker_id.strip():
        raise ValueError("--speaker-id 不能为空")
    if args.speed <= 0 or args.volume <= 0:
        raise ValueError("--speed 和 --volume 必须大于 0")
    if args.sample_rate <= 0:
        raise ValueError("--sample-rate 必须大于 0")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")
    if args.audio:
        if not args.audio.is_file():
            raise ValueError("音频文件不存在或不是文件: {}".format(args.audio))
        if args.audio.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
            raise ValueError("不支持的音频格式；仅支持 wav、mp3、m4a")
        if args.audio.stat().st_size > MAX_AUDIO_SIZE:
            raise ValueError("音频文件超过 10MB 限制")


def infer_voice(args: argparse.Namespace) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "speaker_id": args.speaker_id,
        "speed": args.speed,
        "volume": args.volume,
        "sample_rate": args.sample_rate,
    }
    if args.ref_text is not None:
        data["ref_text"] = args.ref_text

    # requests 在 files={} 时会退化为 form-urlencoded，但端点只接受
    # multipart/form-data。将 text 作为无文件名的 multipart 字段发送。
    files: Dict[str, Any] = {"text": (None, args.text)}
    audio_handle = None
    try:
        if args.audio:
            mime = mimetypes.guess_type(str(args.audio))[0] or "application/octet-stream"
            audio_handle = args.audio.open("rb")
            files["audio"] = (args.audio.name, audio_handle, mime)
        # 算法裸 JSON 同时含 code+info+data，会被共享 _unwrap 误认成
        # ApiResponse 并丢失 duration_seconds，因此本端点保留原始响应。
        response = requests.post(
            BASE_URL + "/open/voice/zeroshot/infer",
            headers={API_KEY_HEADER: get_api_key()},
            files=files,
            data=data,
            timeout=args.timeout,
        )
    finally:
        if audio_handle is not None:
            audio_handle.close()

    try:
        result = response.json()
    except ValueError:
        raise LycheeApiError(response.status_code, "voice infer response is not valid JSON")
    if not isinstance(result, dict):
        raise LycheeApiError(500, "voice infer response is not an object")
    if not 200 <= response.status_code < 300:
        raise LycheeApiError(
            result.get("code", response.status_code),
            str(result.get("info") or result.get("message") or response.reason),
            result.get("request_id"),
        )
    code = result.get("code")
    if code not in (200, "200"):
        raise LycheeApiError(
            code,
            str(result.get("info") or result.get("message") or "infer failed"),
        )
    try:
        duration = float(result.get("duration_seconds", 0))
    except (TypeError, ValueError):
        duration = 0
    if duration <= 0:
        raise LycheeApiError(500, "infer returned no duration")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        result = infer_voice(args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        public_result = {
            "success": True,
            "code": 200,
            "duration_seconds": result["duration_seconds"],
            "speaker_id": args.speaker_id,
        }
        print(json.dumps(public_result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps({"success": False, "error": "网络请求失败: {}".format(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps({"success": False, "error": "文件操作失败: {}".format(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
