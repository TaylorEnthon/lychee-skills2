---
description: 跑评估测试,验证 skill 在不同场景下的触发和处理
---

跑 `tests/test_skill_integration.py` 和 `tests/test_contract_*.py` 验证 skill 集成行为,目标是确认:

- 10 个 skill 的 `--help` 都正常
- 缺参数 / 无 API key 触发合理的错误结构
- contract test 与后端契约一致

## 行为

- 读 `tests/test_skill_integration.py`:每个 skill 跑 `--help` + 缺关键参数,确认退出码和 stderr 格式稳定
- 读 `tests/test_contract_<skill>.py`(逐 skill):验证 mock 后端的请求体字段和响应解析
- 输出一份"评估报告":每个 skill 1 行 PASS / SKIP / FAIL

## 触发示例

```text
/lychee-evals
/lychee-evals voice-clone        # 只评某个 skill
/lychee-evals --contract-only    # 只跑 contract test
```

## 期望输出

```text
== lychee skill evals ==
running tests/test_skill_integration.py ...
..................................                     [ 73%]
............................                           [100%]
13 passed, 9 skipped in 5.0s

running tests/test_contract_voice_clone.py ...
3 passed in 0.55s

== eval summary ==
asr-lychee             SKIP (no contract test yet)
tts-lychee             SKIP (no contract test yet)
voice-clone-lychee     PASS (contract test)
voice-infer-lychee     SKIP (no contract test yet)
... (10 total)

== 评估通过 ==
```

## 注意

- 不依赖 LYCHEE_API_KEY,所有 contract test 用 mock
- 改 skill 输出 schema 时跑这个,确认所有测试还过
- 新 skill:加 `tests/test_contract_<name>.py` 后会从 SKIP 变 PASS
