import re
import subprocess
import sys
from pathlib import Path

from .errors import ModelError

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BINARY_DIR = _PROJECT_ROOT / "bin"
_MODEL_DIR = _PROJECT_ROOT / "models"
_MODEL_FILE = "sense-voice-small-q4_k.gguf"


def _detect_arch() -> str:
    if sys.platform == "win32":
        return "win-x64"
    elif sys.platform == "linux":
        return "linux-x64"
    elif sys.platform == "darwin":
        return "darwin-arm64"
    else:
        raise ModelError(f"不支持的操作系统: {sys.platform}")


def _binary_path() -> Path:
    arch = _detect_arch()
    name = "sense-voice.exe" if sys.platform == "win32" else "sense-voice"
    path = _BINARY_DIR / arch / name
    if not path.exists():
        raise ModelError(f"未找到 ASR 二进制文件: {path}")
    return path


def _model_path() -> Path:
    path = _MODEL_DIR / _MODEL_FILE
    if not path.exists():
        raise ModelError(f"未找到 ASR 模型文件: {path}")
    return path


def _parse_output(stdout: str) -> str:
    text = re.sub(r"^\[\d+\.\d+-\d+\.\d+\]\s*", "", stdout, flags=re.MULTILINE)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text


def transcribe(wav_path: Path) -> str:
    binary = _binary_path()
    model = _model_path()

    result = subprocess.run(
        [
            str(binary),
            "-m", str(model),
            "-t", "4",
            "-l", "auto",
            "-itn",
            str(wav_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        raise ModelError(f"ASR 推理失败 (exit={result.returncode}): {err}")

    return _parse_output(result.stdout)
