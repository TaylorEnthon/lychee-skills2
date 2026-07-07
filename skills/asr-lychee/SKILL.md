---
name: asr-lychee
version: 1.0.0
description: |
  调 lychee-openapi 的语音识别接口 /open/asr，上传音频文件返回识别文本。
  触发：用户说「转录音频」「把这段音频转文字」「识别这段语音」「ASR」「/asr-lychee」。
  不要用此 skill 做实时流式识别（流式用 WebSocket；本 skill 走 HTTP multipart）。
---

# ASR Lychee

上传本地音频到 lychee OpenAPI，返回语音识别文本。

## 配置

设置环境变量 `LYCHEE_API_KEY`；为了兼容旧配置，未设置时会尝试 `TTS_API_KEY`。

## 用法

```bash
python scripts/asr.py --file /path/to/audio.wav
python scripts/asr.py --file audio.mp3 --language zh-CN --output transcript.txt
python scripts/asr.py --file audio.wav --debug --output result.json
```

## 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--file` | 是 | 音频文件，支持 mp3、wav、m4a |
| `--language` | 否 | 语言代码，如 `zh-CN`、`en-US` |
| `--output` | 否 | 输出文件；默认输出到 stdout |
| `--debug` | 否 | 输出完整 data JSON，而不是纯文本 |
| `--timeout` | 否 | HTTP 超时秒数，默认 60 |

## 文件限制

- 大小不超过 2GB。
- 时长必须在 10 秒至 60 分钟之间。
- 超出限制的文件会被服务端拒绝。

## 输出与错误

默认仅打印识别文本，或将文本写入 `--output` 指定的文件。使用 `--debug` 时输出完整 data JSON。

未设置 API key、文件无效、网络失败或服务端返回错误时，命令会在 stderr 输出可读错误信息。

## When to use

上传一段音频让人工转写 / 听写 / 自动转文字。已有 SRT 字幕、用专门的说话人识别、批量处理等场景不要用本 skill。

## Process

1. 读 `--file`,校验存在 + 后缀白名单 + 大小 ≤ 2GB + 时长 10s-60min
2. 读 `LYCHEE_API_KEY`(fallback `TTS_API_KEY`),初始化 `http_client`
3. multipart POST 到 `/open/asr`,带 `language` form 字段
4. 解包 `data.text`,stdout 直接打印(无 `success` 包装);`--debug` 时打印完整 data JSON

## Red flags

- `--debug` 输出但 stdout 没有 `text` 字段:后端空文本,可能音频静音或后端 bug
- 退出码 2 + stderr "文件不存在":`--file` 路径错
- 退出码 2 + stderr "时长":后端拒绝,可能是格式不支持或时长超限
- 退出码 1:网络或服务端,稍后重试

## Verification

成功:

- 退出码 0
- stdout 是识别文本(无 JSON 包装)
- `--output file.txt` 时文件存在 + 大小 > 0 + 是 UTF-8 文本

快速验证:

```bash
python scripts/asr.py --file ./audio.mp3 --output ./out.txt
cat ./out.txt   # 应该是识别的中文/英文
```
