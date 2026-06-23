#!/usr/bin/env python3
"""lychee TTS 命令行客户端。"""

import argparse
import base64
from datetime import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from ws_client import TTS_WS_URL, tts_synthesize
from auth import MissingApiKeyError
from http_client import LycheeApiError

DEFAULT_VOICE_ID = "默认女声"
REQUIRED_VOICES = ["默认女声", "默认男声", "性感女声", "小男孩声音", "云南话男声"]


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def load_json(name: str) -> Dict[str, Any]:
    path = data_dir() / name
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("{} must contain a JSON object".format(path))
    return value


def load_voice_data() -> Tuple[Dict[str, str], Dict[str, Any], Dict[str, Any]]:
    alias_map = load_json("alias_map.json")
    presets = load_json("presets.json")
    voice_aliases = load_json("voice_aliases.json")

    missing = [voice for voice in REQUIRED_VOICES if voice not in presets]
    if missing:
        raise ValueError("required voices missing from presets: {}".format(", ".join(missing)))
    broken = [
        voice for voice in REQUIRED_VOICES if alias_map.get(voice) not in presets
    ]
    if broken:
        raise ValueError("required aliases cannot resolve: {}".format(", ".join(broken)))
    return alias_map, presets, voice_aliases


def resolve_speaker_id(preset: Dict[str, Any]) -> str:
    speaker_ref = preset.get("speaker_ref")
    if not isinstance(speaker_ref, str) or not speaker_ref:
        raise ValueError("preset is missing speaker_ref")
    encoded = speaker_ref[4:] if speaker_ref.startswith("b64:") else speaker_ref
    try:
        return base64.b64decode(encoded).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("preset speaker_ref is invalid: {}".format(exc))


def supports_contains_matching(preset: Dict[str, Any]) -> bool:
    return preset.get("match_mode", "normal") != "exact"


def resolve_voice_id(
    user_voice: Optional[str],
    alias_map: Dict[str, str],
    presets: Dict[str, Any],
    voice_aliases: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool, Optional[str]]:
    if not user_voice:
        return DEFAULT_VOICE_ID, True, None

    voice = user_voice.strip()
    if voice in alias_map and alias_map[voice] in presets:
        return alias_map[voice], False, voice
    if voice in presets:
        return voice, False, voice

    for alias in sorted(alias_map, key=len, reverse=True):
        voice_id = alias_map[alias]
        if (
            alias in voice
            and voice_id in presets
            and supports_contains_matching(presets[voice_id])
        ):
            return voice_id, False, alias

    expanded_aliases: List[Tuple[str, str]] = []
    for voice_id, aliases in (voice_aliases or {}).items():
        if (
            voice_id not in presets
            or not isinstance(aliases, list)
            or not supports_contains_matching(presets[voice_id])
        ):
            continue
        for alias in aliases:
            if isinstance(alias, str) and alias:
                expanded_aliases.append((alias, voice_id))
    for alias, voice_id in sorted(
        expanded_aliases, key=lambda item: len(item[0]), reverse=True
    ):
        if alias in voice:
            return voice_id, False, alias

    keyword_rules = [
        (("男童",), "小男孩声音"),
        (("女童",), "小女孩声音"),
        (("东北", "男"), "东北话男声"),
        (("东北", "女"), "东北话女声"),
        (("四川", "男"), "四川话男声"),
        (("四川", "女"), "四川话女声"),
        (("河南", "男"), "河南话男声"),
        (("河南", "女"), "河南话女声"),
        (("陕西", "男"), "陕西话男声"),
        (("陕西", "女"), "陕西话女声"),
        (("播音", "男"), "播音员男声"),
        (("播音", "女"), "播音员女声"),
        (("新闻", "男"), "播音员男声"),
        (("新闻", "女"), "播音员女声"),
        (("旁白",), "旁白男声"),
        (("客服", "男"), "客服男声"),
        (("客服", "女"), "客服女声"),
        (("助眠", "男"), "助眠男声"),
        (("助眠", "女"), "助眠女声"),
        (("耳语", "男"), "耳语男声"),
        (("耳语", "女"), "耳语女声"),
        (("低沉", "男"), "低沉男声"),
        (("低沉", "女"), "低沉女声"),
        (("甜", "女"), "甜美女声"),
        (("温柔",), "温柔女声"),
    ]
    for keywords, alias in keyword_rules:
        if all(keyword in voice for keyword in keywords) and alias in alias_map:
            voice_id = alias_map[alias]
            if voice_id in presets:
                return voice_id, False, alias

    if "男" in voice and alias_map.get("默认男声") in presets:
        return alias_map["默认男声"], True, None
    if "女" in voice and alias_map.get("默认女声") in presets:
        return alias_map["默认女声"], True, None
    return DEFAULT_VOICE_ID, True, None


