#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

echo "== 安装所有 lychee skills =="
mkdir -p "$SKILLS_DIR"
for skill_dir in "$HERE"/*-lychee; do
    [ -d "$skill_dir" ] || continue
    installer="$skill_dir/install.sh"
    [ -f "$installer" ] || continue
    echo "  -> $(basename "$skill_dir")"
    if [ -x "$installer" ]; then
        "$installer" || echo "WARN: $(basename "$skill_dir") install 失败"
    else
        bash "$installer" || echo "WARN: $(basename "$skill_dir") install 失败"
    fi
done

echo "== 安装跨 skill commands =="
mkdir -p "$HOME/.claude/commands"
for cmd in "$HERE"/commands/*.md; do
    [ -f "$cmd" ] || continue
    cp "$cmd" "$HOME/.claude/commands/"
    echo "  -> $(basename "$cmd")"
done

echo "== 完成 =="
echo "已安装：9 个 skill + 2 个跨 skill command"
echo "运行 /lychee-doctor 自检；运行 /lychee-set-key 设置 API key"
