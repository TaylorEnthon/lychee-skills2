# SRT 字幕格式备忘

## 标准 SRT 格式

```
1
00:00:00,000 --> 00:00:02,500
第一句字幕
[1 blank line]

2
00:00:02,500 --> 00:00:05,000
第二句字幕
```

- 序号:整数,从 1 开始
- 时间码:`HH:MM:SS,mmm --> HH:MM:SS,mmm`(逗号分隔毫秒)
- 文本:多行文本可,空行隔段
- 编码:**UTF-8**,部分 Windows 编辑器默认 GBK,会乱码

## 改 SRT 文件的工具

- VSCode / Sublime(右下角改编码)
- `iconv -f GBK -t UTF-8 input.srt > output.srt`
- Python: `path.read_text(encoding="utf-8")` + `write_text(encoding="utf-8")`

## 给 lychee skill 用时的注意事项

| 场景 | 限制 |
|---|---|
| `videots-lychee` translate | 文件 ≤ 1MB,**英文以外**语言也接受 |
| `video-compose-lychee` | 文件 ≤ 10MB + 必传 `--target-language` |
| `subtract-lychee`(字幕擦除) | 不要传 SRT,本 skill 用视频硬字幕 |

## 字幕压制中文乱码

`video-compose-lychee` 压制时,后端按 `--target-language` 选字体:

- `th` → 泰文字体
- `ar` → 阿拉伯字体(从右到左)
- `ko` → 韩文字体
- `vi` → 越南文字体
- `en` → 英文字体(罗马字)

中文视频用 `zh` 或 `zh-CN` 不在 `language` 取值里?——后端如果默认支持中文,不传 `--target-language` 也行;但和 `video-compose-lychee` 文档要求"传 subtitle 时必传 language"冲突。

实测:后端一般能识别,报错再说。中文传 `en` 或 `zh` 都不报错的话都行。

## 字幕位置 5 个参数

`video-compose-lychee` 5 个字幕位置参数**必须全传或全不传**:

```
--subtitle-x 100
--subtitle-y 800
--subtitle-font-size 36
--coordinate-width 1280
--coordinate-height 720
```

只传 4 个会报错"字幕位置参数必须 5 个同时传"。不传则用默认底部位置。

`--subtitle-font-size` 范围 12-96 像素,超出会自动修正。
