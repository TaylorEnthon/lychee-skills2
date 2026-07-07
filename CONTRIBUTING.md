# 贡献指南

本仓库是 10 个 lychee OpenAPI skill 的封装,给 Claude Code(及其他 skills-compatible 客户端)使用。

## 致贡献者

- 已有 10 个 skill 都跑 97 个测试,改任何一个 skill 之前先跑 `python -m pytest -q`
- 改公共代码(`shared/`)前先看下面"哪些能改"
- 完整背景必读:[AGENTS.md](AGENTS.md) + [docs/development.md](docs/development.md)

## 提交流程

### 1. 准备

```bash
git clone https://github.com/TaylorEnthon/lychee-skills2.git
cd lychee-skills2
pip install -r requirements.txt
pip install pytest
```

### 2. 改之前

- **必须先读**对应 skill 的 `SKILL.md` + `references/*.md`(如有)
- 检查 `git log -- skills/<name>-lychee/` 看最近改动
- 跑基线 `python -m pytest -q`,确认现状绿

### 3. 改之中

- 不引新依赖(只用 `requests` + `websocket-client`)
- 不改 `shared/auth.py`、`shared/http_client.py`、`shared/ws_client.py` 这三个"冻结层";要改需要在 PR 描述里讲清楚
- 不改 `tests/conftest.py` 的 `SKILLS` 列表(只改具体 test 文件)
- 不改 install.sh / install.ps1 的硬编码 skill 数(N 自动维护)
- 输出 JSON 字段改了,必同步 `docs/output-schema.md`
- 不引入 fan-out / parallel / conditional 编排逻辑(本仓库坚持"自然语言驱动")

### 4. PR 提交流程

- 改完后:
  ```bash
  python -m pytest -q
  bash tests/run_tests.sh  # pre-commit 也跑这个
  ```
- commit 信息格式(中文风格):
  ```text
  <一句话说改了什么>

  - <改动点 1>
  - <改动点 2>
  - <影响范围>

  Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
  ```
- PR 模板(`.github/PULL_REQUEST_TEMPLATE.md`)必填,包括:
  - 改动类型(bug fix / 新 skill / 重构 / 文档 / CI)
  - 是否改 shared/、是否需要后端先改
  - 测试状态
- push 后 CI 自动跑 https://github.com/TaylorEnthon/lychee-skills2/actions
- 等 review 后 merge

### 5. 改什么要被拒

- 引入新依赖(只允许 `requirements.txt` 里的)
- 改 `shared/auth.py` 强行兼容新认证方式
- skill 输出 JSON 字段改了不更新 docs
- commit 加 `skills-lock.json` 或 `.codex-prompts/`(pre-commit 拒)
- commit 文件含 CRLF(Windows 编辑器默认开的)
- pre-commit hook 失败不修

## 加一个新 skill

### 步骤清单

1. 创建 `skills/<name>-lychee/`,子目录:
   ```
   skills/<name>-lychee/
   ├── SKILL.md
   ├── scripts/<verb>.py
   ├── install.sh
   ├── install.ps1
   ├── doctor.sh
   └── doctor.ps1
   ```
2. `SKILL.md` 必填字段见 [docs/development.md](docs/development.md) "加一个新 skill" 章节
3. `scripts/<verb>.py` 用 `shared/auth.py` + `shared/http_client.py` + `shared/errors.py`,参考 `skills/tts-lychee/scripts/synthesize.py` 模板
4. 测试:`tests/test_<name>_lychee.py`,跑通 `python -m pytest -q`
5. 加到 `tests/conftest.py` 的 `SKILLS` 列表(只有这一刻才动 conftest)
6. 在 `README.md` 的 Skills 表格加一行
7. 更新 `.claude-plugin/plugin.json` 的 `skills` 数组
8. 更新 `docs/output-schema.md` 加新 skill 章节
9. CHANGELOG.md Unreleased 段加一行

### install.sh / install.ps1 / doctor.sh / doctor.ps1 从已有 skill 复制

模板看 `skills/asr-lychee/`(最简单)或 `skills/tts-lychee/`(最完整,含 `data/`)。

## 加一个 workflow recipe

1. `docs/workflows/<name>.md`,含 触发 prompt 示例、步骤分解、中间产物路径
2. `docs/workflows/README.md` 索引表格加一行
3. `commands/lychee-workflow.md` 期望输出加示例
4. `tests/test_workflow_docs.py` 加断言(必填关键词)

不动 Python 编排代码。靠自然语言驱动。

## 测试约定

- `tests/<skill>_lychee.py` **每个 skill 一个文件**,覆盖:
  - 必需文件存在
  - SKILL.md frontmatter
  - `--help` 退出码 0
  - `doctor.sh` 无 API key 跑通
  - `install.ps1` 源路径校验
- `tests/test_contract_<skill>.py` mock 后端,验证请求体 + 响应解析
- `tests/test_skill_integration.py` 跨 skill smoke
- 跑测试:**不要**依赖 LYCHEE_API_KEY

## shared/ 边界

**可以放**:
- 跨 ≥2 个 skill 复用的工具
- 零业务状态、纯逻辑

**不要放**:
- 单 skill 用的辅助
- 业务数据(放 `skills/<name>/data/`)
- 长文档/FAQ(放 `skills/<name>/references/`)
- 任何会引入 skill 间循环依赖的

## 输出 schema 约定

参见 [docs/output-schema.md](docs/output-schema.md)。改任何 skill 输出字段前:

1. 看 [docs/output-schema.md](docs/output-schema.md) 当前定义
2. 改 skill 的 `print(json.dumps(...))` 那行
3. 同步文档
4. 加 `tests/test_contract_<skill>.py` 覆盖新字段
5. CHANGELOG.md Unreleased 段加一行

## 报告问题

- **Bug**:GitHub issue 用 `.github/ISSUE_TEMPLATE/bug.md` 模板
- **新功能 / 新 endpoint**:用 `.github/ISSUE_TEMPLATE/feature.md`
- **文档错别字**:用 `.github/ISSUE_TEMPLATE/docs.md`

## 验证清单(改完跑这 5 步)

```bash
# 1. 全量测试
python -m pytest -q

# 2. Smoke(只 doctest / 必备文件)
bash tests/run_tests.sh

# 3. CR / LF 一致性
git status --short

# 4. GitHub Actions(本地看不完)
git push origin main
# 看 https://github.com/TaylorEnthon/lychee-skills2/actions

# 5. 装一遍到自己 ~/.claude/skills
bash install.sh
~/.claude/skills/<modified-skill>/doctor.sh
```

## 致谢

感谢所有贡献者(包括 `npx skills add` 用户,他们也是反馈源)。
