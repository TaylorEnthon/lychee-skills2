---
description: 预览 tts-lychee 自然语言描述会匹配到哪个音色（不合成音频）
---

调用 tts-lychee 的音色匹配预览。运行：

```bash
python ~/.claude/skills/tts-lychee/scripts/preview_match.py "用户的描述文本"
```

例如：
```bash
python ~/.claude/skills/tts-lychee/scripts/preview_match.py "性感的女声"
python ~/.claude/skills/tts-lychee/scripts/preview_match.py "男童"
python ~/.claude/skills/tts-lychee/scripts/preview_match.py "云南话"
```

输出 JSON：`{success, voice, used_default_voice, matched?}`。
如果 `used_default_voice: true`，说明没匹配上、用了默认女声——告诉用户"我理解为默认女声，可以吗？"。

不合成音频。匹配确认后用 /tts-lychee 合成。
