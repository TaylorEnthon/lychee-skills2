# lychee-skills2

一组 Claude / AI 客户端的 skill，通过统一鉴权调用 [lychee-openapi](https://github.com/TaylorEnthon/lychee-openapi) 的能力。

## 当前已装 skill

| Skill | 触发 | 协议 | 端点 |
|---|---|---|---|
| `asr-lychee` | `/asr-lychee` "转录音频" "识别这段语音" | HTTP multipart | `POST /open/asr` |

## 环境要求

- Python 3.8+
- 依赖：`requests`（HTTP）、`websocket-client`（TTS 流式，后续 skill 装上后用）
- API Key：从 https://shanhaistudio.lycheeai.com.cn/ 获取

## 配置 API Key

`LYCHEE_API_KEY`（找不到 fallback `TTS_API_KEY`）：

**Windows PowerShell：**
```powershell
setx LYCHEE_API_KEY "你的API密钥"
```

**macOS / Linux bash：**
```bash
export LYCHEE_API_KEY="你的API密钥"
```

设置后重启 AI 客户端，使其继承新环境变量。

## 安装

### 单 skill（推荐开发时）

```bash
bash asr-lychee/install.sh
# 或 Windows PowerShell
powershell -ExecutionPolicy Bypass -File asr-lychee/install.ps1
```

装到 `~/.claude/skills/asr-lychee/`。

### 根 install

（计划中——等所有 9 个 skill 落地后做）

## 自检

```bash
bash ~/.claude/skills/asr-lychee/doctor.sh
```

不调真实业务接口，检查 Python 版本、依赖、API key 提示、shared/ 能 import、HTTP base 可达。

## 仓库结构

```
lychee-skills2/
├── README.md
├── LICENSE
├── .gitignore
├── shared/                9 个 skill 共享的 Python 模块
│   ├── auth.py            get_api_key() 读 LYCHEE_API_KEY 兼容 TTS_API_KEY
│   ├── http_client.py     post_multipart / post_json / get_json / poll_status
│   └── ws_client.py       TTS WebSocket 二进制协议（tts-lychee 实现，其他 skill 占位）
├── asr-lychee/            第一个 skill
│   ├── SKILL.md
│   ├── install.sh / install.ps1
│   ├── doctor.sh / doctor.ps1
│   └── scripts/asr.py
└── ...
```

## 开发路线

第一阶段：9 个独立 skill。第二阶段：合并。每个 skill 都在 `asr-lychee/` 模板上演进。

- [x] `asr-lychee` — HTTP 语音识别
- [ ] `tts-lychee` — WebSocket 语音合成（含音色匹配）
- [ ] `voice-clone-lychee` — 声音克隆
- [ ] `voice-infer-lychee` — 用克隆音色合成
- [ ] `timbre-design-lychee` — 音色设计
- [ ] `voice-separate-lychee` — 人声/背景音分离
- [ ] `subtitle-erase-lychee` — 视频字幕擦除
- [ ] `videots-lychee` — SRT 字幕翻译
- [ ] `speaker-classify-lychee` — 说话人分类

## License

MIT
