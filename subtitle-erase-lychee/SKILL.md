---
name: subtitle-erase-lychee
description: |
  调 lychee-openapi 的视频字幕擦除接口 /open/subtitle/erase，提交视频并返回擦除后结果。
  触发：用户说「擦除字幕」「去掉字幕」「/subtitle-erase」「字幕抹除」。
  异步任务：submit 后 client 本地轮询 result，命中 status=success 才返回。
---

# Subtitle Erase Lychee

上传视频并提交字幕擦除任务，默认轮询到成功后返回第三方服务的完整结果。

## 用法

```bash
python scripts/erase.py --file ./video.mp4
python scripts/erase.py --file ./video.mov --name demo --language-code zh
python scripts/erase.py --file ./video.mp4 --subtitle-mode 2 --interval 10 --timeout 1200
python scripts/erase.py --file ./video.mp4 --no-wait
python scripts/erase.py --file ./video.mp4 --output ./result.json
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--file` | 是 | - | 待擦除字幕的 mp4/mov 视频 |
| `--name` | 否 | - | 项目名称 |
| `--language-code` | 否 | - | 字幕语言代码 |
| `--subtitle-mode` | 否 | - | 字幕模式，取值 1-3 |
| `--interval` | 否 | `5` | 结果轮询间隔，单位秒 |
| `--timeout` | 否 | `600` | 最长等待时间，单位秒 |
| `--no-wait` | 否 | 关闭 | 提交后立即返回 `project_id`，不轮询 |
| `--output` | 否 | - | 将提交响应或最终结果完整写入 JSON 文件 |

## 文件限制

- 视频格式：mp4、mov。
- 文件大小不超过 2GB。
- 视频时长为 10 秒至 60 分钟。

## 响应与轮询

提交成功会得到 `project_id`。默认每隔 `--interval` 秒查询 `/open/subtitle/erase/result`；`pending`、`processing`、`running` 会继续等待，只有 `status=success` 才视为成功，`status=failed` 会立即报错。

成功输出包含 `success`、`project_id`、`status`，同时完整保留服务端返回的其他第三方原始字段。使用 `--no-wait` 时需自行保存 `project_id` 并查询结果。

## 计费与错误

服务端在任务成功后按视频时长异步扣费，客户端不计算或重复扣费。请避免对同一视频重复提交。

设置 `LYCHEE_API_KEY`，也兼容 `TTS_API_KEY`。文件或参数错误返回退出码 2；API、网络、任务失败或轮询超时返回退出码 1。字幕擦除耗时较长，必要时增大 `--timeout`。
