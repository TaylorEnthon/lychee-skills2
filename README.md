# lychee-skills2

## 这是什么

一组面向 Claude Code 与兼容 AI 客户端的 lychee OpenAPI skills。项目把语音、音色、字幕和视频合成能力封装为 11 个独立 skill，并提供统一鉴权、一键安装和跨 skill 自检命令。

这些 skill 覆盖 ASR、TTS、音色克隆、音色推理、音色设计、说话人识别、人声分离、字幕擦除、SRT 字幕翻译和视频压制合成。每个 skill 都可独立安装，也可以通过根安装器一次装齐。

日常使用建议配合 slash command：`/lychee-set-key` 配 API key，`/lychee-doctor` 做全量自检，`/lychee-workflow` 串起字幕翻译、配音准备和视频压制流程。除仓库已有的 `requests` 与 `websocket-client` 外，不需要额外依赖。

## 快速开始

### 5 分钟跑通第一段 TTS

```bash
# 1. 装 skill（挑一种，见下方 "## 一键安装"）
bash install.sh
# 或 npx -y skills add TaylorEnthon/lychee-skills2 --skill tts-lychee

# 2. 配 API key
/lychee-set-key
# 或手动：export LYCHEE_API_KEY=xxx

# 3. 合成第一段 MP3
python ~/.claude/skills/tts-lychee/scripts/synthesize.py --text "你好，这是 lychee 语音合成测试。" --output ./hello.mp3
```

成功会在 `./hello.mp3` 输出文件，屏幕打印 `{"success": true, ...}`。

## 常见任务

文字转语音，选一个预设音色：

```bash
python ~/.claude/skills/tts-lychee/scripts/synthesize.py \
  --text "今天天气不错" --voice "温柔女声" --output ./weather.mp3
```

成功：`./weather.mp3` 存在，屏幕打印 `{"success": true, "output": "./weather.mp3", "voice": "温柔女声"}`。

查看有哪些音色可选：

```bash
python ~/.claude/skills/tts-lychee/scripts/list_voices.py
```

也可以用 `/tts-lychee-list-voices`；输出 JSON 按 category 分组。

音频转文字（ASR）：

```bash
python ~/.claude/skills/asr-lychee/scripts/asr.py --file ./audio.mp3
```

成功：屏幕直接打印识别文本；需要完整 JSON 时加 `--debug`。

克隆一个人的声音：

```bash
python ~/.claude/skills/voice-clone-lychee/scripts/clone.py \
  --file ./ref.wav --carry-back "我的克隆" --output ./clone.json
```

成功：`./clone.json` 包含 `request_id`。当前克隆响应的 `speaker_id` 为 `null`，后续推理使用 `request_id`；TTS 直接合成仍从 `tts-lychee` 的内置 preset 选音色，详见 [docs/workflows/voice-replicate.md](docs/workflows/voice-replicate.md)。

SRT 字幕翻译：

```bash
python ~/.claude/skills/videots-lychee/scripts/translate.py \
  --action translate --file ./input.srt --target-language en \
  --download-output ./translated.srt
```

成功：任务状态为 `completed`，并下载到 `./translated.srt`。

视频字幕翻译后压制配音：

```bash
# 完整流程见 docs/workflows/short-drama-translate.md
/lychee-workflow short-drama-translate ./input.mp4
# 或自然语言："把 ./input.mp4 翻译成英文，配上英文语音，压制成片"
```

成功：每步会写入 `~/.claude/lychee-workflows/short-drama-translate/` 并在 checkpoint 汇报产物。

视频字幕擦除：

```bash
python ~/.claude/skills/subtitle-erase-lychee/scripts/erase.py --file ./video.mp4
```

成功：轮询到 `status=success`，输出包含 `success`、`project_id` 和完整服务端结果。

查看所有 skill 状态：

```bash
/lychee-doctor
# 或单 skill：bash ~/.claude/skills/asr-lychee/doctor.sh
```

成功：汇总显示类似 `11 OK / 0 ERROR`。


## Skills

