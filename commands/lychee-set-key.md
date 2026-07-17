---
description: 引导用户设置 LYCHEE_API_KEY 环境变量（Windows / macOS / Linux / 验证三步）
---

用户要调用任何 lychee-* skill，必须先设置 `LYCHEE_API_KEY` 环境变量。

## 第一步：拿到 API Key

访问 https://shanhaistudio.lycheeai.com.cn/，登录后在「API Key 管理」生成。

## 第二步：设置环境变量

按操作系统选一种：

### Windows PowerShell

```powershell
setx LYCHEE_API_KEY "你的API密钥"
# 关闭并重新打开所有终端/AI 客户端
```

### macOS / Linux bash

```bash
export LYCHEE_API_KEY="你的API密钥"
# 加到 ~/.bashrc 或 ~/.zshrc 让新终端自动继承
echo 'export LYCHEE_API_KEY="你的API密钥"' >> ~/.bashrc
```

## 第三步：验证

运行 `/lychee-doctor`，如果看到 `OK: API key 已设置（前 8 位）=...` 就成功了。

## 验证已读取的环境变量名

环境变量固定为 `LYCHEE_API_KEY`。如果在旧文档中看到 `TTS_API_KEY`，那只是历史命名，请改用 `LYCHEE_API_KEY`。
