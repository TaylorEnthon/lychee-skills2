---
name: tts-lychee
version: 1.0.0
description: |
  调 lychee-openapi 的 TTS WebSocket 接口，文本合成 MP3 音频。
  触发：用户说「合成语音」「TTS」「朗读这段」「/tts-lychee」「用温柔女声说」。
  不要用本 skill 列音色（用 /tts-lychee-list-voices）或预览匹配（用 /tts-lychee-preview-match）。
---

# TTS Lychee

通过 lychee TTS WebSocket 将文本合成为 MP3 音频。

## 配置

设置环境变量 `LYCHEE_API_KEY`；未设置时会兼容读取 `TTS_API_KEY`。运行 `/lychee-set-key` 可查看配置指引。

## 相关 slash command

- `/tts-lychee-list-voices` — 列出所有支持的音色
- `/tts-lychee-preview-match "<描述>"` — 预览自然语言描述匹配到哪个音色（不合成）

## 用法

```bash
python scripts/synthesize.py --text "你好，欢迎使用 lychee。"
python scripts/synthesize.py --text "今天天气不错。" --voice "温柔女声" --output weather.mp3
python scripts/synthesize.py --text "新闻播报。" --voice "播音男声" --speed 1.1 --volume 0.9
python scripts/list_voices.py
python scripts/preview_match.py "性感的女声"
```

## When to use

直接调一次合成(单条文本 → 一个 MP3)。批量合成、克隆音色后合成、多步转码,改用 `/lychee-workflow`。

## Process

1. 读环境变量 `LYCHEE_API_KEY`(fallback `TTS_API_KEY`)
2. 校验文本长度 ≤ 5000 + 音量/速度 > 0
3. 解析 `--voice`:别名 / preset / 关键词规则多层匹配(顺序见 `references/voicing-notes.md`)
4. base64 解 `preset.speaker_ref` 得后端 speaker_id
5. WS 连 `tts_synthesize()`,接收二进制 MP3
6. 写文件 + stdout JSON `{"success": true, "output": "...", "voice": "<name>"}`

## Red flags

- 文件大小 < 1KB:**失败**,WS 半截收到。
- 退出码 2 + stderr `step: tts`:API key 没设,**不要重试**,让用户跑 `/lychee-set-key`。
- 输出 JSON 没有 `voice` 字段:音色匹配错了(查 stderr 错误,通常是 `match_mode: exact` 不被命中)。
- `--list-voices` 没用:这个 flag 不存在,用户应该用 `/tts-lychee-list-voices` 或 `scripts/list_voices.py`。

## Verification

合成成功:

- 退出码 0
- stdout 末行是 `{"success": true, "output": "<mp3 路径>", "voice": "<音色名>"}`
- 输出文件存在 + 大小 > 1KB + 文件头是 `ID3` 或 `\xff\xfb` (MP3 magic)
- `mp3` 可用 `ffprobe`/`ffmpeg` 播放测试时长 > 0

快速验证命令:

```bash
# 跑 synthesis + 检查文件
python scripts/synthesize.py --text "test" --output ./test.mp3
ls -la ./test.mp3  # 应该 > 1KB
```

## 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--text` | 无 | 待合成文本，合成时必填，最多 5000 字符 |
| `--voice` | `默认女声` | 音色名或自然语言描述 |
| `--output` | `./<时间戳>-<voice>_tts.mp3` | MP3 输出路径 |
| `--speed` | `1.0` | 语速 |
| `--volume` | `1.0` | 音量 |
| `--timeout` | `90` | WebSocket 超时秒数 |

## 音色规则

音色解析依次尝试别名精确匹配、预设名、长别名 contains 匹配、`voice_aliases.json`、关键词规则和默认性别。`match_mode: exact` 的音色不参与 contains 匹配。

`默认女声`、`默认男声`、`性感女声`、`小男孩声音`、`云南话男声` 是必须存在且别名可解析的 5 个核心音色。

## 限制与输出

- 单次文本最多 5000 字符。
- 默认超时 90 秒；长文本可用 `--timeout` 调整。
- 成功时输出 `{"success": true, "output": "...", "voice": "默认女声"}`。
- 未设置 API key、WebSocket 或服务端错误时，在 stderr 输出可读 JSON 错误。
