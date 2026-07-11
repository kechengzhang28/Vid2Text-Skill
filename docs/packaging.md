# 打包配置

`scripts/build_skill.py` 将项目打包为 `.skill` zip 产物，用于分发。

## 产物结构

```
vid2text.skill
├── SKILL.md
├── pyproject.toml
├── vid2text/
│   ├── __init__.py
│   ├── asr.py
│   ├── cli.py
│   ├── downloader.py
│   ├── errors.py
│   └── transcoder.py
├── bin/
│   ├── darwin-arm64/sense-voice
│   ├── linux-x64/sense-voice
│   └── win-x64/sense-voice.exe
└── models/
    └── sense-voice-small-q4_k.gguf
```

模型文件（174MB GGUF）内嵌于产物中，不需在线下载。

## 安装与运行

不触发构建系统，直接安装运行时依赖（已安装则跳过）：

```bash
python -c "import click,av" 2>/dev/null || pip install click av
```

在产物根目录（SKILL.md 所在目录）下直接以模块方式运行，避免 `pip install -e .` 触发 build-isolation 导致的依赖解析问题，并防止 Python 写入受保护的 `__pycache__`：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m vid2text.cli "<B站链接或BV号>"
```
