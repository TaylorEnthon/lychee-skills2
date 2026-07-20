#!/usr/bin/env python3
"""lychee 同步 AI 配音 CLI。"""

import argparse
import json
import mimetypes
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import requests

for candidate in (
    Path(__file__).resolve().parents[1] / "shared",
    Path(__file__).resolve().parents[3] / "shared",
):
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))
        break

from auth import MissingApiKeyError
from errors import format_error
from http_client import LycheeApiError, post_json, post_multipart

PATH = "/open/voice/lychee-voice"
LIST_PATH = "/open/voice/lychee-voice/list"
FORMATS = {"wav", "mp3", "pcm", "ogg_opus"}
SAMPLE_RATES = {8000, 16000, 24000, 32000, 44100, 48000}
VOICE_MENTION = re.compile(r"\{\{voice:[^}]+}}")


def _voice_names(values):
    """把 argparse 的 action='append' 列表拍平成名字列表（支持逗号分隔）。"""
    if not values:
        return []
    out = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                out.append(item)
    return out


def _load_voice_pool(timeout=60):
    """拉公共音色池 [{id, name}, ...]。失败抛 ValueError。"""
    from http_client import get_json
    raw = get_json(LIST_PATH, timeout=timeout)
    if not isinstance(raw, list):
        raise ValueError("voice list response is not a list")
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        voice_id = item.get("id")
        if isinstance(name, str) and isinstance(voice_id, str):
            out.append({"id": voice_id, "name": name})
    return out


def _resolve_voice_names(names, timeout=60):
    """名字 → id 解析（精确匹配 name 字段）。返回 {resolved: [{name, id}], missing: [name]}。"""
    pool = _load_voice_pool(timeout=timeout)
    resolved = []
    missing = []
    used_ids = set()
    for name in names:
        match = next((e for e in pool if e["name"] == name and e["id"] not in used_ids), None)
        if match:
            resolved.append({"name": name, "id": match["id"]})
            used_ids.add(match["id"])
        else:
            missing.append(name)
    return {"resolved": resolved, "missing": missing}


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def configure_stdio() -> None:
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(description="通过 lychee OpenAPI 同步生成 AI 配音。")
    parser.add_argument("--text", required=True, help="要合成的文本")
    parser.add_argument("--voice-ids", action="append", help="公共音色 ID；可重复或用逗号分隔")
    parser.add_argument("--voice-names", action="append",
                        help="公共音色 name（自动查表转 id）；任何一个 name 找不到时整体降级为纯文本模式（让 AI 自动选音色）。可重复或用逗号分隔")
    parser.add_argument("--audio-urls", action="append", help="临时参考音频 URL/Base64；可重复")
    parser.add_argument("--image", type=Path, help="图片参考（jpeg/png/webp）")
    parser.add_argument("--format", default="wav", help="wav/mp3/pcm/ogg_opus，默认 wav")
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--speech-rate", type=int, default=0)
    parser.add_argument("--loudness-rate", type=int, default=0)
    parser.add_argument("--pitch-rate", type=int, default=0)
    parser.add_argument("--enable-subtitle", action="store_true")
    parser.add_argument("--polish", action="store_true",
                        help="强制调用方对剧本做润色（agent 跳过自动判断，直接走润色路径）")
    parser.add_argument("--no-polish", action="store_true",
                        help="禁用润色（agent 不要自动润色，直接用用户原文本）")
    parser.add_argument("--output", type=Path, help="本地音频输出路径")
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def _voice_ids(values: Optional[List[str]]) -> List[str]:
    return [item.strip() for value in values or [] for item in value.split(",") if item.strip()]


