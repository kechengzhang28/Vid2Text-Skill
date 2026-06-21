import shutil
import subprocess
import sys
from pathlib import Path

from .errors import TranscodeError

_EXE = ".exe" if sys.platform == "win32" else ""


def _resolve_ffmpeg() -> str:
    if getattr(sys, "frozen", False):
        candidate = Path(sys._MEIPASS) / f"ffmpeg{_EXE}"
        if candidate.exists():
            return str(candidate)

    bundled = (
        Path(__file__).resolve().parent.parent
        / "ffmpeg"
        / _detect_platform()
        / f"ffmpeg{_EXE}"
    )
    if bundled.exists():
        return str(bundled)

    path = shutil.which("ffmpeg")
    if path:
        return path
    raise TranscodeError("未找到 ffmpeg，请将其加入 PATH")


def _detect_platform() -> str:
    if sys.platform == "win32":
        return "win-x64"
    elif sys.platform == "linux":
        return "linux-x64"
    elif sys.platform == "darwin":
        return "darwin-arm64"
    else:
        raise TranscodeError(f"不支持的操作系统: {sys.platform}")


def transcode(audio_path: Path, output_dir: Path) -> Path:
    audio_path = Path(audio_path)
    if audio_path.suffix.lower() == ".wav":
        return audio_path
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / (audio_path.stem + ".wav")
    ffmpeg = _resolve_ffmpeg()
    cmd = [
        ffmpeg, "-y", "-i", str(audio_path),
        "-vn", "-ar", "16000", "-ac", "1", str(out),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not out.exists():
        raise TranscodeError(
            "ffmpeg 转码失败: " + result.stderr.decode("utf-8", errors="ignore")
        )
    return out
