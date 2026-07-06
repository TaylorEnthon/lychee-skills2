# lychee workflows

用自然语言把多个 lychee skill 串成短链路：对话上下文记录意图，中间产物落盘，失败后从上一步结果继续。

## 工作流列表

| name | 一句话 | 步骤数 | 适用场景 |
| --- | --- | ---: | --- |
| [short-drama-translate](short-drama-translate.md) | 短剧字幕翻译、配音准备、字幕压制和可选擦字幕 | 5 | 原视频或原字幕出海翻译 |
| [multi-speaker-dub](multi-speaker-dub.md) | 先分清说话人，再按角色克隆和配音，最后合成 | 4 | 多角色短剧、访谈、播客片段 |
| [voice-replicate](voice-replicate.md) | 克隆音色并用任意文本验证或合成 | 3 | 组合 workflow 入门、音色复用验证 |

## 中间产物约定

- 根目录：`~/.claude/lychee-workflows/`
- 每个 workflow 一个子目录：`~/.claude/lychee-workflows/<workflow-name>/<NN>-<step-name>.<ext>`
- JSON 文件统一保留少量字段：

```json
{
  "success": true,
  "step": "02-clone",
  "workflow": "short-drama-translate",
  "timestamp": "2026-07-06T12:00:00+08:00",
  "next_input": {"speaker_id": "<voice-clone request_id>"}
}
```

`next_input` 只放下一步要消费的字段，如 `task_id`、`download_url`、`request_id`、`speaker_id` 或 `result_path`。

清理重跑：

```bash
rm -rf ~/.claude/lychee-workflows/<workflow-name>
```

## 通用原则

- 自然语言驱动，不写 YAML 硬编排。
- 同一段对话上下文就是状态载体，Claude 应先复述当前 checkpoint 再继续。
- 明确链式指令优于单点指令，例如“翻译字幕后压制成片”比“处理这个视频”更稳。
- 用户可以显式插入 checkpoint，例如“先看第 2 步结果，再决定是否继续”。
- 中间产物落盘用于断点续跑；自动恢复只是一条协作约定，不是代码层调度器。
