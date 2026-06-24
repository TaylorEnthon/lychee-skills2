#!/usr/bin/env python3
"""预览自然语言描述会匹配到哪个 tts-lychee 音色。"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts_client import configure_stdio, preview_match


if __name__ == "__main__":
    configure_stdio()
    parser = argparse.ArgumentParser(description="预览 tts-lychee 音色匹配结果，不合成音频。")
    parser.add_argument("voice", help="音色名或自然语言描述")
    args = parser.parse_args()
    print(json.dumps(preview_match(args.voice), ensure_ascii=False, indent=2))
