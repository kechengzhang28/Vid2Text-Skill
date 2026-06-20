# Vid2Text-Skill

**Languages**: [English](README.md)

从视频链接自动下载音频流并完成语音转文字的 CLI 工具。以 `.skill` 文件形式分发，供 AI Agent 加载后自动识别用户意图并调用。

## 核心能力

- **一键转写**：`vid2text run <url>` 自动完成下载 + 转码 + 语音识别全流程
- **双模型可选**：
  - **Paraformer-Large**（默认）：中文识别准确率最高，自带 VAD + 标点恢复 + ITN
  - **SenseVoice-Small**：多语言覆盖（中/英/粤/日/韩），轻量快速
- **本地运行，零 API 费用**：模型通过 ModelScope 自动下载，完全离线可用
- **文件系统缓存**：音频按 `video_id`、转写结果按 `{content_hash}-{model}` 两层 Key，不同模型结果互不污染
- **多格式输出**：支持 TXT / JSON（SRT 后续支持）
- **Agent 友好**：先算完整结果再二选一路由（STDOUT 完整文本 / 写文件 + 摘要）、标准化退出码（0/1/2）

## 快速开始

### 先决条件

- Python >= 3.9
- [ffmpeg](https://ffmpeg.org/)（需在 PATH 中可用）

### 安装

```bash
pip install -e ".[dev]"
```

首次使用时，默认模型（Paraformer-Large）会从 ModelScope 自动下载。

### 基本用法

```bash
# 一键下载 + 转写
vid2text run https://www.bilibili.com/video/BV1xx411c7mD

# 指定模型和输出格式
vid2text run https://www.youtube.com/watch?v=dQw4w9WgXcQ -m sensevoice -f json

# 转写本地音频文件
vid2text transcribe audio.wav -m paraformer

# 缓存管理
vid2text cache list
vid2text cache clear
```

## 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 视频下载 | yt-dlp | 从视频链接提取最优音频流 |
| 音频处理 | ffmpeg | 转码为 16kHz 单声道 WAV |
| 语音识别 | FunASR（阿里达摩院） | 非自回归端到端识别 |
| CLI 框架 | click | 命令行接口 |
| 进度展示 | tqdm | 下载/转码/模型加载进度条 |
| 缓存 | 文件系统（hash/video_id 命名） | 两层 Key：音频按 video_id、文本按 hash+model |

## 项目结构

```
Vid2Text-Skill/
├── vid2text/           # 主包
│   ├── cli.py          # CLI 入口
│   ├── pipeline.py     # 流水线编排
│   ├── downloader.py   # yt-dlp 封装
│   ├── transcoder.py   # ffmpeg 封装
│   ├── recognizer.py   # FunASR 封装
│   ├── cache.py        # 缓存管理
│   └── utils.py        # 异常、日志、类型定义
├── tests/              # 测试
├── SKILL.md            # Agent 操作手册
├── pyproject.toml      # 包声明
└── docs/               # 开发文档
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check vid2text tests
ruff format --check vid2text tests
pyright
```

## 许可证

MIT License


