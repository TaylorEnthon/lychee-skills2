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

echo "== 检查 requests 依赖 =="
"$PYTHON" -c "import requests; print('requests', requests.__version__)"

echo "== 检查 API key =="
API_KEY="${LYCHEE_API_KEY:-}"
if [ -z "$API_KEY" ]; then
  echo "WARN: LYCHEE_API_KEY 未设置。运行 /lychee-set-key 配置。"
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
from auth import get_api_key, API_KEY_HEADER
from http_client import BASE_URL, post_multipart, get_json, poll_status
from ws_client import TTS_WS_URL
print('shared/ OK')
print('BASE_URL =', BASE_URL)
print('TTS_WS_URL =', TTS_WS_URL)
print('API_KEY_HEADER =', API_KEY_HEADER)
" "$SHARED"
fi

echo "== 检查 HTTP base 可达 =="
curl -fsS "https://shanhaistudio.lycheeai.com.cn/openapi/open/health" && echo
echo "== doctor OK =="
