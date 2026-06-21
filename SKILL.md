---
name: vid2text
description: 将 B站视频转写为纯文本。当用户提供 B站链接或 BV 号并请求转写时使用。
version: "0.2.0"
---

# Vid2Text

一句命令将 B站视频音频转写为纯文本。底层 SenseVoice.cpp ASR，无需 API Key，无需配置。

## 安装

```bash
pip install -e .
```

## 用法

```bash
vid2text "<B站链接或BV号>"
```

示例：`vid2text "https://www.bilibili.com/video/BV1MN4y177PB"`

仅支持 B站。其他平台退出码 1。

## 输出

- **STDOUT**：纯文本（带标点，无时间戳，无元信息）
- **STDERR**：进度和错误信息（退出码非 0 时再读）

流水线：URL → B站API下载(m4a) → ffmpeg(WAV) → ASR推理 → 纯文本，5分钟视频约 10-30 秒。

## 退出码

| 码 | 含义 | Agent 行动 |
|----|------|-----------|
| 0 | 成功 | 读 STDOUT |
| 1 | 无效链接/不支持的平台 | 告知用户链接无效 |
| 2 | 网络/系统/ASR错误 | 报告错误信息给用户 |
