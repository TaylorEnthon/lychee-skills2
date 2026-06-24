---
description: 列出 tts-lychee 支持的全部音色（按 category 分组）
---

调用 tts-lychee 的音色列表接口。运行：

```bash
python ~/.claude/skills/tts-lychee/scripts/list_voices.py
```

输出 JSON 包含 categories 数组，每项有 name（类别名）+ voices（音色名列表）。
常用类别：默认与基础、女声、男声、儿童与少年、朗读播报、情绪风格、角色职业、方言口音。

不要合成音频，只列出。如果用户说"我要用 XX 音色"或"找个性感女声"——列出后由用户选择，再调 /tts-lychee 合成。
