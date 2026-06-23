#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SHARED="$HERE/shared"
if [ ! -d "$SHARED" ] && [ -d "$HERE/../shared" ]; then
  SHARED="$HERE/../shared"
fi

echo "== 检查 Python =="
if python3 --version >/dev/null 2>&1; then
  PYTHON=python3
elif python --version >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: 未找到可用的 Python 3"
  exit 1
fi
"$PYTHON" --version

echo "== 检查 websocket-client 依赖 =="
"$PYTHON" -c "import websocket; print('websocket-client', websocket.__version__)"

echo "== 检查 API key =="
API_KEY="${LYCHEE_API_KEY:-${TTS_API_KEY:-}}"
if [ -z "$API_KEY" ]; then
  echo "WARN: LYCHEE_API_KEY 未设置（兼容 TTS_API_KEY 也没有）。运行 /lychee-set-key 配置。"
else
  echo "OK: API key 已设置（前 8 位）=${API_KEY:0:8}..."
fi

echo "== 检查 shared/ 能 import =="
if [ ! -d "$SHARED" ]; then
  echo "WARN: shared/ 未安装，请重新运行当前 skill 的 install"
else
  "$PYTHON" -c "
import sys
sys.path.insert(0, sys.argv[1])
from ws_client import TTS_WS_URL, tts_synthesize
expected = 'wss://shanhaistudio.lycheeai.com.cn/openapi/tts/ws_binary/v2'
if TTS_WS_URL != expected:
    raise SystemExit('TTS_WS_URL mismatch: ' + TTS_WS_URL)
print('shared/ OK')
print('TTS_WS_URL =', TTS_WS_URL)
" "$SHARED"
fi

echo "== 检查 data/ 与音色规则 =="
"$PYTHON" -c "
import sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from tts_client import REQUIRED_VOICES, load_voice_data, resolve_voice_id
alias_map, presets, voice_aliases = load_voice_data()
print('data JSON OK:', len(presets), 'presets,', len(alias_map), 'aliases,', len(voice_aliases), 'voice groups')
print('required voices OK:', ', '.join(REQUIRED_VOICES))
print('required aliases OK:', ', '.join(REQUIRED_VOICES))
voice_id, used_default, matched = resolve_voice_id('性感的女声', alias_map, presets, voice_aliases)
if voice_id != '性感女声' or used_default:
    raise SystemExit('音色匹配失败: ' + voice_id)
print('voice matching OK: 性感的女声 ->', voice_id, '(matched:', matched + ')')
" "$SHARED" "$HERE/scripts"

echo "== doctor OK =="
