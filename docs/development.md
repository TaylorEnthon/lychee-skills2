# 开发文档

面向贡献者。写新的 skill、改公共模块、加测试,都在这里找规范。

## 仓库结构

```
lychee-skills2/
├── install.sh / install.ps1       根安装器(glob 遍历 skills/*-lychee)
├── README.md                      用户文档
├── CHANGELOG.md                   变更记录
├── requirements.txt               Python 依赖(requests + websocket-client)
├── shared/                        跨 skill 公共模块(被 install.sh 复制到每个 skill)
│   ├── auth.py                    API Key 读取与兼容
│   ├── http_client.py             HTTP + ApiResponse 解包 + LycheeApiError
│   ├── ws_client.py               TTS WebSocket 二进制协议
│   ├── poll_status.py             异步任务轮询 helper
│   └── errors.py                  统一错误 JSON schema
├── commands/                      跨 skill slash command(lychee-set-key / lychee-doctor / lychee-workflow)
├── docs/                          文档(workflows / output-schema.md 等)
├── skills/                        10 个 skill
│   └── <name>-lychee/
│       ├── SKILL.md               Claude 读取的指令(frontmatter + markdown)
│       ├── scripts/<verb>.py      主入口脚本
│       ├── install.sh / .ps1      skill 安装器(把 skill 复制到 ~/.claude/skills/)
│       ├── doctor.sh / .ps1       skill 自检
│       └── (tts-lychee) data/     音色预设
└── tests/                         pytest 测试
    ├── conftest.py                路径常量 + 10 个 skill 的 parametrize
    ├── helpers.py                 smoke test 工具
    ├── run_tests.sh               52 个 smoke test(pre-commit 跑)
    ├── test_<skill>_lychee.py     每个 skill 一个 smoke test 文件
    ├── test_workflow_docs.py      组合使用文档
    ├── test_poll_status.py        轮询 helper
    ├── test_tts_presets.py        tts 音色数据
    └── test_errors.py             错误 helper
```

## 新增一个 skill

最小骨架:

```
skills/<name>-lychee/
├── SKILL.md           # 必须: frontmatter name + description,可选 version
├── scripts/
│   └── <verb>.py      # argparse + main() + return 0/1/2
├── install.sh
├── install.ps1
├── doctor.sh
└── doctor.ps1
```

### SKILL.md 必填字段

```yaml
---
name: <skill-name>
version: 1.0.0
description: |
  一句话说做什么(调哪个 lychee OpenAPI 接口)。
  触发:用户说「<自然语言说法 1>」「<自然语言说法 2>」「<自然语言说法 3>」。
---
```

`name` 必须用 `<name>-lychee` 后缀,`description` 第一行说"做什么",第二行起列"触发词"。

### SKILL.md 推荐章节(对照 addyosmani/agent-skills 模板)

新 skill 推荐包含以下章节(已有 skill 增补即可,无需重写):

```markdown
# <Skill 名>

## 用法

(命令示例,直接复制可跑)

## 参数

(表格或列表)

## 输出

(stdout JSON 示例)

## 退出码

(0/1/2)

## When to use

(用户自然语言说法,跟 description 触发词对应)

## Process

(本 skill 的内部步骤,sub-skill / script 调用顺序)

## Red flags

(运行后哪些征兆表示错了:返回空对象/超时但是 1xx/字段全是 None)

## Verification

(如何知道成功了:文件存在 + 大小 > 0 + mp3 可播放 / 输出 JSON success=true)
```

### references/ 子目录(可选)

长文档 / FAQ / 维护备忘 / 域知识放 `skills/<name>/references/`。SKILL.md 只写"是什么 + 怎么用",references 写"背景 + 已知坑"。

**何时加**(经验法则,不要先加):

- 长文档没法装进 SKILL.md(>300 行)
- 跨多个调用方共享的横向材料(对照 / checklist)
- 域知识(如 tts 音色命名约定)

**何时不加**:只有一个调用方 / 内容短 / 改了 SKILL.md 反而要同步多个文件。

`tts-lychee/references/voicing-notes.md` 是当前仓库里的样板。

### 脚本命名约定

`scripts/<verb>.py` — 用动词:`asr.py` / `translate.py` / `compose.py` / `erase.py` / `infer.py` / `clone.py` / `design.py` / `classify.py` / `separate.py` / `synthesize.py`。

**不**用 `<verb>_client.py` / `<name>.py` 等长名。

### 脚本骨架(参考 `tts-lychee/scripts/synthesize.py`)

