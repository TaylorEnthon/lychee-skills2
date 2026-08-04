---
name: videots-lychee
version: 2.0.0
description: |
  调 lychee-openapi 的 SRT 字幕翻译接口 /open/videots/translate（对外唯一可用）。
  触发：用户说「翻译字幕」「/videots」。
  异步任务：提交后 client 本地轮询 status，命中 status=completed 才返回。
  输入方式二选一：本地 SRT 文件（--file）或公网 SRT URL（--file-url）。
  状态字段：pending / processing / completed / failed / error（无 success）。
---

# VideoTS Lychee

把 SRT 字幕翻译成另一种语言。用户只需要用自然语言告诉 agent，agent 负责全流程。

## 用户场景

**Case 1** —— 用户上传一个 `.srt` 到对话里，说："把这个字幕翻成英文"
> agent 落盘为临时文件，跑 `translate --file <tmp.srt> --target-language en`，翻译完把结果文件 / 内容回给用户

**Case 2** —— 用户贴一个链接："把 https://subs.example.com/s01e03.srt 翻译成中文"
> agent 直接拿链接跑 `translate --file-url <url> --target-language zh`，翻译完回给用户

## 用法

```bash
python scripts/translate.py --action translate --file ./source.srt --target-language en
python scripts/translate.py --action translate --file-url https://example.com/input.srt --target-language en
python scripts/translate.py --action translate --file ./source.srt --target-language ja --download-output ./out.srt
python scripts/translate.py --action translate --file-url https://example.com/in.srt --target-language zh --no-wait
python scripts/translate.py --status-task-id TASK_ID
python scripts/translate.py --tasks
```

## 参数

| 参数 | 说明 |
| --- | --- |
| `--action` | 提交时必填：translate |
| `--file` | 本地 SRT 文件路径，与 `--file-url` 互斥 |
| `--file-url` | 公网 HTTP/HTTPS SRT 链接（≤2048 字符），与 `--file` 互斥 |
| `--target-language` | 提交时必填的目标语言，如 en、zh、ja |
| `--user-prompt` | 可选翻译提示词，默认空串 |
| `--interval` | 轮询间隔秒数，默认 5 |
| `--timeout` | 最长等待秒数，默认 600 |
| `--download-output` | 完成后下载 SRT 到指定路径 |
| `--tasks` | 列出当前用户全部任务，无需 action |
| `--status-task-id` | 查询指定任务，无需 action |
| `--no-wait` | 提交后立即返回 task_id |
| `--output` | 将完整 JSON 响应写入文件 |

## 文件与 URL

- `--file` 必须是 ≤1MB 的 `.srt` 文件；文件不存在 / 后缀不对 / 超限都会被参数校验拦下。
- `--file-url` 必须以 `http://` 或 `https://` 开头，长度 ≤2048 字符。后端会拉取这个 URL。
- 两者**必须二选一**，不能同时给也不能都不给。

## 状态

- 中间状态：`pending`、`processing`。
- 成功终态：`completed`；失败终态：`failed`、`error`。本接口**没有** `success`。
- 服务端在 `completed` 后按 token 异步扣费，客户端不计算费用。

## 下载

使用 `--download-output` 时，客户端调用 `/open/videots/download`。接口直接返回二进制时写入文件；返回 JSON `download_url` 时继续下载实际文件。目标目录会自动创建。

设置 `LYCHEE_API_KEY`。文件或参数错误返回退出码 2；API、网络、任务失败或轮询超时返回退出码 1。

## When to use

SRT 字幕翻译成另一种语言。比人工翻快得多，适合大批量字幕。

## Process

1. 读 `--action`（默认 translate；或 `--tasks` / `--status-task-id` 走查询）
2. 校验输入：必须提供 `--file` 或 `--file-url` 其中一个，加上 `--target-language`
3. submit 走 multipart 到 `/open/videots/translate`，返 `task_id`；其他动作走 GET endpoints
4. submit 默认轮询 `status=completed` 才返，可选 `--download-output` 落盘
5. stdout JSON，失败抛 `LycheeApiError`

## Red flags

- `--file` 与 `--file-url` 都给 / 都不给 → 参数校验拒绝（exit 2）
- `--file-url` 不是 `http(s)://` 开头 → 参数校验拒绝
- `completed` 终态但 `download_url` 空：任务成功但后端没产出文件，**别重试**，看后端任务详情
- 退出码 1 + 401：API key 无效

## Verification

成功：

- exit 0
- stdout `{"success": true, "task_id": "...", "status": "completed", "download_url": "..."}`
- `--download-output ./out.srt` 时文件存在 + 是 SRT 格式（序号 + 时间码 + 文本）

快速验证（本地文件）：

```bash
python scripts/translate.py --action translate \
  --file ./in.srt --target-language en --download-output ./out.srt
head -5 ./out.srt  # 应该是 SRT 格式
```

快速验证（URL）：

```bash
python scripts/translate.py --action translate \
  --file-url https://example.com/sample.srt --target-language en --no-wait
```