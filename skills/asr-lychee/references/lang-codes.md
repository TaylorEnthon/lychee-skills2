# ASR 语言编码备忘

## 常见语言代码

| 名称 | ASR `--language` | 后端实际接受 |
|---|---|---|
| 普通话 | `zh-CN` / `zh` | 两种都试 |
| 英语 | `en-US` / `en` | 通常接 `en-US` |
| 日语 | `ja-JP` / `ja` | |
| 粤语 | `zh-HK` / `yue` | 部分模型支持 |
| 四川话 | 不支持,输出空文本 | 不要用方言参数 |

## 已知坑

- **不指定 `--language`**:服务端默认 `zh-CN`,中文英文混合时英文部分识别质量差
- **方言音频**:普通话模型对方言识别率低,**报错空文本也正常**
- **音频时长 < 10s**:服务端拒绝(参数校验)。如果是短音频,改用其他工具
- **音频 > 60min**:服务端超时,长音频先切片
- **m4a/aac 编码问题**:某些 codec 后端不支持,优先用 wav/mp3

## 调试方法

加 `--debug` 看完整 data JSON:

```bash
python scripts/asr.py --file ./audio.m4a --debug
```

data 字段:
- `text`:识别文本(可能为空)
- `language`:服务端实际识别的语言
- 其他字段由后端返回,脚本只强制读 `text`

## 后端契约

接口 `/open/asr`,multipart POST。返回 `ApiResponse<T>` 格式 `{code, info, data}`,`data.text` 是识别结果。失败时 code 非 200,`shared/http_client.py:_unwrap()` 自动 raise `LycheeApiError`。
