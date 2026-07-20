# 模式选择

## 决策树

```text
有 --image？
├─ 是 → image（multipart）
└─ 否 → 有 --audio-urls？
         ├─ 是 → audio_url（JSON）
         └─ 否 → 有 --voice-names？
                  ├─ 是 → 查公共音色池
                  │        ├─ 全找到 → voices（JSON，传 id）
                  │        └─ 任一缺失 → 整体降级 text（JSON，stdout fallback_reason）
                  └─ 否 → 有 --voice-ids？
                           ├─ 是 → voices（JSON）
                           └─ 否 → text（JSON，默认）
```

## 互斥规则

- `--image` / `--audio-urls` / `--voice-ids` 三选一互斥
- `--voice-ids` 和 `--voice-names` 也互斥（不要同时给——一个用 id 列表，一个用 name 列表）
- `--polish` 和 `--no-polish` 互斥
- 同时出现 → 退出码 2 + stderr JSON `error: ...`

## 降级规则（`--voice-names` 模式）

| 命中情况 | 行为 | stdout 字段 |
|---|---|---|
| 全找到 | voices 模式 + 传 id | `mode: "voices"`、`polish: "auto"\|"skipped"\|"forced"` |
| 部分缺失 | 整体降级 text 模式 | `mode: "text"`、`fallback_reason: "音色「X」不在公共音色池（A、B）；整体降级..."` |
| 全缺失 | 整体降级 text 模式 | `mode: "text"`、`fallback_reason: "所有音色名都不在公共音色池（X、Y）..."` |

降级后端**不**会拒——TTS 后端自动选音色，效果通常优于小模型音色。
