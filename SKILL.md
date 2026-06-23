---
name: vid2text
description: 将B站视频转写为纯文本。当用户提供B站链接或 BV 号并请求转写时使用。
compatibility: 需要 Python 3.10+ 和网络访问 B站 API
metadata:
  version: "0.2.2"
---



# Vid2Text

一句命令将B站视频音频转写为纯文本。底层 SenseVoice.cpp ASR，无需 API Key，无需配置。

## 安装

不触发构建系统，直接安装运行时依赖（已安装则跳过）：

```bash
python -c "import click,av" 2>/dev/null || pip install click av
```

注意：PowerShell 下 `||` 无效，需分别执行检查与安装。

## 用法

在项目根目录（SKILL.md 所在目录）下执行：

```bash
python -m vid2text.cli "<B站链接或BV号>"
```

示例：`python -m vid2text.cli "https://www.bilibili.com/video/BV1MN4y177PB"`

仅支持B站。其他平台退出码 2。

## 输出

- **STDOUT**：纯文本（带标点，无时间戳，无元信息）
- **STDERR**：进度和错误信息（退出码非 0 时再读）

流水线：URL → B站API下载(m4a) → PyAV(WAV) → ASR推理 → 纯文本，5分钟视频约 10-30 秒。

## 退出码

| 码 | 含义 | Agent 行动 |
|----|------|-----------|
| 0 | 成功 | 读 STDOUT |
| 1 | 无效链接 | 告知用户链接无效 |
| 2 | 不支持的平台/网络/系统/ASR错误 | 报告错误信息给用户 |
