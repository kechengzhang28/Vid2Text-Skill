# Contributing

感谢你对 Vid2Text 的关注！

## 环境准备

要求 Python 3.10+。

```bash
git clone <repo-url>
cd Vid2Text-Skill
pip install -e .
```

## 运行测试

```bash
python -m pytest tests/
```

## 项目结构

```
vid2text/
├── __init__.py
├── cli.py              # CLI 入口（Click）
├── downloader.py       # B站 API 直连下载
├── transcoder.py       # PyAV 音频转码
├── asr.py              # SenseVoice.cpp subprocess 推理
└── errors.py           # 异常类型定义
```

## CI/CD

两个 GitHub Actions 工作流：

- **build.yml**：手动触发，编译三平台 sense-voice 二进制并推送至仓库
- **release.yml**：推送 `v*` 标签时自动触发，构建 `.skill` 产物并发布到 GitHub Releases

## 详细文档

架构设计、模块接口、数据格式等详见 [docs/dev.md](docs/dev.md)。
