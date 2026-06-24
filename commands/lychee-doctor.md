---
description: 一键运行所有已装 lychee-* skill 的 doctor 自检
---

运行 `~/.claude/skills/` 下所有 `*-lychee` skill 的 `doctor.sh`（或 `doctor.ps1`）脚本并汇总结果。

## 行为

- 列出所有 `~/.claude/skills/*-lychee/` 子目录
- 对每个存在的子目录，运行 `bash doctor.sh`（Windows 上跑 `pwsh doctor.ps1`）
- 输出每个 skill 的 doctor 结果
- 统计 OK / WARN / ERROR 数量

## 期望输出

```text
asr-lychee: OK
tts-lychee: OK
voice-clone-lychee: OK
voice-infer-lychee: OK
...
总结：9 OK / 0 ERROR
```

如果某个 skill 显示 ERROR，看对应的输出末尾 ERROR 行就知道是哪一项失败。
