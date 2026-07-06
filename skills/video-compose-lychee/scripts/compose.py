#!/usr/bin/env python3
"""lychee 视频音频字幕合成压制客户端。"""

import argparse
import json
import mimetypes
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Set

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError, get_json, post_multipart
from auth import MissingApiKeyError
from errors import format_error
from poll_status import poll_status

MAX_VIDEO_SIZE = 1024 * 1024 * 1024
MAX_AUDIO_SIZE = 200 * 1024 * 1024
MAX_SUBTITLE_SIZE = 10 * 1024 * 1024
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a"}
POSITION_FIELDS = (
    "subtitle_x",
    "subtitle_y",
    "subtitle_font_size",
    "coordinate_width",
    "coordinate_height",
)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="上传视频、音频和字幕到 lychee OpenAPI，轮询并返回压制合成结果。"
    )
    parser.add_argument("--video-file", required=True, type=Path, help="视频文件（mp4，最大 1GB）")
    parser.add_argument("--audio-file", type=Path, help="可选音频文件（mp3/wav/m4a，最大 200MB）")
    parser.add_argument("--subtitle-file", type=Path, help="可选 SRT 字幕文件（最大 10MB）")
    parser.add_argument("--target-language", help="字幕目标语言；传 --subtitle-file 时必填")
    parser.add_argument("--subtitle-x", type=int, help="字幕区域左上角 X 坐标")
    parser.add_argument("--subtitle-y", type=int, help="字幕区域左上角 Y 坐标")
    parser.add_argument("--subtitle-font-size", type=int, help="字幕字号，范围 12-96")
    parser.add_argument("--coordinate-width", type=int, help="字幕坐标来源画布宽度")
    parser.add_argument("--coordinate-height", type=int, help="字幕坐标来源画布高度")
    parser.add_argument("--interval", type=float, default=5.0, help="轮询间隔秒数（默认 5）")
    parser.add_argument("--timeout", type=float, default=600.0, help="最长等待秒数（默认 600）")
    parser.add_argument("--no-wait", action="store_true", help="提交后立即返回，不轮询结果")
    parser.add_argument("--download-output", type=Path, help="将 resultPath 下载到本地文件")
    parser.add_argument("--output", type=Path, help="将完整 JSON 响应写入文件")
    return parser


def _validate_file(path: Path, suffixes: Set[str], max_size: int, label: str) -> None:
    if not path.is_file():
        raise ValueError("{}不存在或不是文件: {}".format(label, path))
    if path.suffix.lower() not in suffixes:
        raise ValueError("{}格式不支持；仅支持 {}".format(label, "、".join(sorted(suffixes))))
    if path.stat().st_size > max_size:
        raise ValueError("{}超过 {}MB 限制".format(label, max_size // 1024 // 1024))


def validate_args(args: argparse.Namespace) -> None:
    _validate_file(args.video_file, {".mp4"}, MAX_VIDEO_SIZE, "视频文件")
    if args.audio_file is not None:
        _validate_file(args.audio_file, AUDIO_SUFFIXES, MAX_AUDIO_SIZE, "音频文件")
    if args.subtitle_file is not None:
        _validate_file(args.subtitle_file, {".srt"}, MAX_SUBTITLE_SIZE, "字幕文件")
        if not args.target_language:
            raise ValueError("传 --subtitle-file 时必须同时传 --target-language")
    elif args.target_language:
        print("WARN: 未传 --subtitle-file，--target-language 将随请求透传但后端不强制", file=sys.stderr)

    present = {field for field in POSITION_FIELDS if getattr(args, field) is not None}
    if present and len(present) != len(POSITION_FIELDS):
        missing = sorted(set(POSITION_FIELDS) - present)
        raise ValueError("字幕位置参数必须 5 个同时传；缺少: {}".format(", ".join("--" + item.replace("_", "-") for item in missing)))
    if args.subtitle_font_size is not None and not 12 <= args.subtitle_font_size <= 96:
        raise ValueError("--subtitle-font-size 必须在 12-96 之间")
    if args.interval <= 0:
        raise ValueError("--interval 必须大于 0")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")


def submit(args: argparse.Namespace) -> Dict[str, Any]:
    data = {
        key: value
        for key, value in {
            "target_language": args.target_language,
            "subtitle_x": args.subtitle_x,
            "subtitle_y": args.subtitle_y,
            "subtitle_font_size": args.subtitle_font_size,
            "coordinate_width": args.coordinate_width,
            "coordinate_height": args.coordinate_height,
        }.items()
        if value is not None
    }
    with ExitStack() as stack:
        video = stack.enter_context(args.video_file.open("rb"))
        files = {
            "video_file": (
                args.video_file.name,
                video,
                mimetypes.guess_type(str(args.video_file))[0] or "video/mp4",
            )
        }
        if args.audio_file is not None:
            audio = stack.enter_context(args.audio_file.open("rb"))
            files["audio_file"] = (
                args.audio_file.name,
                audio,
                mimetypes.guess_type(str(args.audio_file))[0] or "application/octet-stream",
            )
        if args.subtitle_file is not None:
            subtitle = stack.enter_context(args.subtitle_file.open("rb"))
            files["subtitle_file"] = (args.subtitle_file.name, subtitle, "application/x-subrip")
        result = post_multipart(
            "/open/video-compose/tasks",
            files=files,
            data=data,
            timeout=args.timeout,
        )

    if not isinstance(result, dict):
        raise LycheeApiError(500, "video compose submit response is not an object")
    if not (result.get("task_id") or result.get("taskId")):
        raise LycheeApiError(500, "video compose submit response is missing task_id")
    return result


def poll_result(task_id: str, interval: float, timeout: float) -> Dict[str, Any]:
    def fetch() -> Dict[str, Any]:
        return get_json(
            "/open/video-compose/status",
            params={"task_id": task_id},
            timeout=max(0.1, min(60.0, timeout)),
        )

    return poll_status(
        fetch,
        interval=interval,
        timeout=timeout,
        success_states=("completed",),
        error_states=("failed",),
        error_field="errorMessage",
        default_error="video compose failed",
        timeout_error="video compose polling timeout",
        response_error="video compose status response is not an object",
        request_id_field="task_id",
        request_id=task_id,
        pending_states=("pending",),
    )


def download_file(url: str, path: Path, timeout: float) -> None:
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        expected = int(response.headers.get("Content-Length") or 0)
        path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with path.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
                    written += len(chunk)
        if expected and written != expected:
            raise requests.RequestException(
                "下载大小不完整: expected {} bytes, got {}".format(expected, written)
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
        submitted = submit(args)
        task_id = str(submitted.get("task_id") or submitted["taskId"])

        if args.no_wait:
            public_result = {
                "success": True,
                "task_id": task_id,
                "waiting": False,
            }
            write_output(args.output, submitted)
        else:
            result = poll_result(task_id, args.interval, args.timeout)
            result_path = str(result.get("resultPath") or "")
            if args.download_output is not None:
                if not result_path:
                    raise LycheeApiError(500, "video compose completed but resultPath is empty", task_id)
                download_file(result_path, args.download_output, args.timeout)
            public_result = {
                "success": True,
                "task_id": task_id,
                "status": "completed",
                "result_path": result_path,
            }
            write_output(args.output, result)

        print(json.dumps(public_result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="video-compose", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="video-compose"), ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps(format_error(exc, step="video-compose"), ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps(format_error(exc, step="video-compose", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="video-compose", hint="检查文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
