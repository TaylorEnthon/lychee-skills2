#!/usr/bin/env python3
"""lychee Video-TS 字幕翻译客户端。"""

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import BASE_URL, LycheeApiError, get_json, post_multipart
from auth import API_KEY_HEADER, MissingApiKeyError, get_api_key
from errors import format_error
from poll_status import poll_status

MAX_SRT_SIZE = 1024 * 1024
MAX_FILE_URL_LENGTH = 2048
ACTIONS = ("translate",)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="提交、查询和下载 lychee Video-TS 字幕翻译任务。"
    )
    parser.add_argument("--action", choices=ACTIONS, help="翻译动作（仅 translate）")
    parser.add_argument("--file", type=Path, help="本地 SRT 文件路径（≤1MB）")
    parser.add_argument("--file-url", help="公网 HTTP/HTTPS SRT 链接（≤2048 字符）")
    parser.add_argument("--target-language", help="目标语言（提交任务时必填）")
    parser.add_argument("--user-prompt", default="", help="可选翻译提示词")
    parser.add_argument("--interval", type=float, default=5.0, help="轮询间隔秒数（默认 5）")
    parser.add_argument("--timeout", type=float, default=600.0, help="最长等待秒数（默认 600）")
    parser.add_argument("--download-output", type=Path, help="下载完成后的 SRT 到此路径")
    parser.add_argument("--tasks", action="store_true", help="列出当前用户的所有任务")
    parser.add_argument("--status-task-id", help="查询指定 task_id 的状态")
    parser.add_argument("--no-wait", action="store_true", help="提交后立即返回，不轮询")
    parser.add_argument("--output", type=Path, help="将完整 JSON 响应写入文件")
    return parser


def validate_srt(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError("{}不存在或不是文件: {}".format(label, path))
    if path.suffix.lower() != ".srt":
        raise ValueError("{}仅支持 .srt 文件".format(label))
    if path.stat().st_size > MAX_SRT_SIZE:
        raise ValueError("{}超过 1MB 限制".format(label))


def validate_file_url(url: str) -> None:
    if len(url) > MAX_FILE_URL_LENGTH:
        raise ValueError("--file-url 长度不能超过 {} 字符".format(MAX_FILE_URL_LENGTH))
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("--file-url 必须以 http:// 或 https:// 开头")


def validate_args(args: argparse.Namespace) -> None:
    if args.interval <= 0:
        raise ValueError("--interval 必须大于 0")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")
    if args.tasks and args.status_task_id:
        raise ValueError("--tasks 与 --status-task-id 不能同时使用")
    if args.tasks or args.status_task_id:
        return
    if args.action is None:
        raise ValueError("提交任务时必须提供 --action")
    if not args.target_language:
        raise ValueError("提交任务时必须提供 --target-language")
    if args.no_wait and args.download_output:
        raise ValueError("--no-wait 不能与 --download-output 同时使用")

    has_file = bool(args.file)
    has_url = bool(args.file_url)
    if has_file and has_url:
        raise ValueError("--file 与 --file-url 不能同时使用")
    if not has_file and not has_url:
        raise ValueError("必须提供 --file 或 --file-url 其中一个")
    if has_file:
        validate_srt(args.file, "SRT 文件")
    else:
        validate_file_url(args.file_url)


def compact(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def submit(args: argparse.Namespace) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "target_language": args.target_language,
        "user_prompt": args.user_prompt,
    }
    if args.file_url:
        data["file_url"] = args.file_url
    files: Dict[str, Any] = {}
    if args.file:
        mime = mimetypes.guess_type(str(args.file))[0] or "application/x-subrip"
        files["file"] = (args.file.name, args.file.open("rb"), mime)

    return post_multipart(
        "/open/videots/translate",
        files=files,
        data=compact(data),
        timeout=args.timeout,
    )


def task_id_from(result: Dict[str, Any]) -> Optional[str]:
    value = result.get("task_id") or result.get("taskId")
    return str(value) if value is not None else None


def poll_result(task_id: str, interval: float, timeout: float) -> Dict[str, Any]:
    def fetch() -> Dict[str, Any]:
        return get_json(
            "/open/videots/status",
            params={"task_id": task_id},
            timeout=max(0.1, min(60.0, timeout)),
        )

    return poll_status(
        fetch,
        interval=interval,
        timeout=timeout,
        success_states=("completed",),
        error_states=("failed", "error"),
        error_field=("message", "error"),
        default_error="videots failed",
        timeout_error="videots polling timeout",
        response_error="videots status response is not an object",
        request_id_field="task_id",
        request_id=task_id,
    )


def download_result(task_id: str, output_path: Path, timeout: float) -> None:
    response = requests.get(
        BASE_URL.rstrip("/") + "/open/videots/download",
        params={"task_id": task_id},
        headers={API_KEY_HEADER: get_api_key()},
        timeout=timeout,
    )
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            body = response.json()
        except ValueError:
            raise LycheeApiError(response.status_code, "download response is not valid JSON")
        if not response.ok:
            info = body.get("info") if isinstance(body, dict) else response.reason
            raise LycheeApiError(response.status_code, str(info or "videots download failed"), task_id)
        payload = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
        if not isinstance(payload, dict):
            raise LycheeApiError(500, "videots download JSON is not an object", task_id)
        download_url = payload.get("download_url") or payload.get("downloadUrl")
        if not download_url:
            raise LycheeApiError(500, "videots download response is missing download_url", task_id)
        response = requests.get(str(download_url), timeout=timeout)

    response.raise_for_status()
    if not response.content:
        raise LycheeApiError(500, "videots download returned an empty file", task_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)


def write_output(path: Optional[Path], result: Any) -> None:
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
        if args.tasks:
            tasks = get_json("/open/videots/tasks", timeout=args.timeout)
            if not isinstance(tasks, list):
                raise LycheeApiError(500, "videots tasks response is not a list")
            write_output(args.output, tasks)
            print(json.dumps({"success": True, "tasks": tasks}, ensure_ascii=False))
            return 0

        if args.status_task_id:
            result = get_json(
                "/open/videots/status",
                params={"task_id": args.status_task_id},
                timeout=args.timeout,
            )
            if not isinstance(result, dict):
                raise LycheeApiError(500, "videots status response is not an object", args.status_task_id)
            write_output(args.output, result)
            public_result = {"success": True}
            public_result.update(result)
            print(json.dumps(public_result, ensure_ascii=False))
            return 0

        submitted = submit(args)
        task_id = task_id_from(submitted)
        if args.no_wait:
            write_output(args.output, submitted)
            print(
                json.dumps(
                    {"success": True, "task_id": task_id, "waiting": False},
                    ensure_ascii=False,
                )
            )
            return 0

        result = poll_result(task_id, args.interval, args.timeout)
        write_output(args.output, result)
        if args.download_output:
            download_result(task_id, args.download_output, args.timeout)
        print(
            json.dumps(
                {
                    "success": True,
                    "task_id": task_id,
                    "status": "completed",
                    "download_url": result.get("downloadUrl") or result.get("download_url") or "",
                },
                ensure_ascii=False,
            )
        )
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="videots", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="videots"), ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps(format_error(exc, step="videots"), ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps(format_error(exc, step="videots", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="videots", hint="检查文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())