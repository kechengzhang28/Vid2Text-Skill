# Vid2Text-Skill

**Languages**: [English](README.md)

从视频链接下载音频并完成本地语音转文字的 CLI 工具，以 `.skill` 文件分发供 AI Agent 调用。基于 yt-dlp，覆盖绝大部分主流视频平台。

## 核心功能

- **一键转写**：`vid2text run <url>` 一条命令完成下载、转码、语音识别
- **双模型**：Paraformer-Large（默认，中文最优）或 SenseVoice-Small（多语言，轻量快速）
- **零 API 费用**：模型通过 ModelScope 本地运行，首次下载后完全离线可用
- **文件系统缓存**：两层 Key — 音频 `video_id`、文本 `{content_hash}-{model}` — 模型间互不污染
- **多格式输出**：TXT / JSON（SRT 规划中）
- **Agent 友好**：先算完整结果再路由（STDOUT 或文件 + 摘要）；退出码 0/1/2

## 快速开始

### 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 视频下载 | yt-dlp | 提取最优音频流，覆盖数百个视频平台 |
| 音频转码 | ffmpeg | 转码为 16kHz 单声道 WAV |
| 语音识别 | FunASR（阿里达摩院） | Paraformer-Large / SenseVoice-Small 双模型 |
| CLI | click | 命令行接口与参数解析 |
| 缓存 | 文件系统 | 两层 Key：音频按 video_id、文本按 hash+model |

### 先决条件

- Python >= 3.9
- [ffmpeg](https://ffmpeg.org/)（需在 PATH 中可用）

默认模型首次使用时从 ModelScope 自动下载。

### 安装

```bash
pip install -e ".[dev]"
```

### 基本用法

```bash
# 下载 + 转写
vid2text run https://www.bilibili.com/video/BV1xx411c7mD

# 指定模型和输出格式
vid2text run https://www.youtube.com/watch?v=dQw4w9WgXcQ -m sensevoice -f json

# 转写本地音频
vid2text transcribe audio.wav

# 缓存管理
vid2text cache list
vid2text cache clear
```

## 项目结构

```
Vid2Text-Skill/
├── vid2text/       # 主包（cli、pipeline、downloader、transcoder、recognizer、cache、utils）
├── tests/          # 测试
├── SKILL.md        # Agent 操作手册
├── docs/           # 架构文档
└── pyproject.toml  # 包声明
```

## 开发

```bash
pytest              # 运行测试
ruff check .        # 代码检查
ruff format --check .  # 格式检查
pyright             # 类型检查
```

## 许可证

MIT License
