#!/usr/bin/env python3
"""lychee 视频字幕擦除客户端。"""

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

SUPPORTED_SUFFIXES = {".mp4", ".mov"}
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="上传视频到 lychee OpenAPI，轮询并返回字幕擦除结果。"
    )
    parser.add_argument("--file", required=True, type=Path, help="待擦除字幕的视频（mp4/mov）")
    parser.add_argument("--name", help="可选项目名称")
    parser.add_argument("--language-code", help="可选字幕语言代码")
    parser.add_argument("--subtitle-mode", type=int, choices=(1, 2, 3), help="字幕模式（1-3）")
    parser.add_argument("--interval", type=float, default=5.0, help="轮询间隔秒数（默认 5）")
    parser.add_argument("--timeout", type=float, default=600.0, help="最长等待秒数（默认 600）")
    parser.add_argument("--no-wait", action="store_true", help="提交后立即返回，不轮询结果")
    parser.add_argument("--output", type=Path, help="将完整 JSON 响应写入文件")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if not args.file.is_file():
        raise ValueError("视频文件不存在或不是文件: {}".format(args.file))
    if args.file.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("不支持的视频格式；仅支持 mp4、mov")
    if args.file.stat().st_size > MAX_VIDEO_SIZE:
        raise ValueError("视频文件超过 2GB 限制")
    if args.interval <= 0:
        raise ValueError("--interval 必须大于 0")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def submit(
    file_path: Path,
    name: Optional[str],
    language_code: Optional[str],
    subtitle_mode: Optional[int],
    timeout: float,
) -> Dict[str, Any]:
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    data = {
        key: value
        for key, value in {
            "name": name,
            "language_code": language_code,
            "subtitle_mode": str(subtitle_mode) if subtitle_mode is not None else None,
        }.items()
        if value is not None
    }
    with file_path.open("rb") as video:
        result = post_multipart(
            "/open/subtitle/erase",
            files={"file": (file_path.name, video, mime)},
            data=data,
            timeout=timeout,
        )

    if not isinstance(result, dict):
        raise LycheeApiError(500, "subtitle erase submit response is not an object")
    if not result.get("project_id"):
        raise LycheeApiError(500, "subtitle erase submit response is missing project_id")
    return result


def poll_result(project_id: str, interval: float, timeout: float) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        result = get_json(
            "/open/subtitle/erase/result",
            params={"project_id": project_id},
            timeout=max(0.1, min(60.0, remaining)),
        )
        if not isinstance(result, dict):
            raise LycheeApiError(500, "subtitle erase result response is not an object", project_id)

        status = result.get("status")
        if status == "success":
            return result
        if status == "failed":
            raise LycheeApiError(500, "subtitle erase failed", project_id)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))
    raise LycheeApiError(504, "subtitle erase polling timeout", project_id)


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
        submitted = submit(
            args.file,
            args.name,
            args.language_code,
            args.subtitle_mode,
            args.timeout,
        )
        project_id = str(submitted["project_id"])

        if args.no_wait:
            write_output(args.output, submitted)
            public_result = {
                "success": True,
                "project_id": project_id,
                "waiting": False,
            }
        else:
            result = poll_result(project_id, args.interval, args.timeout)
            write_output(args.output, result)
            public_result = dict(result)
            public_result.update(
                {"success": True, "project_id": project_id, "status": "success"}
            )

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
