---
description: 按预定义 recipe 执行多 skill 组合
---

按 `docs/workflows/` 中的 recipe 串行执行多个 lychee skill，并把每步中间产物写到 `~/.claude/lychee-workflows/<recipe>/`。

## 行为

- 先读 `docs/workflows/README.md` 索引，确认用户传入的 recipe name。
- 再读对应 recipe 文件，例如 `docs/workflows/short-drama-translate.md`。
- 根据 recipe 的步骤顺序调用相关 skill；不要写 Python 编排代码，也不要创建临时脚本。
- 每一步完成后把原始结果或摘要写到 `~/.claude/lychee-workflows/<recipe>/<NN>-<step-name>.<ext>`。
- 每步完成后进入 checkpoint 模式，向用户汇报本步产物路径，并询问是否继续下一步。
- 如果步骤失败，先检查上一步 JSON 是否已存在；可从最近成功的 checkpoint 继续。
- 自动恢复只依赖对话上下文和落盘产物，不维护 YAML、数据库或隐藏状态。

## 触发示例

```text
/lychee-workflow short-drama-translate ./input.mp4
```

```text
/lychee-workflow voice-replicate ./ref.wav --voice-name "我的克隆"
```

```text
/lychee-workflow multi-speaker-dub ./episode.mp4 --refs ./refs/
```

## 期望输出

```text
short-drama-translate
1/5 videots-lychee: OK -> ~/.claude/lychee-workflows/short-drama-translate/01-subtitle.srt
2/5 voice-clone-lychee: OK -> ~/.claude/lychee-workflows/short-drama-translate/02-clone.json
checkpoint: 是否继续 3/5 voice-infer-lychee?
...
完成：~/.claude/lychee-workflows/short-drama-translate/05-result.mp4
```

失败时输出失败步骤、错误摘要、可续跑的上一步产物路径。
