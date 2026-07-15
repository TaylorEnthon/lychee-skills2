#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
[ -n "$PYTHON" ] || { echo "ERROR: 未找到 Python 3"; exit 1; }
"$PYTHON" -c "import requests; print('requests', requests.__version__)"

if [ -z "${LYCHEE_API_KEY:-${TTS_API_KEY:-}}" ]; then
  echo "WARN: LYCHEE_API_KEY 未设置（兼容 TTS_API_KEY）。运行 /lychee-set-key 配置。"
else
  echo "OK: API key 已设置"
fi

"$PYTHON" -m py_compile "$HERE/scripts/synthesize.py" "$HERE/scripts/list_voices.py" "$HERE/scripts/list_tasks.py"
"$PYTHON" -c "
import json, pathlib, sys
from datetime import datetime, timedelta, timezone
p = pathlib.Path(sys.argv[1])
if not p.exists():
    print('WARN: 音色缓存不存在；需要时运行 list_voices.py')
else:
    t = datetime.fromisoformat(json.loads(p.read_text(encoding='utf-8'))['updated_at'].replace('Z', '+00:00'))
    print('WARN: 音色缓存已过期；运行 list_voices.py --refresh' if datetime.now(timezone.utc)-t >= timedelta(hours=24) else 'OK: 音色缓存有效')
" "$HERE/data/voices-cache.json"
echo "== doctor OK =="
