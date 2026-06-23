#!/usr/bin/env python3
"""lychee 音色设计客户端。"""

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

LANG_CODES = ("zh", "en", "ja", "de", "fr", "es", "ko", "ar", "ru", "nl", "it", "pl", "pt", "vi", "id", "th")
MAX_TEXT_LENGTH = 500


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="调用 lychee OpenAPI 按性别、年龄、风格和口音生成试听音色。"
    )
    parser.add_argument("--text", required=True, help="试听文本（最多 500 字符）")
    parser.add_argument("--lang", required=True, choices=LANG_CODES, help="语言代码")
    parser.add_argument("--gender", required=True, type=int, choices=(1, 2), help="1=男，2=女")
    parser.add_argument("--age", required=True, type=int, choices=(1, 2, 3, 4), help="1=儿童，2=青年，3=中年，4=老年")
    parser.add_argument("--pitch", type=int, choices=range(1, 7), default=1, help="1=跳过，2-6=极低到极高")
    parser.add_argument("--style", type=int, choices=(1, 2), default=1, help="1=跳过，2=耳语")
    parser.add_argument("--accent", type=int, choices=range(1, 14), default=1, help="1=跳过；中文 2-13，英文 2-11")
    parser.add_argument("--timeout", type=float, default=180.0, help="HTTP 超时秒数（默认 180）")
    parser.add_argument("--output", type=Path, help="将完整响应 JSON 写入文件")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.text.strip():
        raise ValueError("--text 不能为空")
    if len(args.text) > MAX_TEXT_LENGTH:
        raise ValueError("--text 不能超过 500 字符")
    if args.lang == "en" and args.accent > 11:
        raise ValueError("英文 --accent 只支持 1-11")
    if args.lang not in ("zh", "en") and args.accent != 1:
        raise ValueError("非中英文语言 --accent 只支持 1（跳过）")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def design_timbre(args: argparse.Namespace) -> Dict[str, Any]:
    values = {
        "text": args.text,
        "lang_code": args.lang,
        "gender_value": str(args.gender),
        "age_value": str(args.age),
        "pitch_value": str(args.pitch) if args.pitch is not None else None,
        "style_value": str(args.style) if args.style is not None else None,
        "accent_value": str(args.accent) if args.accent is not None else None,
    }
    body = {key: value for key, value in values.items() if value is not None}
    result = post_json(
        "/open/timbre-design/generate",
        body,
        timeout=args.timeout,
    )
    if not isinstance(result, dict):
        raise LycheeApiError(500, "timbre-design response is not an object")
    audio_url = result.get("audioUrl") or result.get("audio_url")
    if not audio_url:
        raise LycheeApiError(500, "timbre-design response missing audioUrl")
    # 生产环境当前受全局 SNAKE_CASE 影响，同时兼容契约中的 camelCase。
    result["audioUrl"] = audio_url
    result["requestId"] = result.get("requestId") or result.get("request_id")
    result["outputDir"] = result.get("outputDir") or result.get("output_dir")
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
