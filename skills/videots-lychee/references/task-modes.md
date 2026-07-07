# videots-lychee 任务模式备忘

## 6 种 mode

| `--action` | 用途 | 输入要求 |
|---|---|---|
| `translate` | 翻译 SRT,目标语言 | `--file` 或 `--tos-path` + `--target-language` |
| `back-translation` | 回译(查翻译质量) | `--file` + `--target-language`(原语言) |
| `retranslate` | 重译某几条 | `--file-original` + `--file-translated` + `--retranslation-items` |
| `list`(无 `--action`) | 列出当前用户全部任务 | 无 |
| `status`(无 `--action`) | 查询单个任务状态 | `--status-task-id` |
| `download` | 单独下载已完成任务 | `--status-task-id` + `--download-output` |

## `--retranslation-items` 格式

JSON 数组,只接 **SRT 段序号**(整数,从 1 起):

```bash
--retranslation-items '[1, 3, 7]'  # 只重译第 1、3、7 段
```

常见错误:传字符串 `"1,3,7"`(不带外层括号)→ 后端报 JSON 解析失败。

## 任务状态字段

不要按 `success` 字面找,接口规范是:

| 后端值 | 客户端行为 |
|---|---|
| `pending` | 继续轮询 |
| `processing` | 继续轮询 |
| `completed` | 成功,下载结果 |
| `failed` | 立即报错 |
| `error` | 立即报错 |

注意:本接口**没有** `success` 终态。多数 skill 用 `success` 表示成功,videots 用 `completed`。

## 失败恢复

`completed` 但 `download_url` 空时不要重试。检查:
1. 任务是否计费异常
2. 后端是否产出文件
3. 直接看后端任务详情

## 计费

`completed` 后按 token 异步扣费。**不要重试**同一任务,会产生额外费用。

## COS 上传(可选)

`--tos-path` 直接给 COS 路径,跳过 multipart 上传。需要在后端配过 COS 凭证。普通用户用 `--file` 多。
