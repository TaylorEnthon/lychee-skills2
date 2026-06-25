---
name: voice-infer-lychee
description: |
  调 lychee-openapi 的语音推理接口 /open/voice/zeroshot/infer，用克隆音色合成语音元数据。
  触发：用户说「用克隆的音色合成」「推理语音」「/voice-infer」「speaker_id 推理」。
  注意：本 skill 只返回算法元数据（duration_seconds 等），不返回音频二进制；
  要拿 MP3 用 tts-lychee skill。
---

# Voice Infer Lychee

使用克隆音色调用 lychee OpenAPI 语音推理接口，返回 `duration_seconds` 等算法元数据。

## 重要说明

本 HTTP 接口不返回 MP3 或其他音频二进制。如需获取 MP3，请使用 `tts-lychee` WebSocket skill。`duration_seconds` 是推理时长及计费依据。

## 从克隆到推理

1. 先用 `voice-clone-lychee` 上传参考音频。
2. 取克隆成功响应的 `request_id`。
3. 将该 `request_id` 作为本 skill 的 `--speaker-id`。

## 配置

设置环境变量 `LYCHEE_API_KEY`；未设置时兼容读取 `TTS_API_KEY`。

## 用法

```bash
python scripts/infer.py --text "你好。" --speaker-id "<voice-clone request_id>"
python scripts/infer.py --text "欢迎使用。" --speaker-id "<request_id>" --speed 1.1 --volume 0.9
python scripts/infer.py --text "测试。" --speaker-id "<request_id>" --audio reference.wav --ref-text "参考音频文本"
python scripts/infer.py --text "测试。" --speaker-id "<request_id>" --output infer-result.json
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
|---|---:|---|---|
| `--text` | 是 | 无 | 待推理文本，最多 3000 字符 |
| `--speaker-id` | 是 | 无 | `voice-clone` 返回的 `request_id` |
| `--speed` | 否 | `1.0` | 语速 |
| `--volume` | 否 | `1.0` | 音量 |
| `--sample-rate` | 否 | `44100` | 采样率 |
| `--ref-text` | 否 | 无 | 参考音频对应文本 |
| `--audio` | 否 | 无 | wav/mp3/m4a，不超过 10MB；提供时服务端先克隆并优先使用新 requestId |
| `--timeout` | 否 | `120` | HTTP 超时秒数 |
| `--output` | 否 | 无 | 将服务端完整 JSON 响应写入文件 |

## 输出

成功时输出类似：

```json
{"success": true, "code": 200, "duration_seconds": 3.45, "speaker_id": "<request_id>"}
```
