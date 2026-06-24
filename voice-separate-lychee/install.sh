#!/usr/bin/env bash
set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$(basename "$SOURCE_DIR")"
SKILL_TARGET="$CLAUDE_HOME/skills/$NAME"
SHARED_SOURCE="$SOURCE_DIR/../shared"
DATA_SOURCE="$SOURCE_DIR/data"
LEGACY_COMMAND="$CLAUDE_HOME/commands/$NAME.md"

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python 3 not found" >&2
  exit 1
fi
PY_VERSION="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
  echo "ERROR: Python $PY_VERSION is too old; need 3.8+" >&2
  exit 1
fi

REQUIRED_PATHS=(
  "$SOURCE_DIR/SKILL.md"
  "$SOURCE_DIR/doctor.sh"
  "$SOURCE_DIR/doctor.ps1"
  "$SOURCE_DIR/install.sh"
  "$SOURCE_DIR/install.ps1"
  "$SOURCE_DIR/scripts"
  "$SHARED_SOURCE"
)
if [ "$NAME" = "tts-lychee" ]; then
  REQUIRED_PATHS+=("$DATA_SOURCE")
fi
for path in "${REQUIRED_PATHS[@]}"; do
  if [ ! -e "$path" ]; then
    echo "Required source path is missing: $path" >&2
    exit 1
  fi
done

rm -rf "$SKILL_TARGET/scripts" "$SKILL_TARGET/shared"
if [ "$NAME" = "tts-lychee" ]; then
  rm -rf "$SKILL_TARGET/data"
fi
mkdir -p "$SKILL_TARGET"
cp "$SOURCE_DIR/SKILL.md" "$SOURCE_DIR/doctor.sh" "$SOURCE_DIR/doctor.ps1" \
   "$SOURCE_DIR/install.sh" "$SOURCE_DIR/install.ps1" \
   "$SKILL_TARGET/"
cp -R "$SOURCE_DIR/scripts" "$SKILL_TARGET/"
cp -R "$SHARED_SOURCE" "$SKILL_TARGET/shared"
if [ "$NAME" = "tts-lychee" ]; then
  cp -R "$DATA_SOURCE" "$SKILL_TARGET/data"
fi
chmod +x "$SKILL_TARGET/install.sh" "$SKILL_TARGET/doctor.sh"

if [ -f "$LEGACY_COMMAND" ]; then
  rm -f "$LEGACY_COMMAND"
  echo "Removed legacy single-file command: $LEGACY_COMMAND"
fi

echo "Installed $NAME → $SKILL_TARGET"
echo "Set LYCHEE_API_KEY before use (or TTS_API_KEY as fallback). Get one from https://shanhaistudio.lycheeai.com.cn/"
