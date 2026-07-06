# lychee-skills2

一组面向 Claude Code 与兼容 AI 客户端的 lychee OpenAPI skills。项目把语音、音色、字幕和短剧翻译能力封装为 10 个独立 skill，并提供统一鉴权、一键安装和跨 skill 自检命令。

每个 skill 都可独立安装，也可以通过根安装器一次装齐。

## Skills

| Skill | 功能 | 主要端点 |
| --- | --- | --- |
| `asr-lychee` | 上传音频并识别为文本 | `POST /open/asr` |
| `tts-lychee` | WebSocket 文本转 MP3，支持音色别名匹配 | `WSS /openapi/tts/ws_binary/v2` |
| `voice-clone-lychee` | 上传参考音频克隆音色 | `POST /open/voice/zeroshot/clone` |
| `voice-infer-lychee` | 使用克隆音色执行推理并返回元数据 | `POST /open/voice/zeroshot/infer` |
| `timbre-design-lychee` | 按性别、年龄、风格和口音设计试听音色 | `POST /open/timbre-design/generate` |
| `speaker-classify-lychee` | 异步识别说话人及其文本分段 | `POST /open/speaker-classify/submit`、`GET /status` |
| `voice-separate-lychee` | 异步分离人声和背景音 | `POST /open/voice/separate`、`GET /status` |
| `subtitle-erase-lychee` | 异步擦除视频字幕 | `POST /open/subtitle/erase`、`GET /result` |
| `videots-lychee` | SRT 翻译、重译、回译、状态和结果下载 | `/open/videots/*` |
| `video-compose-lychee` | 视频+音频+字幕异步合成压制 | `POST /open/video-compose/tasks`、`GET /status` |

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

# 装全部 10 个（建议分 2-3 批，npx 工具对多 skill 的 clone 较慢且易断网）：
npx -y skills add TaylorEnthon/lychee-skills2 --skill asr-lychee --skill tts-lychee --skill voice-clone-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill voice-infer-lychee --skill timbre-design-lychee --skill speaker-classify-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill voice-separate-lychee --skill subtitle-erase-lychee --skill videots-lychee
npx -y skills add TaylorEnthon/lychee-skills2 --skill video-compose-lychee
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

安装器会把 10 个 skill 复制到 `~/.claude/skills/`，并把 3 个跨 skill command 复制到 `~/.claude/commands/`。安装过程可重复运行；单个 skill 安装失败会显示 WARN，其余 skill 继续安装。

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

## 开发路线

### 第一阶段：独立 skills

- [x] 10/10 skill 全部完成
- [x] HTTP 与 WebSocket 公共客户端
- [x] 单 skill 安装、自检与根一键安装
- [x] API Key 配置和全量 doctor command

### 可能的第二阶段

- 跨 skill 工作流编排，例如克隆音色后直接合成、字幕翻译后自动配音
- 自动化契约测试、安装回归和多平台 CI
- 依赖自动检测与可选的一键安装
- 统一任务历史、结果下载和失败重试体验
- 根据 lychee OpenAPI 新端点继续扩展 skills

## License

[MIT](LICENSE)
