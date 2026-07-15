---
name: voice-lychee
version: 1.0.0
description: 调 lychee-openapi 的同步配音接口 /open/voice/lychee-voice，以文本、公共音色、图片或临时参考音频生成完整音频。触发：用户说「合成配音」「AI 配音」「文本转语音」「用音色 X 读」「多音色对话」「图片转语音」「临时参考音频生成」「voice generation」「text to speech」「AI voice」「image to voice」「multi-voice dialogue」「/voice-lychee」。
---

# Voice Lychee

调用同步 HTTP 配音接口并下载完整音频。异步流式 TTS 用 `/tts-lychee`；音色克隆用 `/voice-clone-lychee`；音色推理用 `/voice-infer-lychee`。

## 配置

设置 `LYCHEE_API_KEY`；未设置时兼容 `TTS_API_KEY`。

## 用法

```bash
python scripts/synthesize.py --text "你好" --output ./hello.wav
python scripts/synthesize.py --text "{{voice:1}}你好" --voice-ids 1 --output ./voice.wav
python scripts/synthesize.py --text "@音频1你好" --audio-urls https://example.com/ref.wav --output ./temp.wav
python scripts/synthesize.py --text "你好" --image ./face.png --format mp3 --output ./image.mp3
python scripts/list_voices.py
python scripts/list_tasks.py --status success
```

## When to use

- 直接把文字同步生成完整音频。
- 使用 1–3 个公共音色生成单人或多人对白。
- 使用一张图片或 1–3 条临时音频作为参考。
- 查询公共音色或当前 API Key 对应用户的配音历史。

## Process

1. 有 `--image` 时走 `image` multipart；否则依次识别 `--audio-urls`、`--voice-ids`，都没有则走 `text` JSON。
2. 调 `/open/voice/lychee-voice`，读取同步响应的 `audio_url`。
3. 下载音频到 `--output`；未指定时生成时间戳文件名。
4. stdout 输出单行 JSON；音色列表例外，输出 pretty-print JSON。

## 参数

| 参数 | 说明 |
| --- | --- |
| `--text` | 必填，最多 3000 字符 |
| `--voice-ids` | 公共音色 ID，1–3 个；可重复传或逗号分隔 |
| `--audio-urls` | HTTP/HTTPS URL、纯 Base64 或 Data URL，1–3 个 |
| `--image` | jpeg/png/webp 图片 |
| `--format` | `wav`（默认）/`mp3`/`pcm`/`ogg_opus` |
| `--sample-rate` | 8000/16000/24000/32000/44100/48000 |
| `--speech-rate` | -50..100 整数 |
| `--loudness-rate` | -50..100 整数 |
| `--pitch-rate` | -12..12 整数 |
| `--enable-subtitle` | 请求字幕数据；CLI 仍只输出音频摘要 |
| `--output` | 本地音频路径 |
| `--timeout` | 请求及下载超时秒数，默认 120 |

## Red flags

- `--image`、`--audio-urls`、`--voice-ids` 互斥。
- `voices` 模式的 `{{voice:N}}` 中 N 是 `voice_ids` 的 1-based 下标，不是音色 ID。
- `audio_url` 模式直接写 `@音频N`，服务端不转换 `{{voice:N}}`。
- 纯文本模式禁止 `{{voice:N}}`；图片模式不处理 mention。
- 临时音频不会沉淀到音色池；需长期复用时先调用 voice-clone。

## Verification

成功时退出码为 0，stdout 包含 `success=true`、本地 `output`、`duration_ms`、`audio_url`，且本地文件存在。参数或本地文件错误退出 2；API、网络或下载失败退出 1。

更多规则见 `references/mode-decision-tree.md`、`references/mention-rules.md`、`references/error-codes.md`。

