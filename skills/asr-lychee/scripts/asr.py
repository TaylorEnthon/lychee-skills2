#!/usr/bin/env python3
"""ASR 客户端。调 https://shanhaistudio.lycheeai.com.cn/openapi/open/asr。"""

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

SUPPORTED_SUFFIXES = {".mp3", ".wav", ".m4a"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="上传音频到 lychee OpenAPI 并输出识别文本。"
    )
    parser.add_argument("--file", required=True, type=Path, help="音频文件（mp3/wav/m4a）")
    parser.add_argument("--language", help="语言代码，如 zh-CN、en-US、ja-JP")
    parser.add_argument("--output", type=Path, help="输出文件（默认输出到 stdout）")
    parser.add_argument(
        "--debug", action="store_true", help="输出完整 data JSON，而不是纯文本"
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="HTTP 超时秒数（默认 60）")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.file.is_file():
        raise ValueError("音频文件不存在或不是文件: {}".format(args.file))
    if args.file.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("不支持的音频格式；仅支持 mp3、wav、m4a")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def recognize(file_path: Path, language: Optional[str], timeout: float) -> Dict[str, Any]:
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    data = {"language": language} if language else None
    with file_path.open("rb") as audio:
        result = post_multipart(
            "/open/asr",
            files={"file": (file_path.name, audio, mime)},
            data=data,
            timeout=timeout,
        )
    if not isinstance(result, dict):
        raise LycheeApiError(500, "ASR response data is not an object")
    return result


def render_result(result: Dict[str, Any], debug: bool) -> str:
    if debug:
        return json.dumps(result, ensure_ascii=False, indent=2)
    text = result.get("text")
    if text is None:
        raise LycheeApiError(500, "ASR response is missing text")
    return str(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        output = render_result(
            recognize(args.file, args.language, args.timeout), args.debug
        )
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 0
    except MissingApiKeyError as exc:
        print("配置错误: {}".format(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print("参数错误: {}".format(exc), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print("ASR 请求失败: {}".format(exc), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print("网络请求失败: {}".format(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print("文件操作失败: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
