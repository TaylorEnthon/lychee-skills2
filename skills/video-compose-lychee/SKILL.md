---
name: video-compose-lychee
version: 1.0.0
description: |
  调 lychee-openapi 的视频压制合成接口 /open/video-compose/tasks，异步处理视频、音频和字幕并返回下载地址。
  触发：用户说「视频压制」「音频合成」「字幕压制」「video-compose」。
  异步任务：submit 后 client 本地轮询 status，命中 status=completed 才返回。
---

# Video Compose Lychee

上传 mp4 视频，可选叠加音频和 SRT 字幕，提交到 lychee OpenAPI 后默认轮询到完成并返回结果下载地址。适合纯视频压制、音频合成、字幕压制，以及音频加字幕的组合流程。

## 用法

```bash
python scripts/compose.py --video-file ./video.mp4
python scripts/compose.py --video-file ./video.mp4 --subtitle-file ./subtitle.srt --target-language th
python scripts/compose.py --video-file ./video.mp4 --audio-file ./dub.mp3 --subtitle-file ./subtitle.srt --target-language en --download-output ./result.mp4
```

## 参数

| 参数 | 必填 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `--video-file` | 是 | Path | - | mp4 视频文件，最大 1GB |
| `--audio-file` | 否 | Path | - | mp3/wav/m4a 音频文件，最大 200MB |
| `--subtitle-file` | 否 | Path | - | SRT 字幕文件，最大 10MB |
| `--target-language` | 传字幕时是 | str | - | 字幕目标语言，如 th/ar/ko/vi/en |
| `--subtitle-x` | 否 | int | - | 字幕区域左上角 X 坐标，需和其余 4 个字幕位置参数同时传 |
| `--subtitle-y` | 否 | int | - | 字幕区域左上角 Y 坐标，需和其余 4 个字幕位置参数同时传 |
| `--subtitle-font-size` | 否 | int | - | 字幕字号，范围 12-96，需和其余 4 个字幕位置参数同时传 |
| `--coordinate-width` | 否 | int | - | 坐标来源画布宽度，需和其余 4 个字幕位置参数同时传 |
| `--coordinate-height` | 否 | int | - | 坐标来源画布高度，需和其余 4 个字幕位置参数同时传 |
| `--interval` | 否 | float | `5.0` | 结果轮询间隔，单位秒 |
| `--timeout` | 否 | float | `600.0` | HTTP 请求与最长等待时间，单位秒 |
| `--no-wait` | 否 | flag | 关闭 | 提交后立即返回 `task_id`，不轮询 |
| `--download-output` | 否 | Path | - | 完成后将 `resultPath` 下载到本地文件 |
| `--output` | 否 | Path | - | 将完整 JSON 响应写入文件 |

## 输出

成功：

```json
{"success": true, "task_id": "task_123", "status": "completed", "result_path": "https://example.com/result.mp4"}
```

提交未轮询：

```json
{"success": true, "task_id": "task_123", "waiting": false}
```

失败：

```json
{"success": false, "error": "[500] video compose failed (request_id=task_123)"}
```

## 退出码

- `0`：提交成功，或轮询到完成。
- `1`：API、网络、任务失败或轮询超时。
- `2`：API Key、参数或本地文件错误。

## 状态与错误

提交成功会得到 `task_id`。默认每隔 `--interval` 秒查询 `/open/video-compose/status`；`pending` 会继续等待，`completed` 视为成功，`failed` 会用服务端 `errorMessage` 报错。

常见错误：

```text
传 --subtitle-file 时必须同时传 --target-language
字幕位置参数必须 5 个同时传；缺少: --coordinate-height
视频文件格式不支持；仅支持 .mp4
```

设置 `LYCHEE_API_KEY`，也兼容 `TTS_API_KEY`。
