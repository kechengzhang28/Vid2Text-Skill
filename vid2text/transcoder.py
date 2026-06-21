import shutil
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
