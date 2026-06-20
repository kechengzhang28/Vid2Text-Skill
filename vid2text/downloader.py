from __future__ import annotations

import pathlib
import re
import urllib.parse

import yt_dlp

from vid2text import utils
from vid2text.cache import Cache

_BILI = re.compile(r"BV[0-9A-Za-z]{10}")


def extract_video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise utils.UserError(f"无效 URL: {url}")
    m = _BILI.search(url)
    if m:
        return m.group(0)
    if "youtu" in parsed.netloc:
        q = urllib.parse.parse_qs(parsed.query)
        if "v" in q:
            return q["v"][0]
    raise utils.UserError(f"无法识别 video_id: {url}")


def download(url: str, *, cache: Cache, cache_root: pathlib.Path) -> utils.DownloadResult:
    video_id = extract_video_id(url)
    cached = cache.find_audio(video_id)
    if cached is not None:
        return utils.DownloadResult(
            video_id=video_id,
            audio_path=cached,
            duration_sec=0.0,
        )
    try:
        ydl_opts = {  # pyright: ignore[reportUnknownVariableType]
            "format": "bestaudio/best",
            "outtmpl": str(cache_root / "audio" / "%(id)s.%(ext)s"),
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            info = ydl.extract_info(url, download=True)  # pyright: ignore[reportAssignmentType]
            ext: str = info.get("ext") or "wav"
            audio_path = cache.audio_path(video_id, ext)
            duration = float(info.get("duration") or 0)
            return utils.DownloadResult(
                video_id=video_id,
                audio_path=pathlib.Path(audio_path),
                duration_sec=duration,
            )
    except yt_dlp.utils.DownloadError as e:  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        raise utils.DependencyError(f"下载失败: {e}") from e
