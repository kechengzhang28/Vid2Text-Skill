---
name: "vid2text"
description: "从视频链接下载音频并完成语音转文字，基于 yt-dlp + FunASR。支持 B站/YouTube 等。当用户要求转写视频、提取视频文字、生成字幕时调用。"
---

# Vid2Text Skill — 视频语音转文字

## 1. 能力描述

从视频链接（B站、YouTube 等）下载音频流并完成高准确率语音转文字，基于 yt-dlp + FunASR，覆盖绝大部分主流视频平台。

## 2. 触发场景

当用户表达以下意图时，Agent 应调用本 Skill：

- "帮我转写这个视频" / "把这个视频的文字提取出来"
- "这个视频讲了什么？给我文本"
- "生成视频字幕" / "提取视频字幕"
- "下载并转写这个 B 站视频" / "YouTube 视频转文字"
- "翻译这个视频"（先转写原文，再调用翻译工具）
- 关键词：`转写`、`语音转文字`、`字幕`、`transcribe`、`ASR`、`视频文字提取`

## 3. 先决条件

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| Python >= 3.9 | 运行环境 | — |
| ffmpeg | 音频转码（16kHz 单声道 WAV） | `apt install ffmpeg` / `brew install ffmpeg` |
| 网络连接 | 下载视频音频 + 首次拉取模型 | — |

**模型自动处理**：首次使用时，FunASR 会从 ModelScope 自动下载模型文件（~1-2GB），后续使用无需再次下载。无需用户手动操作。

## 4. 命令

### 4.1 `vid2text run <url>` — 下载并转写

```
vid2text run <url> [OPTIONS]
```

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-m, --model` | `paraformer` \| `sensevoice` | `paraformer` | 选择 ASR 模型 |
| `-f, --format` | `txt` \| `json` | `txt` | 输出格式 |
| `-o, --output` | PATH | — | 输出文件路径（不指定则输出到 STDOUT） |
| `--no-cache` | flag | `False` | 跳过缓存读写 |

### 4.2 `vid2text transcribe <audio_file>` — 转写本地音频

```
vid2text transcribe <audio_file> [OPTIONS]
```

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-m, --model` | `paraformer` \| `sensevoice` | `paraformer` | 选择 ASR 模型 |
| `-f, --format` | `txt` \| `json` | `txt` | 输出格式 |
| `-o, --output` | PATH | — | 输出文件路径 |
| `--no-cache` | flag | `False` | 跳过缓存读写 |

### 4.3 `vid2text cache` — 缓存管理

```
vid2text cache list     # 列出所有文本缓存条目
vid2text cache clear    # 清空所有缓存
```

## 5. 输出契约（Agent 必读）

### 5.1 STDOUT / 文件分工

**无 `-o` 时：**
- STDOUT 输出完整的转写结果（TXT 格式为纯文本；JSON 格式见 5.2）

**带 `-o <file>` 时：**
- 文件写入完整的转写结果
- STDOUT 只输出一行摘要：`<文件绝对路径>\t<字数>\t<时长>`

### 5.2 JSON 输出结构

```json
{
  "meta": {
    "model": "Paraformer-Large",
    "language": "zh",
    "duration_sec": 120.5,
    "video_id": "BV1xx411c7mD",
    "source_url": "https://www.bilibili.com/video/BV1xx411c7mD"
  },
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "大家好",
      "confidence": 0.98
    }
  ],
  "text": "大家好今天我们来..."
}
```

- `meta`：元信息（模型名、语言、时长、视频 ID、来源 URL）
- `segments`：逐句分段（起止时间秒、文本、置信度）
- `text`：完整拼接文本

### 5.3 模型名称

| 别名 | 显示名称 | 用途 |
|------|----------|------|
| `paraformer` | Paraformer-Large | 中文高准确率，带 VAD + 标点恢复 |
| `sensevoice` | SenseVoice-Small | 多语言（中/英/粤/日/韩），轻量快速 |

### 5.4 退出码

| 退出码 | 含义 | Agent 处置 |
|--------|------|------------|
| 0 | 成功 | 读取输出，呈现给用户 |
| 1 | 用户输入错误（URL 无效、文件不存在、参数非法、未知模型） | 向用户报告具体错误，请用户修正输入 |
| 2 | 系统错误（依赖未安装、下载/转码/识别失败） | 检查环境：ffmpeg 是否安装、网络是否可达，向用户报告 |

### 5.5 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 视频下载 | yt-dlp | 从视频链接提取最优音频流，覆盖数百个平台 |
| 音频转码 | ffmpeg | 转码为 16kHz 单声道 WAV |
| 语音识别 | FunASR（阿里达摩院） | 非自回归端到端识别，Paraformer-Large / SenseVoice-Small |
| CLI 框架 | click | 命令行接口与参数解析 |
| 缓存 | 文件系统（hash/video_id 命名） | 两层 Key：音频按 video_id、文本按 {hash}-{model} |

## 6. 典型用法

### 6.1 模型选择决策

| 场景 | 推荐模型 | 命令 |
|------|----------|------|
| 纯中文、要求高准确率 | `paraformer`（默认） | `vid2text run <url>` |
| 多语言/中英混合/粤语/日语/韩语 | `sensevoice` | `vid2text run <url> -m sensevoice` |
| 追求速度、对准确率要求不高 | `sensevoice` | `vid2text run <url> -m sensevoice` |
| 用户未指定模型 | 使用默认 `paraformer` | `vid2text run <url>` |

### 6.2 Agent 调用策略

```
场景 A：用户提供视频链接
  1. 直接调用 vid2text run <url>
  2. 检查退出码，0→输出结果，1→提示用户修正，2→检查环境

场景 B：用户提供本地音频文件
  1. 先检查缓存：vid2text cache list
  2. 调用 vid2text transcribe <audio_file>
  3. 检查退出码，同上

场景 C：用户要求 JSON 结构化输出（需要后续 NLP 处理）
  1. 调用 vid2text run <url> -f json（无 -o 则从 STDOUT 解析 JSON）
  2. 或用 -o 指定文件，从文件读取 JSON

场景 D：长视频（>30 分钟）
  1. Agent 应给予更长的超时时间（10-30 分钟）
  2. 考虑使用 --no-cache 确保不读过期缓存

场景 E：用户切换模型重新转写
  1. 直接换 -m 参数调用，缓存 Key 含模型别名，不会串结果
```

### 6.3 输出结果呈现建议

- **TXT 格式**：直接展示给用户
- **JSON 格式**：提取 `meta` 做简要摘要，`segments` 可做时间轴展示，`text` 做全文展示
- 结果较长时，优先展示前 500 字 + 提示完整内容在文件中

## 7. 约束与注意

| 约束 | 说明 |
|------|------|
| **仅处理音频** | 本工具只提取和转写音频流，不处理视频画面 |
| **本地运行** | 所有处理在本地完成，视频只下载音频流（不下载视频轨道） |
| **模型首次下载** | 首次使用某一模型时会自动从 ModelScope 下载（~1-2GB），需等待 |
| **长视频** | 建议 Agent 为长视频（>30 分钟）设置 10-30 分钟超时 |
| **平台限制** | 基于 yt-dlp，覆盖绝大部分主流视频平台（B站、YouTube、Twitch、Twitter/X 等） |
| **网络依赖** | 下载视频和首次拉取模型需要网络，转写和缓存命中则不需要 |
| **并发** | 同一缓存目录不支持并发写入 |
| **隐私** | 下载的音频和转写结果仅存储在本地 `~/.vid2text/cache/` 中 |
