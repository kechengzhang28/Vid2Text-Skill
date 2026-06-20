# Vid2Text-Skill

**Languages**: [中文](README-zh-CN.md)

A CLI tool that downloads audio streams from video links and transcribes them to text. Distributed as a `.skill` file for AI Agents to load and automatically recognize user intent.

## Core Features

- **One-Click Transcription**: `vid2text run <url>` automatically completes the full pipeline of download + transcoding + speech recognition
- **Dual Model Support**:
  - **Paraformer-Large** (default): Best Chinese recognition accuracy, with built-in VAD + punctuation restoration + ITN
  - **SenseVoice-Small**: Multilingual coverage (Chinese/English/Cantonese/Japanese/Korean), lightweight and fast
- **Local Execution, Zero API Cost**: Models are downloaded automatically via ModelScope, fully available offline
- **Filesystem Cache**: Audio cached by `video_id`, transcription results cached by `{content_hash}-{model}` — two-level keys prevent cross-model contamination
- **Multi-Format Output**: Supports TXT / JSON (SRT coming soon)
- **Agent-Friendly**: Computes full results first, then routes via dual-path (STDOUT full text / write file + summary), standardized exit codes (0/1/2)

## Quick Start

### Prerequisites

- Python >= 3.9
- [ffmpeg](https://ffmpeg.org/) (must be available in PATH)

### Installation

```bash
pip install -e ".[dev]"
```

On first use, the default model (Paraformer-Large) will be automatically downloaded from ModelScope.

### Basic Usage

```bash
# One-click download + transcribe
vid2text run https://www.bilibili.com/video/BV1xx411c7mD

# Specify model and output format
vid2text run https://www.youtube.com/watch?v=dQw4w9WgXcQ -m sensevoice -f json

# Transcribe local audio file
vid2text transcribe audio.wav -m paraformer

# Cache management
vid2text cache list
vid2text cache clear
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Video Download | yt-dlp | Extract optimal audio stream from video links |
| Audio Processing | ffmpeg | Transcode to 16kHz mono WAV |
| Speech Recognition | FunASR (Alibaba DAMO Academy) | Non-autoregressive end-to-end recognition |
| CLI Framework | click | Command-line interface |
| Progress Display | tqdm | Download/transcoding/model loading progress bars |
| Cache | Filesystem (hash/video_id naming) | Two-level keys: audio by video_id, text by hash+model |

## Project Structure

```
Vid2Text-Skill/
├── vid2text/           # Main package
│   ├── cli.py          # CLI entry point
│   ├── pipeline.py     # Pipeline orchestration
│   ├── downloader.py   # yt-dlp wrapper
│   ├── transcoder.py   # ffmpeg wrapper
│   ├── recognizer.py   # FunASR wrapper
│   ├── cache.py        # Cache management
│   └── utils.py        # Exceptions, logging, type definitions
├── tests/              # Tests
├── SKILL.md            # Agent operation manual
├── pyproject.toml      # Package declaration
└── docs/               # Development documentation
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code linting
ruff check vid2text tests
ruff format --check vid2text tests
pyright
```

## License

MIT License


