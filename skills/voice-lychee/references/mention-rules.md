# Mention 规则

| 模式 | 用户写法 | 服务端处理 |
| --- | --- | --- |
| `voices` | `{{voice:N}}` | 替换为 `@音频N`；N 是 `voice_ids` 的 1-based 下标 |
| `text` | 不允许 mention | CLI 在请求前报错 |
| `image` | 不支持 | CLI 不替换，文本原样发送 |
| `audio_url` | `@音频N` | 不替换，原样透传火山（`@音频N` 是后端原生引用） |

N 范围：`audio_url` 在 `[1, audio_urls.size()]`；`voices` 在 `[1, voice_ids.size()]`。

## 示例

### `voices` 模式

```text
{{voice:1}}说：你好啊。{{voice:2}}回答：我很好，谢谢！
```

后端把 `{{voice:1}}` → `@音频1`、`{{voice:2}}` → `@音频2`，对应 `voice_ids=["id1","id2"]`。

### `audio_url` 模式

```text
@音频1说：你好，欢迎收听本期节目。@音频2回答：谢谢你的介绍。
```

`@音频N` 直接透传后端，对应 `audio_urls=["url1","url2"]`。
