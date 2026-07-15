# Mention 规则

| 模式 | 用户写法 | 服务端处理 |
| --- | --- | --- |
| `voices` | `{{voice:N}}` | 替换为 `@音频N`；N 是 `voice_ids` 的 1-based 下标 |
| `text` | 不允许 mention | CLI 在请求前报错 |
| `image` | 不支持 | CLI 不替换，文本原样发送 |
| `audio_url` | `@音频N` | 不替换，原样透传火山 |

`audio_url` 的 N 必须在 `1..audio_urls数量` 内；`voices` 的 N 必须在 `1..voice_ids数量` 内。

