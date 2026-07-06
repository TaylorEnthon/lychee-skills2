# voice-replicate

用参考音频克隆一个音色，再用任意文本验证该克隆音色；如果已有 `tts-lychee` preset，则可以继续生成 MP3。

## 触发 prompt 示例

```text
按 voice-replicate 流程，用 ./ref.wav 克隆音色，并用“欢迎回来”测试
```

```text
克隆 ./speaker.mp3，然后用这句文本做推理：今天我们继续看下一集
```

```text
/lychee-workflow voice-replicate ./ref.wav --text "This is a cloned voice test"
```

## 步骤分解

| 步骤 | 调用 skill | 输入 | 输出 | 中间产物路径 |
| --- | --- | --- | --- | --- |
| 1. 克隆音色 | `voice-clone-lychee` | `python scripts/clone.py --file ./ref.wav --carry-back voice-replicate --output ./<wf>/01-clone.json` | `request_id`、`carry_back` | `./<wf>/01-clone.json` |
| 2. 克隆音色推理 | `voice-infer-lychee` | `python scripts/infer.py --speaker-id <request_id> --text "任意文本" --output ./<wf>/02-infer.json` | `success`、`duration_seconds`、`speaker_id` | `./<wf>/02-infer.json` |
| 3. 可选生成 MP3 | `tts-lychee` | `python scripts/tts_client.py --voice "默认女声" --text "任意文本" --output ./<wf>/03-output.mp3` | MP3 路径和命中的内置音色名 | `./<wf>/03-output.mp3` |

## 中间产物约定

默认目录用 `~/.claude/lychee-workflows/voice-replicate/`。

`01-clone.json` 是断点文件。它存在时，Claude 应读取 `request_id` 并从步骤 2 继续。`02-infer.json` 用于确认克隆音色能被后端识别，`03-output.mp3` 只在用户选择 `tts-lychee` 内置音色或已有 preset 时生成。

## 已知坑

- 当前 `voice-clone-lychee` 没有 `--text` 参数，也没有 `--audio` 参数；使用 `--file`。
- 当前克隆响应中的 `speaker_id` 为 `null`，后续使用 `request_id`。
- `tts-lychee` 从内置 preset 的 `speaker_ref` 解码出 `speaker_id`，不直接读取 `voice-clone-lychee` 的 `request_id`。如果要让克隆音色直接产出 MP3，需要先确认后端或 preset 是否支持该 `request_id`。
