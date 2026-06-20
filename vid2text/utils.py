from __future__ import annotations

import dataclasses
import logging
import pathlib


class Vid2TextError(Exception):
    """所有 vid2text 异常基类。"""


class UserError(Vid2TextError):
    """用户输入问题：URL 无效、文件不存在、参数非法。"""


class DependencyError(Vid2TextError):
    """外部工具问题：yt-dlp/ffmpeg 未安装或执行失败。"""


class ModelError(Vid2TextError):
    """ASR 模型问题：加载失败、推理异常。"""


@dataclasses.dataclass(frozen=True)
class DownloadResult:
    video_id: str
    audio_path: pathlib.Path
    duration_sec: float


@dataclasses.dataclass(frozen=True)
class TranscodeResult:
    audio_path: pathlib.Path
    src_format: str
    dst_format: str


@dataclasses.dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    confidence: float


@dataclasses.dataclass(frozen=True)
class RecognitionResult:
    model_alias: str
    language: str
    duration_sec: float
    segments: list[Segment]
    text: str
    video_id: str | None = None
    source_url: str | None = None
    content_hash: str | None = None


def make_logger(name: str, verbose: int = 0) -> logging.Logger:
    logger = logging.getLogger(f"vid2text.{name}")
    level = logging.DEBUG if verbose >= 1 else logging.INFO
    logger.setLevel(level)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
        logger.addHandler(h)
    return logger
