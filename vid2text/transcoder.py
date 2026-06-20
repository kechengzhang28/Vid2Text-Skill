from __future__ import annotations

import pathlib
import subprocess

from vid2text import utils


def transcode(src: pathlib.Path, dst_format: str = "wav") -> utils.TranscodeResult:
    dst = src.with_suffix(f".{dst_format}")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vn", "-ar", "16000", "-ac", "1", "-f", dst_format,
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError as e:
        raise utils.DependencyError("ffmpeg 未安装或不在 PATH") from e
    except subprocess.CalledProcessError as e:
        stderr_text = ""
        if e.stderr is not None:
            stderr_text = e.stderr.decode(errors="ignore")
        raise utils.DependencyError(f"ffmpeg 转码失败: {stderr_text}") from e
    return utils.TranscodeResult(
        audio_path=dst, src_format=src.suffix.lstrip("."), dst_format=dst_format
    )