| Skill | 功能 | 主要端点 |
| --- | --- | --- |
| `asr-lychee` | 上传音频并识别为文本 | `POST /open/asr` |
| `tts-lychee` | WebSocket 文本转 MP3，支持音色别名匹配 | `WSS /openapi/tts/ws_binary/v2` |
| `voice-lychee` | 文本、公共音色、图片或临时参考音频同步生成完整音频 | `POST /open/voice/lychee-voice` |
| `voice-clone-lychee` | 上传参考音频克隆音色 | `POST /open/voice/zeroshot/clone` |
| `voice-infer-lychee` | 使用克隆音色执行推理并返回元数据 | `POST /open/voice/zeroshot/infer` |
| `timbre-design-lychee` | 按性别、年龄、风格和口音设计试听音色 | `POST /open/timbre-design/generate` |
| `speaker-classify-lychee` | 异步识别说话人及其文本分段 | `POST /open/speaker-classify/submit`、`GET /status` |
| `voice-separate-lychee` | 异步分离人声和背景音 | `POST /open/voice/separate`、`GET /status` |
| `subtitle-erase-lychee` | 异步擦除视频字幕 | `POST /open/subtitle/erase`、`GET /result` |
| `videots-lychee` | SRT 翻译、重译、回译、状态和结果下载 | `/open/videots/*` |
| `video-compose-lychee` | 视频+音频+字幕异步合成压制 | `POST /open/video-compose/tasks`、`GET /status` |

想直接动手？看上方 "## 常见任务"。

## 环境要求

- Python 3.8+
- `requests`：HTTP 与文件上传 skill
- `websocket-client`：`tts-lychee`
- 可访问 `https://shanhaistudio.lycheeai.com.cn/openapi`

安装依赖：

```bash
python -m pip install -r requirements.txt
# 或单独装：pip install requests websocket-client
```

## 一键安装

### 方式零：npx 一行安装（推荐）

```bash
# 装单个 skill
npx -y skills add TaylorEnthon/lychee-skills2 --skill tts-lychee

# 装多个 skill
npx -y skills add TaylorEnthon/lychee-skills2 \
  --skill asr-lychee \
  --skill tts-lychee \
  --skill voice-clone-lychee

# 装全部 11 个（建议分 2-3 批，npx 工具对多 skill 的 clone 较慢且易断网）：
npx -y skills add TaylorEnthon/lychee-skills2 --skill asr-lychee --skill tts-lychee --skill voice-clone-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill voice-infer-lychee --skill timbre-design-lychee --skill speaker-classify-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill voice-separate-lychee --skill subtitle-erase-lychee --skill videots-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill video-compose-lychee --skill voice-lychee
```

`npx skills add` 自动从 `skills/<name>/` 拉文件安装到 `~/.claude/skills/<name>/`。

> **注意**：`npx skills add` 一次 `--skill` 多次参数会逐个 clone 仓库，**网络不稳时容易中途断连**。推荐**分 2-3 批**跑（每批 3 个 skill），或直接用方式一的 `bash install.sh` 一次装齐。

### 方式一：仓库安装器

克隆仓库后，在仓库根目录运行：

```bash
bash install.sh
```

Windows PowerShell 7：

