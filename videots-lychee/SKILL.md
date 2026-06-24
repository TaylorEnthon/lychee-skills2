---
name: videots-lychee
description: |
  调 lychee-openapi 的 SRT 字幕翻译接口 /open/videots/*，支持 translate / retranslate / back-translation。
  触发：用户说「翻译字幕」「/videots」「重译这段台词」「回译字幕」。
  异步任务：提交后 client 本地轮询 status，命中 status=completed 才返回。
  状态字段：pending / processing / completed / failed / error（无 success）。
---

# VideoTS Lychee

统一提交字幕翻译、选择性重译和回译任务，并支持状态、任务列表和结果下载。

## 用法

```bash
python scripts/translate.py --action translate --file ./source.srt --target-language en
python scripts/translate.py --action retranslate --file-original ./source.srt --file-translated ./translated.srt --target-language en --retranslation-items '[1, 3]'
python scripts/translate.py --action back-translation --file ./translated.srt --target-language zh
python scripts/translate.py --action translate --tos-path path/to/source.srt --target-language ja --no-wait
python scripts/translate.py --tasks
python scripts/translate.py --status-task-id TASK_ID
python scripts/translate.py --action translate --file ./source.srt --target-language en --download-output ./translated.srt
```

## 参数

| 参数 | 说明 |
| --- | --- |
| `--action` | 提交时必填：translate / retranslate / back-translation |
| `--file` / `--tos-path` | translate、back-translation 的 SRT 来源 |
| `--file-original` / `--file-translated` | retranslate 的一对本地 SRT |
| `--tos-path-original` / `--tos-path-translated` | retranslate 的一对 TOS 路径 |
| `--target-language` | 提交时必填的目标语言，如 en、zh、ja |
| `--user-prompt` | 可选翻译提示词 |
| `--retranslation-items` | retranslate 必填的 JSON 字符串 |
| `--mode` | 提交模式，默认 direct |
| `--interval` | 轮询间隔秒数，默认 5 |
| `--timeout` | 最长等待秒数，默认 600 |
| `--download-output` | 完成后下载 SRT 到指定路径 |
| `--tasks` | 列出当前用户全部任务，无需 action |
| `--status-task-id` | 查询指定任务，无需 action |
| `--no-wait` | 提交后立即返回 task_id |
| `--output` | 将完整 JSON 响应写入文件 |

## 文件与状态

- 本地文件必须为 SRT，单个文件不超过 1MB。
- 中间状态：`pending`、`processing`。
- 成功终态：`completed`；失败终态：`failed`、`error`。本接口没有 `success` 状态。
- 服务端在 completed 后按 token 异步扣费，客户端不计算费用。

## 下载

使用 `--download-output` 时，客户端调用 `/open/videots/download`。接口直接返回二进制时写入文件；返回 JSON `download_url` 时继续下载实际文件。目标目录会自动创建。

设置 `LYCHEE_API_KEY`，也兼容 `TTS_API_KEY`。文件或参数错误返回退出码 2；API、网络、任务失败或轮询超时返回退出码 1。
