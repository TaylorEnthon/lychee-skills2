# multi-speaker-dub

先识别每段是谁在说话，再按角色使用各自参考音频克隆，逐段推理或配音，最后合成视频。

## 触发 prompt 示例

```text
按 multi-speaker-dub 流程处理 ./episode.mp4，说话人参考音频在 ./refs/
```

```text
先识别 ./dialogue.wav 里的说话人，再让我给每个 speaker 匹配参考音频
```

```text
多说话人配音：目标语言 en，输入 ./input.mp4，speaker A 用 ./a.wav，speaker B 用 ./b.wav
```

## 前置条件

用户必须预先提供每个说话人的参考音频。Claude 不能凭空克隆某个角色的声音；如果只有原视频，先用 `speaker-classify-lychee` 拆出 `spk_result`，再让用户给 `spk_0`、`spk_1` 等角色绑定参考音频。

## 步骤分解

| 步骤 | 调用 skill | 输入 | 输出 | 中间产物路径 |
| --- | --- | --- | --- | --- |
| 1. 说话人识别 | `speaker-classify-lychee` | `python scripts/classify.py --file ./dialogue.wav --output ./<wf>/01-speakers.json` | `request_id`、`spk_result`、`asr_duration`、`duration_ms` | `./<wf>/01-speakers.json` |
| 2. 每个角色克隆 | `voice-clone-lychee` | `python scripts/clone.py --file ./refs/spk_0.wav --carry-back spk_0 --output ./<wf>/02-clone-spk_0.json` | 每个 speaker 的 `request_id` | `./<wf>/02-clone-<speaker>.json` |
| 3. 逐段推理或配音 | `voice-infer-lychee` / `tts-lychee` | `python scripts/infer.py --speaker-id <request_id> --text "<segment text>" --output ./<wf>/03-infer-001.json` | 每段元数据；如需 MP3，使用已配置到 `tts-lychee` preset 的音色或用户提供音频 | `./<wf>/03-infer-*.json`、`./<wf>/04-dub.mp3` |
| 4. 合成视频 | `video-compose-lychee` | `python scripts/compose.py --video-file ./input.mp4 --audio-file ./<wf>/04-dub.mp3 --subtitle-file ./<wf>/01-subtitle.srt --target-language en --download-output ./<wf>/05-result.mp4 --output ./<wf>/05-compose.json` | 成片 MP4、`task_id`、`result_path` | `./<wf>/05-result.mp4`、`./<wf>/05-compose.json` |

## 中间产物约定

默认目录用 `~/.claude/lychee-workflows/multi-speaker-dub/`。

- `01-speakers.json`：保存完整 `spk_result`，每段包含说话人、文本和时间。
- `02-clone-<speaker>.json`：保存对应角色克隆结果。
- `03-infer-<NN>.json`：保存每段推理结果和下一步要用的时间信息。
- `04-dub.mp3`：合成后的整条配音；当前仓库不提供多段音频拼接脚本，用户可提供已拼好的音轨。

## 失败恢复

如果 `01-speakers.json` 已存在，先读取唯一 speaker 列表并确认映射；如果某个 `02-clone-<speaker>.json` 已存在，复用里面的 `request_id`，只补缺失角色。

## 已知坑

- `speaker-classify-lychee` 成功终态是 `success`，和 `videots-lychee` 的 `completed` 不同。
- `voice-clone-lychee` 的 `carry_back` 是服务端透传字符串，不会自动生成 `speaker_ref`。
- 多说话人“合成多音轨”不是独立 skill；`video-compose-lychee` 只接收一个 `--audio-file`，所以输入前需要准备好整条配音音轨。