def preview_match(voice: Optional[str]) -> Dict[str, Any]:
    alias_map, presets, voice_aliases = load_voice_data()
    voice_id, used_default, matched_alias = resolve_voice_id(
        voice, alias_map, presets, voice_aliases
    )
    result = {
        "success": True,
        "voice": presets[voice_id]["name"],
        "used_default_voice": used_default,
    }
    if matched_alias:
        result["matched"] = matched_alias
    return result


def list_voices() -> Dict[str, Any]:
    _, presets, _ = load_voice_data()
    categories: List[str] = []
    category_map: Dict[str, List[str]] = {}
    for preset in presets.values():
        if not preset.get("listable", True):
            continue
        category = preset.get("category", "扩展")
        if category not in category_map:
            categories.append(category)
            category_map[category] = []
        category_map[category].append(preset["name"])
    return {
        "success": True,
        "categories": [
            {"name": name, "voices": category_map[name]} for name in categories
        ],
    }


def run_doctor() -> Dict[str, Any]:
    alias_map, presets, voice_aliases = load_voice_data()
    voice_id, used_default, matched_alias = resolve_voice_id(
        "性感的女声", alias_map, presets, voice_aliases
    )
    if voice_id != "性感女声" or used_default:
        raise ValueError("音色匹配检查失败: 性感的女声 -> {}".format(voice_id))
    return {
        "success": True,
        "presets": len(presets),
        "aliases": len(alias_map),
        "voice_groups": len(voice_aliases),
        "required_voices": REQUIRED_VOICES,
        "preview": {
            "input": "性感的女声",
            "voice": voice_id,
            "matched": matched_alias,
        },
        "tts_ws_url": TTS_WS_URL,
    }


def sanitize_filename_part(value: str, max_chars: int = 24) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", value or "")
    cleaned = re.sub(r"\s+", "", cleaned).strip(". ")
    return cleaned[:max_chars] or "默认音色"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="调用 lychee TTS WebSocket 合成 MP3 音频。")
    parser.add_argument("--text", help="待合成文本（最多 5000 字符）")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="音色名或自然语言描述")
    parser.add_argument("--output", help="输出 MP3 路径")
    parser.add_argument("--speed", type=float, default=1.0, help="语速（默认 1.0）")
    parser.add_argument("--volume", type=float, default=1.0, help="音量（默认 1.0）")
    parser.add_argument("--timeout", type=float, default=90.0, help="WebSocket 超时秒数（默认 90）")
    parser.add_argument("--list-voices", action="store_true", help="按分类列出全部可用音色")
    parser.add_argument("--preview-match", help="预览描述将匹配的音色，不合成")
    parser.add_argument("--doctor", action="store_true", help="运行离线自检")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        if args.doctor:
            result = run_doctor()
        elif args.list_voices:
            result = list_voices()
        elif args.preview_match is not None:
            result = preview_match(args.preview_match)
        else:
            if not args.text or not args.text.strip():
                raise ValueError("--text is required for synthesis")
            if len(args.text) > 5000:
                raise ValueError("--text must not exceed 5000 characters")
            if args.speed <= 0 or args.volume <= 0 or args.timeout <= 0:
                raise ValueError("--speed, --volume and --timeout must be greater than zero")

            alias_map, presets, voice_aliases = load_voice_data()
            voice_id, _, _ = resolve_voice_id(
                args.voice, alias_map, presets, voice_aliases
            )
            speaker_id = resolve_speaker_id(presets[voice_id])
            voice_name = presets[voice_id]["name"]
            output = args.output or "{}-{}_tts.mp3".format(
                datetime.now().strftime("%Y%m%d-%H%M%S"),
                sanitize_filename_part(voice_name),
            )
            written = tts_synthesize(
                args.text,
                speaker_id,
                args.speed,
                args.volume,
                output,
                timeout=args.timeout,
            )
            result = {"success": True, "output": written, "voice": voice_name}

        print(json.dumps(result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (LycheeApiError, ValueError, OSError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
