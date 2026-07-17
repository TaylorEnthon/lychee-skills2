#!/usr/bin/env python3
"""查询 voice-lychee 任务历史。"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests

for candidate in (Path(__file__).resolve().parents[1] / "shared", Path(__file__).resolve().parents[3] / "shared"):
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break

from auth import MissingApiKeyError
from errors import format_error
from http_client import LycheeApiError, get_json


def list_tasks(*, page: int = 1, page_size: int = 20, status: Optional[str] = None, timeout: float = 60) -> Dict[str, Any]:
    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    result = get_json("/open/voice/lychee-voice/tasks", params=params, timeout=timeout)
    if not isinstance(result, dict) or not isinstance(result.get("list"), list):
        raise LycheeApiError(500, "task list response is invalid")
    return {
        "success": True,
        "total": result.get("total", len(result["list"])),
        "page": result.get("page", page),
        "page_size": result.get("page_size", page_size),
        "tasks": result["list"],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="查询 AI 配音任务历史。")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--status", choices=("success", "failed"))
    parser.add_argument("--output", type=Path, help="将完整 data 响应写入 JSON 文件")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        if args.page < 1 or not 1 <= args.page_size <= 100 or args.timeout <= 0:
            raise ValueError("page >= 1、page-size 为 1-100、timeout > 0")
        result = list_tasks(page=args.page, page_size=args.page_size, status=args.status, timeout=args.timeout)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee"), ensure_ascii=False), file=sys.stderr)
        return 2
    except (LycheeApiError, requests.RequestException) as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查输出路径权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

