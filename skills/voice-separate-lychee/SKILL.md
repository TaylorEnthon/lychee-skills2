---
name: voice-separate-lychee
version: 1.0.0
description: |
  调 lychee-openapi 的背景音与人声分离接口 /open/voice/separate，
  上传音频返回 vocals_url（人声）和 no_vocals_url（背景音）。
  触发：用户说「分离人声背景音」「人声分离」「/voice-separate」。
  异步任务：submit 后 client 本地轮询 status，命中 status=success 才返回。
---

# Voice Separate Lychee

上传音频和可选 SRT 字幕，提交背景音与人声分离任务并轮询结果。

## 用法

```bash
python scripts/separate.py --file ./song.wav
python scripts/separate.py --file ./video.m4a --srt ./video.srt
python scripts/separate.py --file ./song.mp3 --interval 5 --timeout 600
python scripts/separate.py --file ./song.wav --no-wait
python scripts/separate.py --file ./song.wav --output ./result.json
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--file` | 是 | - | 待分离的音频文件 |
| `--srt` | 否 | - | SRT 字幕文件，用于 OCR 时间戳辅助 |
| `--interval` | 否 | `3` | 状态轮询间隔，单位秒 |
| `--timeout` | 否 | `300` | 提交和轮询的最长等待时间，单位秒 |
| `--no-wait` | 否 | 关闭 | 提交后立即返回 `request_id`，不轮询 |
| `--output` | 否 | - | 将提交响应或最终状态完整写入 JSON 文件 |

## 文件限制

- 音频格式：wav、mp3、m4a、aac、flac。
- 音频大小不超过 50MB，时长不超过 600 秒。
- 可选 SRT 文件大小不超过 1MB。

## 响应与轮询

提交成功会得到 `request_id`、`task_name`、`audio_path` 等字段。默认每隔 `--interval` 秒查询一次状态；`pending`、`running` 会继续等待，只有 `status=success` 才视为成功，`status=failed` 会立即报错。

成功后输出：

- `vocals_url`：完整的人声音频下载 URL。
- `no_vocals_url`：完整的背景音下载 URL。

服务端成功但没有 `result` 时，两个 URL 输出为空字符串。使用 `--no-wait` 时只提交任务，之后需自行用返回的 `request_id` 查询 `/open/voice/separate/status`。

## 环境变量与错误

设置 `LYCHEE_API_KEY`，也兼容 `TTS_API_KEY`。运行 `doctor.sh` 或 `doctor.ps1` 可检查 Python、`requests`、共享客户端和 HTTP 服务。

文件无效或参数错误返回退出码 2；API、网络、任务失败或轮询超时返回退出码 1。分离任务可能耗时较长，请按需增大 `--timeout`。
