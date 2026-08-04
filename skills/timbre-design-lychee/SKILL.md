---
name: timbre-design-lychee
version: 3.0.0
description: |
  调 lychee-openapi 的音色设计接口 /open/timbre-design/generate-mimo，用自然语言描述生成试听音色。
  触发：用户说「设计音色」「生成新音色」「描述一个声音」「/timbre-design」「mimo」。
  一次同步返回 audioUrl（试听音频 URL），不需要客户端轮询。
---

# Timbre Design Lychee

用一段话描述想要的音色，拿到一段可下载的试听音频。

## 用户场景

> 默认**不润色**。用户提到"润色""改得顺口""优化一下"才润色；提到"原文念""不润色"才显式不润色；都没提则不传 `--optimize-text/--no-optimize-text`，body 不带字段。

**Case 1** —— 用户说："帮我设计一个年轻女声，读'你好，欢迎收听'"
> agent 跑 `design --description "年轻女声" --text "你好，欢迎收听"`，拿到 audioUrl 链接给用户

**Case 2** —— 用户说："来个磁性男声，中年稳重，做个新闻播报试试"
> agent 跑 `design --description "磁性男声，中年稳重" --text "今日新闻"`，链接回给用户

**Case 3** —— 用户贴一段具体描述："少女音，活泼可爱，读'嗨，大家好'"
> agent 跑 `design --description "少女音，活泼可爱" --text "嗨，大家好"`，链接回给用户

**Case 4** —— 用户说："设计个温柔女声，润色一下读'嗯，那个，晚饭想好吃啥了吗'"
> agent 跑 `design --description "温柔女声" --text "嗯，那个，晚饭想好吃啥了吗" --optimize-text`，链接回给用户

## 用法

```bash
# 默认（不润色 text）
python scripts/design.py --description "年轻女性，声音清脆活泼" --text "你好，欢迎收听今天的节目"

# 显式润色 text
python scripts/design.py --description "中年男性，沉稳磁性" --text "今日新闻" --optimize-text

# 不润色
python scripts/design.py --description "少女音，活泼可爱" --text "嗨" --no-optimize-text
```

## 参数

| 参数 | 必填 | 默认 | 说明 |
| --- | ---: | --- | --- |
| `--description` | 是 | 无 | 音色自然语言描述，最多 500 字符 |
| `--text` | 是 | 无 | 试听文本，最多 500 字符 |
| `--optimize-text` | 否 | 都不传 | 服务端润色 `text`（与 `--no-optimize-text` 互斥） |
| `--no-optimize-text` | 否 | 都不传 | 不润色 `text` |
| `--timeout` | 否 | `180` | HTTP 超时秒数 |
| `--output` | 否 | 无 | 将完整响应 JSON 写入文件 |

> `--optimize-text` 和 `--no-optimize-text` **都不传**时，body 不带 `optimize_text` 字段，由后端决定默认行为。

## 响应

```json
{"success": true, "audioUrl": "http://...", "requestId": "<uuid>"}
```

- `audioUrl`：可下载的试听音频完整 URL
- `requestId`：音频 ID

成功立即返回，**客户端不轮询**（mimo 走同步）。

## When to use

按一段话描述生成**试听**音色，**不能直接合成文本**。试听满意后用户需自行选择 preset 路径（`tts-lychee` 的内置音色）。

## Process

1. 读 `--description`（必填）+ `--text`（必填）+ 可选 `--optimize-text/--no-optimize-text`
2. 校验两者都非空 + 字符上限 500
3. 构造 body：`{description, text}`，若显式传了润色 flag 则加 `optimize_text`
4. POST 到 `/open/timbre-design/generate-mimo`
5. 解包：`audioUrl`（必）+ `requestId`
6. stdout JSON，失败抛 `LycheeApiError`

## Red flags

- `--description` 或 `--text` 空 / 超 500 字符 → 参数校验拒绝
- 退出码 1 + 401：API key 无效

## Verification

成功：

- exit 0
- stdout `{"success": true, "audioUrl": "<http url>", "requestId": "<uuid>"}`
- `audioUrl` 可下载（curl 200）

快速验证：

```bash
python scripts/design.py --description "年轻女性，清脆" --text "你好" --output ./design.json
curl -I "$(jq -r .audioUrl ./design.json)"  # 200
```