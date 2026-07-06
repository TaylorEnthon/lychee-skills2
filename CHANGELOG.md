# Changelog

lychee-skills2 的所有显著变更按时间倒序记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 改动

- 加 `shared/errors.py`:`format_error(exc, step, hint)` 统一 8 个 skill 的 stderr JSON 错误输出,带 `step` 和 `hint` 字段,便于 `/lychee-workflow` 诊断
- 清 5 个 skill 的残留 `import time`(重构 `poll_result` 后已无用):classify / separate / erase / translate / compose
- 加 `tests/test_errors.py` 覆盖 `format_error` 4 个分支 + 端到端 subprocess 验证

## 0.6.0 - 2026-07-06

### 改动

- 抽 `shared/poll_status.py` 统一轮询逻辑,5 个 skill 的 `poll_result` 用 helper(classify/separate/erase/translate/compose),净减 ~100 行
- 加 `tests/test_tts_presets.py` 验 `presets.json` / `alias_map.json` 完整性(REQUIRED_VOICES、base64、match_mode)
- 加 `tests/test_poll_status.py` 覆盖 success / failed / timeout 三分支

## 0.5.0 - 2026-07-06

### 改动

- 修 CI:`tests.yml` 改装 `requirements.txt` + pytest;`installers.yml` 加 `video-compose` 和 `lychee-workflow`;删重复的 `ci.yml`
- 修 pre-commit 测试只验内容不查 mode 位(GitHub checkout 不保留)
- 修 installers `CLAUDE_HOME` 应是 `$HOME/.claude` 而不是 `$HOME`
- 加 GitHub Actions CI:Windows + Ubuntu × Python 3.9-3.12
- 加 `docs/output-schema.md`:10 个 skill 的 stdout/stderr/退出码规范

## 0.4.0 - 2026-07-06

### 改动

- 10 个 SKILL.md 加 `version: 1.0.0` frontmatter
- `tts-lychee/scripts/tts_client.py` → `synthesize.py`(统一命名)
- README 重写:加 "## 这是什么" / "## 快速开始" / "## 常见任务" / "## 文档导航"

## 0.3.0 - 2026-07-06

### 改动

- 加组合使用:3 个 recipe(short-drama-translate / multi-speaker-dub / voice-replicate)+ `/lychee-workflow` slash command + 中间产物约定
- 新增 `video-compose-lychee` skill
- 加 `tests/test_video_compose_lychee.py` 和 `tests/test_workflow_docs.py`

## 0.2.0 - 2026-07-05

### 改动

- 修 `tts-lychee/SKILL.md` argparse 漂移:删除未注册的 `--list-voices` / `--preview-match` / `--doctor` 文档入口,改指向 `scripts/list_voices.py` / `scripts/preview_match.py`

## 0.1.0 - 2026-07-05

### 初始

- 9 个 skill(asr / tts / voice-clone / voice-infer / timbre-design / speaker-classify / voice-separate / subtitle-erase / videots)
- 公共 `shared/auth.py` / `http_client.py` / `ws_client.py`
- 一键安装(bash / pwsh) + `/lychee-set-key` + `/lychee-doctor`
- 52 个 smoke test
