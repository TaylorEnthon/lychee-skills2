<!--
AGENTS.md — 给 AI coding agent 的全局协作规则。
类似 .claude/CLAUDE.md,但 AGENTS.md 是仓库级、跨 agent(Claude Code / Cursor / Codex)。
CLAUDE.md / AGENTS.md / GEMINI.md 同时存在时,以最具体的为准。
-->

# lychee-skills2 — Agent Rules

仓库是 10 个 lychee OpenAPI skill 的封装,Claude 在用户调用时按 SKILL.md 触发。

## 必有前提

- 用户运行 `/lychee-set-key` 配置 `LYCHEE_API_KEY`(fallback `TTS_API_KEY`)
- bash / pwsh 已装,把 skill 复制到 `~/.claude/skills/<name>-lychee/`

## 全局规则

1. **不请求真实后端除非用户明确要求**。所有测试用 `responses` mock 或 `unittest.mock` 改 `_SESSION`。`SKILL.md` 的示例默认 `--no-wait` 跳过轮询。
2. **不引新依赖**。Python 只能 `requests` + `websocket-client`,Shell `bash 3.2+` / `pwsh 7+`。新依赖必须先讨论。
3. **跨 skill 代码放 `shared/`**;单 skill 用放 `skills/<name>/scripts/`;静态数据放 `skills/<name>/data/`;长文档/FAQ 放 `skills/<name>/references/`(新约定,见 `docs/development.md`)。
4. **改 SKILL.md 的 description / frontmatter 要 1 行描述 + 触发词**("触发:用户说「...」")。其它章节可加,但不删现有功能段。
5. **改输出字段必同步 `docs/output-schema.md`**。改 `shared/http_client.py` / `shared/auth.py` 必先看是否有更上层的 helper。
6. **pre-commit hook 必须过**(`.githooks/pre-commit`):CRLF 检查、大小检查、52 smoke test。Windows 编辑器保存时关 CRLF。
7. **commit 信息用中文**;Co-Authored-By 保留。
8. **失败不破坏现状**。新增 helper 必须在 ≥2 个 caller 上验证可用,否则放进 `shared/_unused/` 等真有用再 promote。
9. **API key 不能 commit**;scripts 不要 console print 含 `api_key` 的请求。
10. **不在 skill 脚本里硬编码后端 URL**;从 `shared/http_client.BASE_URL` 读。

## 仓库根速查

```
install.sh / install.ps1     一键安装 / 配置 CLAUDE_HOME
README.md                    用户入口
CHANGELOG.md                 版本记录
docs/development.md          贡献者 / 加 skill 骨架
docs/output-schema.md        stdout/stderr 字段规范
docs/workflows/              组合使用 recipe
tests/                       pytest,5 个文件 + helpers + smoke
shared/                      auth / http_client / ws_client / poll_status / errors
commands/                    /lychee-set-key / /lychee-doctor / /lychee-workflow
skills/<name>-lychee/        10 个 skill
```

## 何时跑测试

```bash
python -m pytest -q          # 全量
bash tests/run_tests.sh      # 只 smoke(52 个)
```

pre-commit 触发时自动跑 52 smoke。push 前手动跑 `python -m pytest -q`。

## 调试

- 不带 API key:`unset LYCHEE_API_KEY TTS_API_KEY && python <script>` 应退出码 2 + stderr JSON `{"success": false, "error": "...", "step": "<skill>", "hint": "..."}`
- 看后端契约:`shared/http_client.py:60` 的 `_unwrap()` 假定 `ApiResponse<T>` 格式
- 真要打后端:设 `LYCHEE_API_KEY` + 用 `--no-wait` 防止无限轮询

## 不要做

- 不要给 `shared/` 加 5 个 caller 以下的 helper(unused code)
- 不要碰 freeze 层(目前没有明确规定,但 tts `synthesize.py` 和 `shared/auth.py/http_client.py/ws_client.py` 谨慎修改)
- 不要 commit `skills-lock.json` 或 `.codex-prompts/`(pre-commit 会拒)
- 不要在 commit 加 `CRLF`
