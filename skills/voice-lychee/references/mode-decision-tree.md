# 模式选择

```text
有 --image？
├─ 是 → image（multipart）
└─ 否 → 有 --audio-urls？
         ├─ 是 → audio_url（JSON）
         └─ 否 → 有 --voice-ids？
                  ├─ 是 → voices（JSON）
                  └─ 否 → text（JSON，默认）
```

三个模式选择参数互斥；同时出现时本地报参数错误，避免静默忽略输入。

