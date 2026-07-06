#!/usr/bin/env python3
"""lychee Video-TS 字幕翻译客户端。"""

import argparse
import json
import mimetypes
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import BASE_URL, LycheeApiError, get_json, post_multipart
from auth import API_KEY_HEADER, MissingApiKeyError, get_api_key
from poll_status import poll_status

MAX_SRT_SIZE = 1024 * 1024
ACTIONS = ("translate", "retranslate", "back-translation")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="提交、查询和下载 lychee Video-TS 字幕翻译任务。"
    )
    parser.add_argument("--action", choices=ACTIONS, help="翻译动作")
    parser.add_argument("--file", type=Path, help="translate/back-translation 使用的 SRT")
    parser.add_argument("--tos-path", help="translate/back-translation 使用的 TOS 路径")
    parser.add_argument("--file-original", type=Path, help="retranslate 原始 SRT")
    parser.add_argument("--file-translated", type=Path, help="retranslate 已翻译 SRT")
    parser.add_argument("--tos-path-original", help="retranslate 原始 SRT 的 TOS 路径")
    parser.add_argument("--tos-path-translated", help="retranslate 已翻译 SRT 的 TOS 路径")
    parser.add_argument("--target-language", help="目标语言（提交任务时必填）")
    parser.add_argument("--user-prompt", default="", help="可选翻译提示词")
    parser.add_argument("--retranslation-items", help="retranslate 必填的 JSON 字符串")
    parser.add_argument("--mode", default="direct", help="提交模式（默认 direct）")
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

    if args.action in ("translate", "back-translation"):
        if bool(args.file) == bool(args.tos_path):
            raise ValueError("必须且只能提供 --file 或 --tos-path 其中一个")
        if args.file:
            validate_srt(args.file, "SRT 文件")
    else:
        file_pair = bool(args.file_original) and bool(args.file_translated)
        tos_pair = bool(args.tos_path_original) and bool(args.tos_path_translated)
        if file_pair == tos_pair:
            raise ValueError(
                "retranslate 必须且只能提供一套文件或 TOS 路径"
            )
        if bool(args.file_original) != bool(args.file_translated):
            raise ValueError("--file-original 与 --file-translated 必须成对提供")
        if bool(args.tos_path_original) != bool(args.tos_path_translated):
            raise ValueError("两个 retranslate TOS 路径必须成对提供")
        if file_pair:
            validate_srt(args.file_original, "原始 SRT")
            validate_srt(args.file_translated, "已翻译 SRT")
        if not args.retranslation_items:
            raise ValueError("retranslate 必须提供 --retranslation-items")
        try:
            json.loads(args.retranslation_items)
        except json.JSONDecodeError as exc:
            raise ValueError("--retranslation-items 不是有效 JSON: {}".format(exc))


def compact(data: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def submit(args: argparse.Namespace) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "target_language": args.target_language,
        "user_prompt": args.user_prompt,
        "mode": args.mode,
    }
    files: Dict[str, Any] = {}

    with ExitStack() as stack:
        if args.action in ("translate", "back-translation"):
            data["tos_path"] = args.tos_path
            if args.file:
                handle = stack.enter_context(args.file.open("rb"))
                mime = mimetypes.guess_type(str(args.file))[0] or "application/x-subrip"
                files["file"] = (args.file.name, handle, mime)
        else:
            data.update(
                {
                    "tos_path_original": args.tos_path_original,
                    "tos_path_translated": args.tos_path_translated,
                    "retranslation_items": args.retranslation_items,
                }
            )
            if args.file_original and args.file_translated:
                original = stack.enter_context(args.file_original.open("rb"))
                translated = stack.enter_context(args.file_translated.open("rb"))
                files["file_original"] = (
                    args.file_original.name,
                    original,
                    "application/x-subrip",
                )
                files["file_translated"] = (
                    args.file_translated.name,
                    translated,
                    "application/x-subrip",
                )

        result = post_multipart(
            "/open/videots/{}".format(args.action),
            files=files,
            data=compact(data),
            timeout=args.timeout,
        )

    if not isinstance(result, dict):
        raise LycheeApiError(500, "videots submit response is not an object")
    if not task_id_from(result):
        raise LycheeApiError(500, "videots submit response is missing task_id")
    return result


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
