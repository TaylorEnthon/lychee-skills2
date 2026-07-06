#!/usr/bin/env python3
"""lychee 语音克隆客户端。"""

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError, post_multipart
from auth import MissingApiKeyError
from errors import format_error

SUPPORTED_SUFFIXES = {".wav", ".mp3", ".m4a"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_CARRY_BACK_LENGTH = 500


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="上传参考音频到 lychee OpenAPI 并生成克隆音色。"
    )
    parser.add_argument("--file", required=True, type=Path, help="参考音频（wav/mp3/m4a）")
    parser.add_argument("--carry-back", help="服务端原样透传的字符串（最多 500 字符）")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP 超时秒数（默认 120）")
    parser.add_argument("--output", type=Path, help="将完整响应 JSON 写入文件")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.file.is_file():
        raise ValueError("音频文件不存在或不是文件: {}".format(args.file))
    if args.file.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("不支持的音频格式；仅支持 wav、mp3、m4a")
    if args.file.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("音频文件超过 10MB 限制")
    if args.carry_back is not None and len(args.carry_back) > MAX_CARRY_BACK_LENGTH:
        raise ValueError("--carry-back 不能超过 500 字符")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def clone_voice(
    file_path: Path, carry_back: Optional[str], timeout: float
) -> Dict[str, Any]:
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    data = None
    if carry_back:
        data = {"body": json.dumps({"carry_back": carry_back}, ensure_ascii=False)}

    with file_path.open("rb") as audio:
        result = post_multipart(
            "/open/voice/zeroshot/clone",
            files={"audio": (file_path.name, audio, mime)},
            data=data,
            timeout=timeout,
        )

    if not isinstance(result, dict):
        raise LycheeApiError(500, "voice clone response is not an object")

    code = result.get("code")
    if code not in (200, "200"):
        raise LycheeApiError(
            code,
            str(result.get("message") or "voice clone failed"),
            result.get("request_id"),
        )
    if not result.get("request_id"):
        raise LycheeApiError(500, "voice clone response is missing request_id")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        result = clone_voice(args.file, args.carry_back, args.timeout)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        public_result = {
            "success": True,
            "request_id": result["request_id"],
            "carry_back": result.get("carry_back"),
        }
        print(json.dumps(public_result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="voice-clone", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="voice-clone"), ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps(format_error(exc, step="voice-clone"), ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps(format_error(exc, step="voice-clone", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="voice-clone", hint="检查文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
