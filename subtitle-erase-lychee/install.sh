#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="$(basename "$HERE")"
TARGET="$HOME/.claude/skills/$NAME"

mkdir -p "$TARGET/scripts"
cp "$HERE/SKILL.md" "$TARGET/"
cp "$HERE/scripts/"*.py "$TARGET/scripts/"
cp "$HERE/doctor.sh" "$HERE/doctor.ps1" "$HERE/install.sh" "$HERE/install.ps1" "$TARGET/"
mkdir -p "$TARGET/shared"
cp -r "$HERE/../shared/." "$TARGET/shared/"
echo "$NAME 安装到 $TARGET"
