#!/usr/bin/env python3
"""lychee 音色设计客户端（mimo 模式）。"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError, post_json
from auth import MissingApiKeyError
from errors import format_error

MAX_TEXT_LENGTH = 500


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="用自然语言描述调用 lychee OpenAPI mimo 音色设计。"
    )
    parser.add_argument("--description", required=True, help="音色自然语言描述（最多 500 字符）")
    parser.add_argument("--text", required=True, help="试听文本（最多 500 字符）")
    parser.add_argument("--optimize-text", dest="optimize_text", action="store_const", const=True, default=None, help="润色 text（与 --no-optimize-text 二选一）")
    parser.add_argument("--no-optimize-text", dest="optimize_text", action="store_const", const=False, help="不润色 text")
    parser.add_argument("--timeout", type=float, default=180.0, help="HTTP 超时秒数（默认 180）")
    parser.add_argument("--output", type=Path, help="将完整响应 JSON 写入文件")
    return parser


def validate_text(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError("--{} 不能为空".format(name))
    if len(value) > MAX_TEXT_LENGTH:
        raise ValueError("--{} 不能超过 {} 字符".format(name, MAX_TEXT_LENGTH))


def validate_args(args: argparse.Namespace) -> None:
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")
    validate_text(args.description, "description")
    validate_text(args.text, "text")


def design_timbre(args: argparse.Namespace) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "description": args.description,
        "text": args.text,
    }
    if args.optimize_text is not None:
        body["optimize_text"] = args.optimize_text

    result = post_json(
        "/open/timbre-design/generate-mimo",
        body,
        timeout=args.timeout,
    )
    if not isinstance(result, dict):
        raise LycheeApiError(500, "timbre-design response is not an object")
    audio_url = result.get("audioUrl") or result.get("audio_url")
    if not audio_url:
        raise LycheeApiError(500, "timbre-design response missing audioUrl")
    result["audioUrl"] = audio_url
    result["requestId"] = result.get("requestId") or result.get("request_id") or result.get("audioId") or result.get("audio_id")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        result = design_timbre(args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        public_result = {
            "success": True,
            "audioUrl": result["audioUrl"],
            "requestId": result.get("requestId"),
        }
        print(json.dumps(public_result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="timbre-design", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="timbre-design"), ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps(format_error(exc, step="timbre-design"), ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps(format_error(exc, step="timbre-design", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="timbre-design", hint="检查文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())