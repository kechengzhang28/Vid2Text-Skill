# Contributing

感谢你对 Vid2Text 的关注！

## 环境准备

要求 Python 3.10+。

```bash
git clone <repo-url>
cd Vid2Text-Skill
pip install click av pytest
```

## 运行测试

```bash
python -m pytest tests/
```

## 项目结构

```
Vid2Text-Skill/
├── vid2text/             # 核心包
│   ├── __init__.py
│   ├── cli.py            # CLI 入口（click）
│   ├── downloader.py     # B站 API 直连下载
│   ├── transcoder.py     # PyAV 音频转码
│   ├── asr.py            # SenseVoice.cpp subprocess 推理
│   └── errors.py         # 异常类型定义
├── tests/                # pytest 测试
├── bin/                  # 预编译 sense-voice 二进制（三平台）
├── models/               # GGUF 模型文件
├── scripts/
│   └── build_skill.py    # 打包 .skill 产物
├── docs/                 # 项目架构文档
│   ├── architecture.md
│   ├── cli.md
│   ├── downloader.md
│   ├── transcoder.md
│   ├── asr.md
│   ├── errors.md
│   └── packaging.md
├── .github/workflows/    # CI/CD
├── SKILL.md              # Skill 元数据与用法
└── pyproject.toml
```

## CI/CD

两个 GitHub Actions 工作流：

- **build.yml**：手动触发（`workflow_dispatch`），从 [SenseVoice.cpp](https://github.com/lovemefan/SenseVoice.cpp) 源码静态编译三平台（`darwin-arm64` / `linux-x64` / `win-x64`）`sense-voice` 二进制，并提交回仓库 `bin/`
- **release.yml**：推送 `v*` 标签时触发，运行 `scripts/build_skill.py` 构建 `.skill` 产物并上传至 GitHub Releases（草稿状态，需手动发布）

## 详细文档

项目技术架构见以下文档：

- [项目架构](docs/architecture.md) — 流水线、技术栈、模块依赖关系、数据流
- [CLI 入口](docs/cli.md) — 命令行接口设计
- [下载模块](docs/downloader.md) — B站 API 直连下载
- [转码模块](docs/transcoder.md) — PyAV 音频转码
- [ASR 模块](docs/asr.md) — SenseVoice.cpp subprocess 推理
- [错误类型](docs/errors.md) — 异常体系
- [打包配置](docs/packaging.md) — .skill 产物结构
