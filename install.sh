#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

echo "== 安装所有 lychee skills =="
mkdir -p "$SKILLS_DIR"
for skill_dir in "$HERE"/skills/*-lychee; do
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

if [ -d "$HERE/.githooks" ] && [ -d "$HERE/.git" ]; then
    mkdir -p "$HERE/.git/hooks"
    cp "$HERE/.githooks/pre-commit" "$HERE/.git/hooks/pre-commit"
    chmod +x "$HERE/.git/hooks/pre-commit"
    echo "Installed pre-commit hook to $HERE/.git/hooks/pre-commit"
fi

echo "== 完成 =="
echo "已安装：10 个 skill + 2 个跨 skill command"
echo "运行 /lychee-doctor 自检；运行 /lychee-set-key 设置 API key"
