#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="$(basename "$HERE")"
TARGET="$HOME/.claude/skills/$NAME"

mkdir -p "$TARGET/scripts" "$TARGET/shared" "$TARGET/data"
cp "$HERE/SKILL.md" "$TARGET/"
cp "$HERE/scripts/"*.py "$TARGET/scripts/"
cp "$HERE/doctor.sh" "$HERE/doctor.ps1" "$HERE/install.sh" "$HERE/install.ps1" "$TARGET/"
cp -r "$HERE/../shared/." "$TARGET/shared/"
cp -r "$HERE/data/." "$TARGET/data/"
echo "$NAME 安装到 $TARGET"