```python
#!/usr/bin/env python3
"""lychee <something> 客户端。"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError, get_json, post_multipart
from auth import MissingApiKeyError
from errors import format_error


def configure_stdio() -> None: ...
def build_parser() -> argparse.ArgumentParser: ...
def validate_args(args: argparse.Namespace) -> None: ...
def submit(args) -> Dict[str, Any]: ...
def write_output(path, result): ...


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    try:
        validate_args(args)
        submitted = submit(args)
        # ...轮询 / 下载 / 处理
        public_result = {"success": True, ...}
        print(json.dumps(public_result, ensure_ascii=False))
        return 0
    except MissingApiKeyError as exc:
        print(json.dumps(format_error(exc, step="<skill-name>", hint="运行 /lychee-set-key 配置 API key"), ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps(format_error(exc, step="<skill-name>"), ensure_ascii=False), file=sys.stderr)
        return 2
    except LycheeApiError as exc:
        print(json.dumps(format_error(exc, step="<skill-name>"), ensure_ascii=False), file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(json.dumps(format_error(exc, step="<skill-name>", hint="检查网络"), ensure_ascii=False), file=sys.stderr)
        return 1
    except OSError as exc:
        print(json.dumps(format_error(exc, step="<skill-name>", hint="检查文件路径和权限"), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

### 退出码约定

- `0` 成功
- `1` API/网络/任务失败
- `2` API key 缺失 / 参数 / 本地文件错误

### shared/ 边界

**可以放在 `shared/` 的**:
- 跨多个 skill 复用的工具(读 API key / HTTP 客户端 / 轮询 / 错误格式)
- 纯逻辑、零业务状态

**不要放在 `shared/` 的**:
- 单 skill 用的辅助(放 `skills/<name>/scripts/`)
- 业务领域数据(tts 音色预设放 `tts-lychee/data/`)
- 任何会引入 skill 间循环依赖的

**改动 `shared/` 前**先看现有的 `shared/` 怎么用 — 加新文件可以,改现有 API 要 review 9 个 skill 是不是都依赖。

### 后端契约

`shared/http_client.py` 假定后端返回 `ApiResponse<T>` 格式:
```json
{"code": 0, "message": "ok", "data": {...}}
```
其中 `data` 是业务数据。如果后端某端点返回结构不同(裸 dict / 列表),在该 skill 脚本里手解,**不要**改 `http_client.py` 的通用解包。

## 测试

### 跑测试

```bash
# 全量
python -m pytest -q

# 单文件
python -m pytest tests/test_<skill>_lychee.py -v

# pre-commit 跑的 smoke(52 个)
bash tests/run_tests.sh
```

### 加测试

每个 skill **应该**有 `tests/test_<skill>_lychee.py`,覆盖:
- `test_required_files_exist` — `tests/conftest.py` 的 `SKILLS` 列表自动覆盖
- `test_skill_md_has_yaml_frontmatter`
- `test_script_help_runs` — `python <script> --help` 退出码 0
- `test_doctor_runs_without_api_key` — 无 key 时 doctor 输出 WARN
- `test_install_ps1_source_path_validation`

参考 `tests/test_tts_lychee.py`。

### 数据驱动测试

`tts-lychee/data/presets.json` 是手维护的 JSON,加 `tests/test_tts_presets.py` 自动验:
- REQUIRED_VOICES 都在
- 每个 preset 有 `speaker_ref` / `category` / `match_mode`
- 所有 alias value 都能解析

`scripts/synthesize.py:run_doctor()` 也跑核心匹配检查 — **别绕过**,让 doctor 是真测试。

## CI

GitHub Actions 跑 3 个 workflow(`.github/workflows/`):

- **Tests** — 跨 Ubuntu/Windows × Python 3.9-3.12,跑 `python -m pytest -q`
- **Installers** — 装 10 个 skill + 5 个 command 到 `$RUNNER_TEMP`,验证文件齐全
- ~~CI(已删,和 Tests 重复)~~

pre-commit hook 在 `.githooks/pre-commit`,装到 `.git/hooks/`(install.sh 装):
- 文件大小限制(>10MB fail)
- CRLF 检查(`.py`/`.sh` 必须 LF)
- 跑 `bash tests/run_tests.sh` 52 smoke

**改动 `tests/` 或 `skills/` 后** pre-commit 自动跑,确保基础测试过。

## 输出 schema

所有 skill 通过 stdout 输出一行 JSON。规范见 [docs/output-schema.md](output-schema.md)。**改输出字段时**同步更新该文档。

## 组合使用

3 个 workflow recipe 在 `docs/workflows/`:
- `short-drama-translate.md`
- `multi-speaker-dub.md`
- `voice-replicate.md`

加新 recipe 流程:
1. 写 `docs/workflows/<name>.md`,包含触发 prompt + 步骤分解(调用哪些 skill)+ 中间产物路径
2. 在 `docs/workflows/README.md` 索引加一行
3. 在 `commands/lychee-workflow.md` 期望输出加示例
4. 加 `tests/test_workflow_docs.py` 断言(必填关键词)

**不加** Python 编排代码 — 组合靠自然语言驱动(参考 [listenhub 哲学](https://listenhub.ai/docs/zh/skills/guides/composing-skills))。
