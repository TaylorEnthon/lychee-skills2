---
name: voice-clone-lychee
version: 1.0.0
description: |
  调 lychee-openapi 的语音克隆接口 /open/voice/zeroshot/clone，上传参考音频生成克隆音色。
  触发：用户说「克隆这个声音」「用这个声音合成」「/voice-clone」「训练音色」。
---

# Voice Clone Lychee

上传一段参考音频，通过 lychee OpenAPI 生成可供后续语音合成使用的克隆音色。

## 配置

设置环境变量 `LYCHEE_API_KEY`。

## 用法

```bash
python scripts/clone.py --file reference.wav
python scripts/clone.py --file voice.mp3 --carry-back "project-001"
python scripts/clone.py --file sample.m4a --output clone-result.json --timeout 180
```

## 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--file` | 是 | 参考音频，支持 wav、mp3、m4a |
| `--carry-back` | 否 | 服务端原样透传的字符串，最多 500 字符 |
| `--timeout` | 否 | HTTP 超时秒数，默认 120 |
| `--output` | 否 | 将服务端完整 JSON 响应写入文件 |

## 参考音频限制

- 格式：wav、mp3、m4a。
- 大小：不超过 10MB。
- 时长：1–30 秒。
- 非 wav 文件会由服务端通过 ffmpeg 转换为 wav。

## 重要：后续合成使用 request_id

克隆接口响应中的 `speaker_id` 始终为 `null`。请使用成功响应的 `request_id` 作为后续 voice-infer 接口的 `speaker_id`。

成功时命令行输出：

```json
{"success": true, "request_id": "<uuid>", "carry_back": "<透传值>"}
```

## When to use

从一段参考音频(目标说话人)创建一个可合成的声纹 id,之后给其它文本/场景配音。一次只克隆一个角色。多说话人场景先分类后逐角色克隆,见 `docs/workflows/multi-speaker-dub.md`。

## Process

1. 读 `--file`,校验 wav/mp3/m4a、≤10MB、1-30 秒
2. 读 `LYCHEE_API_KEY`,multipart POST 到 `/open/voice/zeroshot/clone`,key 是 `audio`,字段含 `carry_back`
3. 解包 data:`request_id`(给后续 infer 用)、`speaker_id`(目前始终为 null)、`carry_back`
4. stdout JSON `{"success": true, "request_id": "...", "carry_back": "..."}`
5. 失败(无 request_id / status 非 200)→ 抛 LycheeApiError

## Red flags

- `speaker_id` 不为 null(罕见):后端字段变了,文档不一致,先查后端
- `carry_back` 返回 null:**透传失败**,可能后端限制了字符串长度(>500 也失败)
- 退出码 1 + 403:API key 无效或额度耗尽
- 退出码 1 + 413:`--file` 超过 10MB 或时长 > 30s

## Verification

成功:

- 退出码 0
- stdout `{"success": true, "request_id": "<36 字符 UUID>", "carry_back": "<透传字符串>"}`
- `request_id` 给 voice-infer-lychee 用,能成功合成一次短文

快速验证:

```bash
python scripts/clone.py --file ./ref.wav --carry-back "test-clone-001" --output ./clone.json
cat ./clone.json  # 应该有 request_id
```
