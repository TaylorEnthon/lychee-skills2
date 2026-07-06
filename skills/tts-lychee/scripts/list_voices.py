#!/usr/bin/env python3
"""列出 tts-lychee 支持的全部音色。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthesize import configure_stdio, list_voices


if __name__ == "__main__":
    configure_stdio()
    print(json.dumps(list_voices(), ensure_ascii=False, indent=2))
