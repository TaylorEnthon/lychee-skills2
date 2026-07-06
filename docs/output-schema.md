# lychee skill 输出 JSON schema

本文记录 `skills/*-lychee/scripts/` 下 10 个 skill 的当前 stdout / stderr 输出结构，作为后续重构和用户集成的唯一参考。

多数脚本成功时向 stdout 打印单行 JSON，失败时向 stderr 打印单行 JSON。例外：`asr-lychee` 默认成功输出纯文本，`asr-lychee --debug`、`tts-lychee/scripts/list_voices.py` 和 `tts-lychee/scripts/preview_match.py` 当前输出 pretty-print JSON。

本文只描述 CLI 可见输出；`--output` 写入的完整服务端响应见文末说明。

## 通用结构

成功：

```json
{"success": true}
```

失败（stderr）：

```json
{"success": false, "error": "<人类可读错误信息>"}
```

退出码：

- `0`：成功。
- `1`：API、网络、任务失败或轮询超时。
- `2`：API key 缺失、参数错误或本地文件错误。

例外：

- `asr-lychee` 默认成功 stdout 是识别文本，不带 `success` 字段。
- `asr-lychee` 失败 stderr 是中文纯文本，不是 JSON。
- `tts-lychee/scripts/list_voices.py` 和 `preview_match.py` 没有统一错误包装；异常会按 Python traceback 退出。

## 公共字段

| 字段 | 类型 | 适用 skill | 说明 |
| --- | --- | --- | --- |
| `success` | bool | 除 ASR 默认成功外的大多数 JSON 输出 | CLI 包装结果是否成功 |
| `error` | str | 失败时 | 人类可读错误信息 |
| `task_id` | str | `videots-lychee`、`video-compose-lychee` | 后端任务 ID |
| `request_id` | str | `voice-clone-lychee`、`voice-infer-lychee`、`speaker-classify-lychee`、`voice-separate-lychee` | 后端算法请求 ID |
| `project_id` | str | `subtitle-erase-lychee` | 字幕擦除项目 ID |
| `waiting` | bool | 异步脚本 `--no-wait` | `false` 表示只提交不轮询 |
| `status` | str | 异步脚本完成或状态查询 | 后端任务状态 |
| `output` | str | `tts-lychee` | 本地 MP3 输出路径 |
| `download_url` | str | `videots-lychee` | 翻译结果下载 URL，可能为空字符串 |
| `result_path` | str | `video-compose-lychee` | 合成视频结果 URL，来自后端 `resultPath` |
| `audioUrl` | str | `timbre-design-lychee` | 试听音频 URL |
| `duration_seconds` | number | `voice-infer-lychee` | 推理时长 |
| `duration_ms` | number/null | `speaker-classify-lychee` | 任务耗时，毫秒 |
| `asr_duration` | number/null | `speaker-classify-lychee` | ASR 处理时长 |
| `spk_result` | array | `speaker-classify-lychee` | 说话人分段数组 |
| `vocals_url` | str | `voice-separate-lychee` | 人声音频 URL，缺失时为空字符串 |
| `no_vocals_url` | str | `voice-separate-lychee` | 背景音 URL，缺失时为空字符串 |
| `tasks` | array | `videots-lychee --tasks` | 当前用户任务列表 |
| `voice` | str | `tts-lychee` | 命中的内置音色名 |
| `carry_back` | str/null | `voice-clone-lychee` | 服务端透传字段 |
| `code` | int | `voice-infer-lychee` | CLI 固定输出 `200` |
| `requestId` | str/null | `timbre-design-lychee` | 后端音色设计请求 ID |

## tts-lychee

主脚本：`skills/tts-lychee/scripts/synthesize.py`

成功 stdout：

```json
{"success": true, "output": "./hello.mp3", "voice": "温柔女声"}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

退出码：

- `2`：缺少 API key。
- `1`：参数值错误、音色数据错误、WebSocket/API 错误、文件写入错误。

辅助脚本：`skills/tts-lychee/scripts/list_voices.py`

成功 stdout（pretty-print JSON）：

```json
{
  "success": true,
  "categories": [
    {"name": "默认与基础", "voices": ["默认女声", "默认男声"]}
  ]
}
```

辅助脚本：`skills/tts-lychee/scripts/preview_match.py`

成功 stdout（pretty-print JSON）：

```json
{
  "success": true,
  "voice": "性感女声",
  "used_default_voice": false,
  "matched": "性感女声"
}
```

`matched` 只有命中别名时出现。

## asr-lychee

脚本：`skills/asr-lychee/scripts/asr.py`

默认成功 stdout 是纯文本：

```text
识别出来的文本
```

`--debug` 成功 stdout 是服务端 `data` 对象的 pretty-print JSON：

```json
{
  "text": "识别出来的文本"
}
```

字段由后端返回决定；当前脚本只强制读取 `text`。

失败 stderr 是纯文本：

```text
配置错误: <错误信息>
参数错误: <错误信息>
ASR 请求失败: <错误信息>
网络请求失败: <错误信息>
文件操作失败: <错误信息>
```

退出码：

- `2`：缺少 API key、参数错误、本地文件错误。
- `1`：API 或网络错误。

## voice-clone-lychee

脚本：`skills/voice-clone-lychee/scripts/clone.py`

成功 stdout：

```json
{"success": true, "request_id": "<uuid>", "carry_back": "project-001"}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## voice-infer-lychee

