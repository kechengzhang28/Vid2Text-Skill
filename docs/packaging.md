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

模型文件（174MB GGUF）内嵌于产物中，不需在线下载。安装方式为解压后 `pip install -e .`。
