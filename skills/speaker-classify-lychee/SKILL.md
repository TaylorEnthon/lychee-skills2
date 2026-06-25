---
name: speaker-classify-lychee
description: |
  调 lychee-openapi 的公共说话人分类接口 /open/speaker-classify/*，
  上传音频返回说话人分段（每段：spk / content / start / end）。
  触发：用户说「分清谁说的」「说话人分类」「谁说了什么」「/speaker-classify」。
  异步任务：submit 后 client 本地轮询 status，命中 status=success 才返回。
---

# Speaker Classify Lychee

上传音频到公共说话人分类接口，提交异步任务后在本地轮询，返回每个说话人的识别分段。

## 用法

```bash
python scripts/classify.py --file ./meeting.wav
python scripts/classify.py --file ./meeting.mp3 --interval 5 --timeout 600
python scripts/classify.py --file ./meeting.m4a --no-wait
python scripts/classify.py --file ./meeting.wav --output ./result.json
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--file` | 是 | - | 待分类的音频文件 |
| `--interval` | 否 | `3` | 状态轮询间隔，单位秒 |
| `--timeout` | 否 | `300` | 提交和轮询的最长等待时间，单位秒 |
| `--no-wait` | 否 | 关闭 | 提交后立即返回 `request_id`，不轮询 |
| `--output` | 否 | - | 将提交响应或最终状态完整写入 JSON 文件 |

## 文件限制

- 接口契约覆盖 24 种常见音频格式；客户端按服务端当前白名单校验，包括 wav、mp3、m4a、aac、flac、ogg、opus、wma 等。
- 文件大小不超过 50MB。
- 音频时长为 1 秒至 10 分钟。

## 响应与轮询

提交成功会得到 `request_id`。默认每隔 `--interval` 秒查询一次状态；`pending`、`running` 会继续等待，只有 `status=success` 才视为成功，`status=error` 会立即报错。

成功响应中的 `spk_result` 是分段数组，每段包含：

- `spk`：说话人标识。
- `content`：该段识别文本。
- `start` / `end`：该段起止时间。
- `asr_duration`：ASR 处理时长。
- `duration_ms`：任务耗时（毫秒）。

使用 `--no-wait` 时只提交任务；之后需自行用返回的 `request_id` 查询 `/open/speaker-classify/status`。

## 环境变量与错误

设置 `LYCHEE_API_KEY`，也兼容 `TTS_API_KEY`。运行 `doctor.sh` 或 `doctor.ps1` 可检查 Python、`requests`、共享客户端和 HTTP 服务。

文件无效或参数错误返回退出码 2；API、网络、任务失败或轮询超时返回退出码 1。长音频可能超过默认 300 秒，请按需增大 `--timeout`。