脚本：`skills/voice-infer-lychee/scripts/infer.py`

成功 stdout：

```json
{"success": true, "code": 200, "duration_seconds": 3.45, "speaker_id": "<request_id>"}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## timbre-design-lychee

脚本：`skills/timbre-design-lychee/scripts/design.py`

成功 stdout：

```json
{"success": true, "audioUrl": "https://example.com/demo.wav", "requestId": "<uuid>"}
```

脚本内部兼容后端返回的 `audio_url` / `request_id`，但 stdout 统一输出 `audioUrl` / `requestId`。

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## speaker-classify-lychee

脚本：`skills/speaker-classify-lychee/scripts/classify.py`

`--no-wait` 成功 stdout：

```json
{"success": true, "request_id": "<uuid>", "waiting": false}
```

轮询完成成功 stdout：

```json
{
  "success": true,
  "request_id": "<uuid>",
  "spk_result": [
    {"spk": "spk_0", "content": "你好", "start": 0.0, "end": 1.2}
  ],
  "asr_duration": 1.2,
  "duration_ms": 1200
}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## voice-separate-lychee

脚本：`skills/voice-separate-lychee/scripts/separate.py`

`--no-wait` 成功 stdout：

```json
{"success": true, "request_id": "<uuid>", "waiting": false}
```

轮询完成成功 stdout：

```json
{"success": true, "request_id": "<uuid>", "vocals_url": "https://example.com/vocal.wav", "no_vocals_url": "https://example.com/bgm.wav"}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## subtitle-erase-lychee

脚本：`skills/subtitle-erase-lychee/scripts/erase.py`

`--no-wait` 成功 stdout：

```json
{"success": true, "project_id": "<project-id>", "waiting": false}
```

轮询完成成功 stdout：

```json
{"status": "success", "success": true, "project_id": "<project-id>"}
```

轮询完成时 stdout 先复制完整后端 result，再覆盖或追加 `success: true`、`project_id`、`status: "success"`。因此还可能包含后端返回的其他字段。

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## videots-lychee

脚本：`skills/videots-lychee/scripts/translate.py`

`--tasks` 成功 stdout：

```json
{"success": true, "tasks": []}
```

`--status-task-id` 成功 stdout：

```json
{"success": true, "task_id": "<task-id>", "status": "completed"}
```

状态查询时 stdout 先放 `success: true`，再合并完整后端 status 对象；后端字段可能包含 `task_id`、`taskId`、`status`、`downloadUrl`、`download_url`、`message` 等。

`--no-wait` 成功 stdout：

```json
{"success": true, "task_id": "<task-id>", "waiting": false}
```

轮询完成成功 stdout：

```json
{"success": true, "task_id": "<task-id>", "status": "completed", "download_url": "https://example.com/result.srt"}
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## video-compose-lychee

脚本：`skills/video-compose-lychee/scripts/compose.py`

`--no-wait` 成功 stdout：

```json
{"success": true, "task_id": "<task-id>", "waiting": false}
```

轮询完成成功 stdout：

```json
{"success": true, "task_id": "<task-id>", "status": "completed", "result_path": "https://example.com/result.mp4"}
```

警告 stderr：

```text
WARN: 未传 --subtitle-file，--target-language 将随请求透传但后端不强制
```

失败 stderr：

```json
{"success": false, "error": "<错误信息>"}
```

## 字段命名约定（待统一）

当前只记录差异，不改代码：

- `task_id` vs `taskId`：`videots-lychee`、`video-compose-lychee` 读取两种后端字段，但 stdout 输出 `task_id`。
- `audioUrl` vs `audio_url`：`timbre-design-lychee` 读取两种字段，但 stdout 输出 `audioUrl`。
- `requestId` vs `request_id`：`timbre-design-lychee` stdout 输出 `requestId`，其他 voice 类 skill 多用 `request_id`。
- `downloadUrl` vs `download_url`：`videots-lychee` 读取两种字段，但 stdout 输出 `download_url`。
- `resultPath` vs `result_path`：`video-compose-lychee` 后端字段是 `resultPath`，stdout 输出 `result_path`。
- `output` vs `download_url` vs `audioUrl` vs `result_path`：都表示产物位置，但有本地路径和远端 URL 的差异。
- `status=success` vs `status=completed`：`speaker-classify`、`voice-separate`、`subtitle-erase` 成功终态是 `success`；`videots`、`video-compose` 成功终态是 `completed`。
- JSON 错误 vs 纯文本错误：除 `asr-lychee` 外，多数脚本失败时输出 `{"success": false, "error": "..."}`。
- 单行 JSON vs pretty-print JSON：主异步脚本和 TTS 合成脚本输出单行 JSON；`asr --debug`、`list_voices.py`、`preview_match.py` 输出 pretty-print JSON。

## 不在本规范的范围

`--output` 参数只是把完整服务端响应另存到文件，不改变 stdout / stderr 的公开格式。

这些落盘文件通常是 pretty-print JSON，字段比 stdout 更多，可能直接包含后端原始字段。本文不把 `--output` 文件视为稳定 CLI schema；用户集成应优先读取 stdout，调试或断点续跑再读取 `--output` 文件。
