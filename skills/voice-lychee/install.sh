#!/usr/bin/env bash
set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$(basename "$SOURCE_DIR")"
TARGET="$CLAUDE_HOME/skills/$NAME"
REPO_ROOT="$(cd "$SOURCE_DIR/../.." && pwd)"

for path in SKILL.md doctor.sh doctor.ps1 install.sh install.ps1 scripts references data; do
  [ -e "$SOURCE_DIR/$path" ] || { echo "Required source path is missing: $SOURCE_DIR/$path" >&2; exit 1; }
done
[ -d "$REPO_ROOT/shared" ] || { echo "Required source path is missing: $REPO_ROOT/shared" >&2; exit 1; }

rm -rf "$TARGET/scripts" "$TARGET/shared" "$TARGET/references" "$TARGET/data"
mkdir -p "$TARGET"
cp "$SOURCE_DIR/SKILL.md" "$SOURCE_DIR/doctor.sh" "$SOURCE_DIR/doctor.ps1" "$SOURCE_DIR/install.sh" "$SOURCE_DIR/install.ps1" "$TARGET/"
cp -R "$SOURCE_DIR/scripts" "$SOURCE_DIR/references" "$SOURCE_DIR/data" "$TARGET/"
cp -R "$REPO_ROOT/shared" "$TARGET/shared"
chmod +x "$TARGET/install.sh" "$TARGET/doctor.sh"
echo "Installed $NAME → $TARGET"

