#!/usr/bin/env python3
"""拉取 voice-lychee 公共音色并缓存 24 小时。"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import requests

for candidate in (Path(__file__).resolve().parents[1] / "shared", Path(__file__).resolve().parents[3] / "shared"):
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break

from auth import MissingApiKeyError
from errors import format_error
from http_client import LycheeApiError, get_json

DEFAULT_CACHE = Path(__file__).resolve().parents[1] / "data" / "voices-cache.json"


def _fresh_cache(path: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - updated < timedelta(hours=24) and isinstance(payload["voices"], list):
            return payload["voices"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def _normalize(items: Any) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        raise LycheeApiError(500, "voice list response is not an array")
    fields = ("id", "name", "description", "type", "gender", "lang_code")
    return [{key: item.get(key) for key in fields if key in item} for item in items if isinstance(item, dict)]


def list_voices(cache_path: Path = DEFAULT_CACHE, *, refresh: bool = False, no_cache: bool = False, timeout: float = 60) -> List[Dict[str, Any]]:
    if not no_cache and not refresh:
        cached = _fresh_cache(cache_path)
        if cached is not None:
            return cached
    voices = _normalize(get_json("/open/voice/lychee-voice/list", timeout=timeout))
    if not no_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "voices": voices,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return voices


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="拉取公共音色池并缓存 24 小时。")
    parser.add_argument("--refresh", action="store_true", help="忽略缓存并重新拉取")
    parser.add_argument("--no-cache", action="store_true", help="不读写缓存")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        print(json.dumps({"success": True, "voices": list_voices(refresh=args.refresh, no_cache=args.no_cache, timeout=args.timeout)}, ensure_ascii=False, indent=2))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except (LycheeApiError, requests.RequestException) as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查缓存目录权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