def validate_args(args: argparse.Namespace) -> None:
    args.format = args.format.lower()
    args.voice_ids = _voice_ids(args.voice_ids)
    args.voice_names = _voice_names(getattr(args, "voice_names", None))
    if not args.text.strip():
        raise ValueError("--text 不能为空")
    if len(args.text) > 3000:
        raise ValueError("--text 不能超过 3000 字符")
    if args.format not in FORMATS:
        raise ValueError("--format 仅支持 wav、mp3、pcm、ogg_opus")
    if args.sample_rate not in SAMPLE_RATES:
        raise ValueError("--sample-rate 不支持该采样率")
    if not -50 <= args.speech_rate <= 100 or not -50 <= args.loudness_rate <= 100:
        raise ValueError("speech/loudness rate 必须在 -50 到 100 之间")
    if not -12 <= args.pitch_rate <= 12:
        raise ValueError("--pitch-rate 必须在 -12 到 12 之间")
    if args.timeout <= 0:
        raise ValueError("--timeout 必须大于 0")
    selectors = sum(bool(value) for value in (args.image, args.audio_urls, args.voice_ids))
    if selectors > 1:
        raise ValueError("--image、--audio-urls、--voice-ids 不能混用")
    if len(args.voice_ids) > 3 or len(args.audio_urls or []) > 3:
        raise ValueError("参考音色或音频最多支持 3 个")
    if args.image and not args.image.is_file():
        raise ValueError("图片不存在或不是文件: {}".format(args.image))
    if not (args.image or args.audio_urls or args.voice_ids) and VOICE_MENTION.search(args.text):
        raise ValueError("纯文本模式不允许出现 mention")
    if getattr(args, "polish", False) and getattr(args, "no_polish", False):
        raise ValueError("--polish 和 --no-polish 不能同时传")
    if args.voice_ids and args.voice_names:
        raise ValueError("--voice-ids 和 --voice-names 不能同时传")


def reference_type(args: argparse.Namespace) -> str:
    if args.image:
        return "image"
    if args.audio_urls:
        return "audio_url"
    if args.voice_ids:
        return "voices"
    return "text"


def request_fields(args: argparse.Namespace) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "reference_type": reference_type(args),
        "text_prompt": args.text,
        "format": args.format,
        "sample_rate": args.sample_rate,
        "speech_rate": args.speech_rate,
        "loudness_rate": args.loudness_rate,
        "pitch_rate": args.pitch_rate,
        "enable_subtitle": args.enable_subtitle,
    }
    if args.voice_ids:
        body["voice_ids"] = args.voice_ids
    if args.audio_urls:
        body["audio_urls"] = args.audio_urls
    return body


def generate(args: argparse.Namespace) -> Dict[str, Any]:
    body = request_fields(args)
    if not args.image:
        result = post_json(PATH, body=body, timeout=args.timeout)
    else:
        mime = mimetypes.guess_type(str(args.image))[0] or "application/octet-stream"
        data = {key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in body.items()}
        with args.image.open("rb") as image:
            result = post_multipart(
                PATH,
                files={"image": (args.image.name, image, mime)},
                data=data,
                timeout=args.timeout,
            )
    if not isinstance(result, dict) or not result.get("audio_url"):
        raise LycheeApiError(500, "voice response is missing audio_url")
    return result


def download(url: str, output: Path, timeout: float) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(response.content)


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    try:
        args = build_parser().parse_args(argv)
        validate_args(args)
        fallback_reason = None
        # voice-names 解析：找名字 → ID。任何 name 找不到时整体降级为 text 模式
        if getattr(args, "voice_names", None):
            try:
                resolution = _resolve_voice_names(args.voice_names, timeout=args.timeout)
            except (ValueError, LycheeApiError, requests.RequestException) as exc:
                raise ValueError("查询音色池失败：{}".format(exc))
            resolved = resolution["resolved"]
            missing = resolution["missing"]
            if not resolved and missing:
                # 全部缺失 → text 模式（AI 自动选音色）
                fallback_reason = "所有音色名都不在公共音色池（{}）；已用纯文本模式（让 AI 自动选音色）。".format("、".join(missing))
                args.voice_ids = None
            elif missing:
                # 部分缺失 → 整体降级为 text 模式 + 提示哪些被忽略
                used_names = [r["name"] for r in resolved]
                fallback_reason = "音色「{}」不在公共音色池（{}）；整体降级为纯文本模式（让 AI 自动选音色）。".format(
                    "、".join(missing), "、".join(used_names))
                args.voice_ids = None
            else:
                # 全找到 → 用 resolved ids
                args.voice_ids = [r["id"] for r in resolved]
        output = args.output or Path("{}_voice-lychee.{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"), args.format))
        result = generate(args)
        download(result["audio_url"], output, args.timeout)
        polish_strategy = "auto"
        if getattr(args, "polish", False):
            polish_strategy = "forced"
        elif getattr(args, "no_polish", False):
            polish_strategy = "skipped"
        payload = {
            "success": True,
            "output": str(output),
            "duration_ms": result.get("duration"),
            "audio_url": result["audio_url"],
            "mode": reference_type(args),
            "polish": polish_strategy,
        }
        if fallback_reason:
            payload["fallback_reason"] = fallback_reason
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee"), ensure_ascii=False), file=sys.stderr)
        return 2
    except (LycheeApiError, requests.RequestException) as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查网络和接口参数"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="voice-lychee", hint="检查本地文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
