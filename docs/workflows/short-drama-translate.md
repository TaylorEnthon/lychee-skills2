# short-drama-translate

把短剧视频或字幕翻译成目标语言，准备配音音色，压制新字幕和音频，并按需擦掉原视频字幕。

## 触发 prompt 示例

```text
把 ./input.mp4 翻译成英文，配上英文语音，压制成片
```

```text
按 short-drama-translate 流程，目标语言英文，音色用 ./ref.wav 克隆，擦掉原字幕
```

```text
按 short-drama-translate 流程走 ./input.mp4 -> th，每步保存中间产物到 ~/work/thai/
```

## 步骤分解

| 步骤 | 调用 skill | 输入 | 输出 | 中间产物路径 |
| --- | --- | --- | --- | --- |
| 1. 翻译字幕 | `videots-lychee` | `python scripts/translate.py --action translate --file ./input.srt --target-language th --download-output ./<wf>/01-subtitle.srt --output ./<wf>/01-videots.json` | 翻译后的 SRT；JSON 中可取 `task_id` / `download_url` | `./<wf>/01-subtitle.srt`、`./<wf>/01-videots.json` |
| 2. 克隆参考音色 | `voice-clone-lychee` | `python scripts/clone.py --file ./ref.wav --carry-back short-drama-translate --output ./<wf>/02-clone.json` | `request_id`；后续作为 `voice-infer-lychee --speaker-id` | `./<wf>/02-clone.json` |
| 3. 按字幕段推理 | `voice-infer-lychee` | `python scripts/infer.py --speaker-id <voice-clone request_id> --text "<subtitle segment>" --output ./<wf>/03-infer-001.json` | 每段 `duration_seconds` 等元数据；真实 MP3 合成仍用 `tts-lychee` 的内置音色或已配置 preset | `./<wf>/03-infer-*.json`、`./<wf>/04-dub.mp3` |
| 4. 压制成片 | `video-compose-lychee` | `python scripts/compose.py --video-file ./input.mp4 --audio-file ./<wf>/04-dub.mp3 --subtitle-file ./<wf>/01-subtitle.srt --target-language th --download-output ./<wf>/05-result.mp4 --output ./<wf>/05-compose.json` | 成片 MP4；JSON 中有 `task_id`、`status`、`result_path` | `./<wf>/05-result.mp4`、`./<wf>/05-compose.json` |
| 5. 可选擦原字幕 | `subtitle-erase-lychee` | `python scripts/erase.py --file ./input.mp4 --no-wait --output ./<wf>/06-erase.json` | `project_id`；用于保留原片但去掉原字幕的场景 | `./<wf>/06-erase.json` |

## 中间产物约定

默认目录用 `~/.claude/lychee-workflows/short-drama-translate/`。用户指定目录时用用户目录；否则按 `./<wf>/<NN>-<name>.<ext>` 写入。

关键文件：

- `01-subtitle.srt`：目标语言字幕。
- `02-clone.json`：克隆结果，下一步读取 `request_id`。
- `03-infer-*.json`：逐字幕段推理元数据。
- `04-dub.mp3`：已经准备好的配音音频；当前仓库没有自动拼接脚本，需由用户提供或由 Claude 分段生成后手动合成。
- `05-result.mp4`：压制成片。

## 失败恢复

如果 `./<wf>/02-clone.json` 存在且包含 `request_id`，从步骤 3 继续，不重复克隆。若 `01-subtitle.srt` 已存在，则跳过 VideoTS 翻译，先让用户确认字幕是否可直接复用。

## 已知坑

- `videots-lychee` 的成功状态是 `completed`，不是 `success`。
- `voice-clone-lychee` 参数是 `--file`，不是 `--audio`；接口返回的 `speaker_id` 始终为 `null`，后续用 `request_id`。
- `voice-infer-lychee` 只返回算法元数据，不返回 MP3 二进制。
- `tts-lychee` 没有 `--list-voices` flag；列音色用 `/tts-lychee-list-voices`。
- `video-compose-lychee` 传 `--subtitle-file` 时必须同时传 `--target-language`。
