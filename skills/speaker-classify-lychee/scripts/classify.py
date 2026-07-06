#!/usr/bin/env python3
"""lychee 公共说话人分类客户端。"""

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError, get_json, post_multipart
from auth import MissingApiKeyError
from poll_status import poll_status

SUPPORTED_SUFFIXES = {
    ".3gp", ".3gpp", ".aac", ".aif", ".aiff", ".alac", ".amr", ".ape",
    ".au", ".awb", ".caf", ".dsf", ".flac", ".m4a", ".mka", ".mp3",
    ".oga", ".ogg", ".opus", ".ra", ".tta", ".wav", ".weba", ".wma",
    ".wv",
}
MAX_FILE_SIZE = 50 * 1024 * 1024


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="上传音频到 lychee OpenAPI，轮询并返回说话人分类结果。"
    )
    parser.add_argument("--file", required=True, type=Path, help="待分类的音频文件")
    parser.add_argument("--interval", type=float, default=3.0, help="轮询间隔秒数（默认 3）")
    parser.add_argument("--timeout", type=float, default=300.0, help="最长等待秒数（默认 300）")
    parser.add_argument("--no-wait", action="store_true", help="提交后立即返回，不轮询结果")
    parser.add_argument("--output", type=Path, help="将完整 JSON 响应写入文件")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.file.is_file():
        raise ValueError("音频文件不存在或不是文件: {}".format(args.file))
    if args.file.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("不支持的音频格式: {}".format(args.file.suffix or "无扩展名"))
    if args.file.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("音频文件超过 50MB 限制")
    if args.interval <= 0:
        raise ValueError("--interval 必须大于 0")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def submit(file_path: Path, timeout: float) -> Dict[str, Any]:
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    with file_path.open("rb") as audio:
        result = post_multipart(
            "/open/speaker-classify/submit",
            files={"file": (file_path.name, audio, mime)},
            timeout=timeout,
        )
    if not isinstance(result, dict):
        raise LycheeApiError(500, "speaker classify submit response is not an object")
    if not result.get("request_id"):
        raise LycheeApiError(500, "speaker classify submit response is missing request_id")
    return result


def poll_result(request_id: str, interval: float, timeout: float) -> Dict[str, Any]:
    def fetch() -> Dict[str, Any]:
        return get_json(
            "/open/speaker-classify/status",
            params={"request_id": request_id},
            timeout=max(0.1, min(60.0, timeout)),
        )

    return poll_status(
        fetch,
        interval=interval,
        timeout=timeout,
        success_states=("success",),
        error_states=("error",),
        error_field="error",
        default_error="speaker classify failed",
        timeout_error="speaker classify polling timeout",
        response_error="speaker classify status response is not an object",
        request_id_field="request_id",
        request_id=request_id,
    )


def write_output(path: Optional[Path], result: Dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        submitted = submit(args.file, args.timeout)
        request_id = str(submitted["request_id"])

        if args.no_wait:
            write_output(args.output, submitted)
            public_result = {
                "success": True,
                "request_id": request_id,
                "waiting": False,
            }
        else:
            result = poll_result(request_id, args.interval, args.timeout)
            write_output(args.output, result)
            public_result = {
                "success": True,
                "request_id": request_id,
                "spk_result": result.get("spk_result", []),
                "asr_duration": result.get("asr_duration"),
                "duration_ms": result.get("duration_ms"),
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
