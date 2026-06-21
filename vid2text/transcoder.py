import shutil
import subprocess
import sys
from pathlib import Path

from .errors import TranscodeError


def _resolve_ffmpeg() -> str:
    if getattr(sys, "frozen", False):
        candidate = Path(sys._MEIPASS) / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
    path = shutil.which("ffmpeg")
    if path:
        return path
    raise TranscodeError("未找到 ffmpeg，请将其加入 PATH")


def transcode(audio_path: Path, output_dir: Path) -> Path:
    audio_path = Path(audio_path)
    if audio_path.suffix.lower() == ".wav":
        return audio_path
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / (audio_path.stem + ".wav")
    ffmpeg = _resolve_ffmpeg()
    cmd = [
        ffmpeg, "-y", "-i", str(audio_path),
        "-vn", "-ar", "16000", "-ac", "1", "-f", "wav", str(out),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not out.exists():
        raise TranscodeError(
            "ffmpeg 转码失败: " + result.stderr.decode("utf-8", errors="ignore")
        )
    return out
