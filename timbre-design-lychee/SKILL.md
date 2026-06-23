---
name: timbre-design-lychee
description: |
  调 lychee-openapi 的音色设计接口 /open/timbre-design/generate，按性别/年龄/风格/口音生成试听音色。
  触发：用户说「设计音色」「生成新音色」「按 XX 风格生成」「/timbre-design」。
  注意：返回的 audioUrl 是试听音频 URL（camelCase 字段），不是二进制；本 skill 一次同步返回（服务端内部轮询），不需要客户端再轮询。
---

# Timbre Design Lychee

按语言、性别、年龄、音高、风格和口音生成一段可下载的试听音频。

## 配置

设置环境变量 `LYCHEE_API_KEY`；未设置时兼容读取 `TTS_API_KEY`。

## 用法

```bash
python scripts/design.py --text "你好，这是音色设计测试。" --lang zh --gender 2 --age 2
python scripts/design.py --text "您好。" --lang zh --gender 1 --age 3 --pitch 3 --accent 4
python scripts/design.py --text "Hello from the new voice." --lang en --gender 2 --age 2 --accent 4 --output result.json
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
|---|---:|---|---|
| `--text` | 是 | 无 | 试听文本，最多 500 字符 |
| `--lang` | 是 | 无 | `zh/en/ja/de/fr/es/ko/ar/ru/nl/it/pl/pt/vi/id/th` |
| `--gender` | 是 | 无 | `1`=男，`2`=女 |
| `--age` | 是 | 无 | `1`=儿童，`2`=青年，`3`=中年，`4`=老年 |
| `--pitch` | 否 | `1` | `1`=跳过，`2`=极低，`3`=低，`4`=中，`5`=高，`6`=极高 |
| `--style` | 否 | `1` | `1`=跳过，`2`=耳语 |
| `--accent` | 否 | `1` | `1`=跳过；中文 2-13，英文 2-11 |
| `--timeout` | 否 | `180` | 服务端内部轮询最多 120 秒，预留网络开销 |
| `--output` | 否 | 无 | 将完整 JSON 响应写入文件 |

## 口音值

中文：`2`=河南，`3`=陕西，`4`=四川，`5`=贵州，`6`=云南，`7`=桂林，`8`=济南，`9`=石家庄，`10`=甘肃，`11`=宁夏，`12`=青岛，`13`=东北。

英文：`2`=American，`3`=Australian，`4`=British，`5`=Chinese，`6`=Canadian，`7`=Indian，`8`=Korean，`9`=Portuguese，`10`=Russian，`11`=Japanese。

## 响应与超时

服务端内部会最多轮询 24 次、每次 5 秒，客户端只发送一次 generate 请求，不调用 status。建议保持 `--timeout 180`。

- `audioUrl`：可下载的试听音频完整 URL。
- `requestId`：任务 ID，后续可用于查询 `/open/timbre-design/status`。
- `outputDir`：服务端输出目录。

字段为 camelCase，成功时输出：

```json
{"success": true, "audioUrl": "http://...", "requestId": "<uuid>"}
```