```powershell
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

安装器会把 11 个 skill 复制到 `~/.claude/skills/`，并把跨 skill command 复制到 `~/.claude/commands/`。安装过程可重复运行；单个 skill 安装失败会显示 WARN，其余 skill 继续安装。

如只需一个 skill，也可运行 `skills/<name>-lychee/` 子目录中的 `install.sh` 或 `install.ps1`。

## 配置 API Key

安装后运行 `/lychee-set-key`，按提示获取并设置 `LYCHEE_API_KEY`。完整说明见 [commands/lychee-set-key.md](commands/lychee-set-key.md)。

旧环境变量 `TTS_API_KEY` 仍可作为 fallback；两个变量同时存在时优先使用 `LYCHEE_API_KEY`。

## 自检

运行 `/lychee-doctor` 一次检查全部已安装 skill。命令会汇总 Python、依赖、API Key、共享模块和 HTTP health 状态；定义见 [commands/lychee-doctor.md](commands/lychee-doctor.md)。

也可以直接运行单个 skill 的 doctor：

```bash
bash ~/.claude/skills/asr-lychee/doctor.sh
```

## 组合使用

lychee workflows 用自然语言把多个独立 skill 串成短链路，中间产物写到本地，适合字幕翻译、配音准备、视频压制这类需要多步协作的任务。

当前内置 3 个 recipe：[short-drama-translate](docs/workflows/short-drama-translate.md)、[multi-speaker-dub](docs/workflows/multi-speaker-dub.md)、[voice-replicate](docs/workflows/voice-replicate.md)。它们只描述步骤和产物约定，不新增 Python 编排器。

安装后可用 `/lychee-workflow short-drama-translate ./input.mp4` 这类命令启动组合流程。命令定义见 [commands/lychee-workflow.md](commands/lychee-workflow.md)，中间产物约定和 recipe 索引见 [docs/workflows/README.md](docs/workflows/README.md)。

## 文档导航

- [docs/workflows/README.md](docs/workflows/README.md)：3 个组合 workflow 的详细步骤和中间产物约定。
- [commands/lychee-set-key.md](commands/lychee-set-key.md)、[commands/lychee-doctor.md](commands/lychee-doctor.md)、[commands/lychee-workflow.md](commands/lychee-workflow.md)：API key、自检和组合使用详解。
- 每个 skill 的完整说明在 `skills/<name>-lychee/SKILL.md`。

## 仓库结构

```text
lychee-skills2/
├── install.sh / install.ps1       一键安装全部 skill 与 commands
├── README.md
├── LICENSE                        MIT
├── commands/
│   ├── lychee-set-key.md          API Key 配置命令
│   └── lychee-doctor.md           全量自检命令
├── shared/
│   ├── auth.py                    API Key 读取与兼容逻辑
│   ├── http_client.py             HTTP 请求与 ApiResponse 解包
│   └── ws_client.py               TTS WebSocket 二进制协议
└── skills/
    ├── asr-lychee/
    ├── tts-lychee/
    ├── voice-lychee/
    ├── voice-clone-lychee/
    ├── voice-infer-lychee/
    ├── timbre-design-lychee/
    ├── speaker-classify-lychee/
    ├── voice-separate-lychee/
    ├── subtitle-erase-lychee/
    ├── videots-lychee/
    └── video-compose-lychee/
```

每个 skill 子目录包含 `SKILL.md`、`scripts/`、`install.sh`、`install.ps1`、`doctor.sh` 和 `doctor.ps1`；安装时还会复制所需的 `shared/`，`tts-lychee` 另带 `data/` 音色数据。

## 开发

本地提交前建议运行 `python -m pytest -q`，当前完整测试不依赖 `LYCHEE_API_KEY`，不会请求真实后端。

GitHub Actions 会在 push / PR 到 `main` 时运行 [`.github/workflows/tests.yml`](.github/workflows/tests.yml) 和 [`.github/workflows/installers.yml`](.github/workflows/installers.yml),覆盖 Ubuntu、Windows 和 Python 3.9-3.12。skill CLI 输出格式见 [docs/output-schema.md](docs/output-schema.md),贡献指南见 [docs/development.md](docs/development.md),变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 开发路线

### 最近完成

- ✅ 11 个 skill 已完成：语音、音色、字幕、视频合成链路都已有独立入口。
- ✅ 公共 client 已完成：`shared/auth.py`、`shared/http_client.py`、`shared/ws_client.py`。
- ✅ 一键安装、API Key 配置、全量 doctor 和 3 个组合 workflow recipe 已完成。
- ✅ 测试覆盖 skill 必要文件、help、doctor、安装脚本边界、参数校验和 workflow 文档。

### 进行中

- 🚧 README 导航和常见任务命令继续按真实 CLI 参数校准。
- 🚧 组合 workflow 仍是协作 recipe，不新增 Python 编排器。

### 下一阶段（待定）

- 📋 README 示例随 skill 参数变化保持同步，优先补最常复制的端到端命令。
- 📋 单元测试继续从现有 `tests/conftest.py` 覆盖的 11 个 skill 出发，补 command 文档示例和更多参数校验的轻量 smoke test。
- 📋 根据 lychee OpenAPI 新端点或现有端点变更，再决定是否扩展 skill。

## License

[MIT](LICENSE)
