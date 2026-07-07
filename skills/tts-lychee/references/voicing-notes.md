# TTS 音色选择备忘

## 命名约定

- 中文 2-4 字,**不用空格**,后端 preset key 直接是这串字符
- 性别前缀:`女声` / `男声`,方言前缀:`东北话` / `四川话`
- "正常" + 角色 + 语言,如:"温柔女声"、"播音男声"、"云南话男声"

## match_mode

`presets.json` 每个 preset 有 `match_mode`:

- `normal`:参与 contains 匹配,可以模糊命中
- `exact`:严格相等才命中,避免误中(关键音色)

## 5 个核心音色(REQUIRED_VOICES)

不可缺,且 `alias_map.json` 必须能解析:

| name | 用途 |
|---|---|
| `默认女声` | fallback,没指定音色时 |
| `默认男声` | fallback 男 |
| `性感女声` | 关键词"性感"命中 |
| `小男孩声音` | 关键词"男童"命中 |
| `云南话男声` | 地域默认 |

## 关键词匹配优先级(从 synthesize.py:resolve_voice_id)

1. 别名精确匹配(`alias_map` value)
2. preset name 直接匹配
3. 长别名 contains 匹配(按长度倒序,先长后短)
4. `voice_aliases.json` 展开的别名 contains
5. 关键词规则表(27 条硬编码,"男童" → "小男孩声音"等)
6. `男` / `女` fallback 默认

## 修改预设数据的风险

改 `presets.json` 后**必须跑**:

```bash
python -m pytest tests/test_tts_presets.py -v
python -m pytest tests/test_tts_lychee.py::test_script_help_runs -v
```

`run_doctor()` 在 `synthesize.py` 跑时也会验证。

## 加新方言 / 新音色流程

1. 准备后端返回的 `speaker_ref`(base64 编码的 speaker_id)
2. 在 `presets.json` 加 entry,name 是中文 4-6 字
3. 在 `alias_map.json` 加常用别名(2-3 个)
4. 在 `voice_aliases.json` 加更长的别名
5. 必要的话在 `synthesize.py:keyword_rules` 加新关键词规则
6. 跑测试 + doctor
