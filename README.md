# Vid2Text-Skill

**Languages**: [中文](README-zh-CN.md)

A CLI tool that downloads audio from video URLs and transcribes it via on-device ASR. Packaged as a `.skill` for AI Agents. Powered by yt-dlp, covering most major video platforms.

## Features

- **One-Click Transcription**: `vid2text run <url>` completes download, transcode, and ASR in one command
- **Dual Model**: Paraformer-Large (default, best for Chinese) or SenseVoice-Small (multilingual, lightweight)
- **Zero API Cost**: Models run locally via ModelScope, fully offline after first download
- **Filesystem Cache**: Two-level keys — audio by `video_id`, text by `{content_hash}-{model}` — isolates results across models
- **Multi-Format**: TXT / JSON output (SRT planned)
- **Agent-Friendly**: Full result computed first, then routed (STDOUT or file + summary); exit codes 0/1/2

## Quick Start

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Video Download | yt-dlp | Extract optimal audio stream from hundreds of video platforms |
| Audio Transcoding | ffmpeg | Transcode to 16kHz mono WAV |
| Speech Recognition | FunASR (Alibaba DAMO Academy) | Paraformer-Large / SenseVoice-Small dual models |
| CLI | click | Command-line interface and argument parsing |
| Cache | Filesystem | Two-level keys: audio by video_id, text by hash+model |

### Prerequisites

- Python >= 3.9
- [ffmpeg](https://ffmpeg.org/) (must be available in PATH)

The default model downloads from ModelScope on first use.

### Installation

```bash
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Download + transcribe
vid2text run https://www.bilibili.com/video/BV1xx411c7mD

# Specify model and output format
vid2text run https://www.youtube.com/watch?v=dQw4w9WgXcQ -m sensevoice -f json

# Transcribe local audio
vid2text transcribe audio.wav

# Cache management
vid2text cache list
vid2text cache clear
```

## Project Structure

```
Vid2Text-Skill/
├── vid2text/       # Main package (cli, pipeline, downloader, transcoder, recognizer, cache, utils)
├── tests/          # Test suite
├── SKILL.md        # Agent operation manual
├── docs/           # Architecture documentation
└── pyproject.toml  # Package declaration
```

## Development

```bash
pytest              # Run tests
ruff check .        # Lint
ruff format --check .  # Check formatting
pyright             # Type check
```

## License

MIT License
