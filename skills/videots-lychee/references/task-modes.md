# videots-lychee 任务模式备忘

## 4 种 mode

| 模式 | 触发 | 输入要求 |
|---|---|---|
| `translate`（`--action translate`） | 翻译 SRT 到目标语言 | `--file` 或 `--file-url` + `--target-language` |
| `status`（`--status-task-id`） | 查询单个任务状态 | `--status-task-id` |
| `list`（`--tasks`） | 列出当前用户全部任务 | 无 |
| `download`（隐含在 `translate --download-output`） | 下载已完成任务的结果 | 提交时带 `--download-output` |

`retranslate` / `back-translation` 不再对外开放，本 skill 不再支持。

## 输入方式

`--file` 与 `--file-url` **必须二选一**，不能同时给也不能都不给：

| 参数 | 适用 | 校验 |
|---|---|---|
| `--file` | 本地 SRT | 文件存在 + `.srt` 后缀 + ≤1MB |
| `--file-url` | 公网 SRT | `http(s)://` 开头 + ≤2048 字符 |

常见错误：传 `--tos-path`（已废弃）或 `--retranslation-items`（retranslate 接口不再可用）。

## 任务状态字段

不要按 `success` 字面找，接口规范是：

| 后端值 | 客户端行为 |
|---|---|
| `pending` | 继续轮询 |
| `processing` | 继续轮询 |
| `completed` | 成功，下载结果 |
| `failed` | 立即报错 |
| `error` | 立即报错 |

注意：本接口**没有** `success` 终态。多数 skill 用 `success` 表示成功，videots 用 `completed`。

## 失败恢复

`completed` 但 `download_url` 空时不要重试。检查：

1. 任务是否计费异常
2. 后端是否产出文件
3. 直接看后端任务详情

## 计费

`completed` 后按 token 异步扣费。**不要重试**同一任务，会产生额外费用。