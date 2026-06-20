from __future__ import annotations

import pathlib

from vid2text import utils
from vid2text.cache import Cache
from vid2text.downloader import download
from vid2text.recognizer import recognize
from vid2text.transcoder import transcode


def run(
    url: str,
    *,
    model_alias: str,
    format: str = "txt",
    language: str = "auto",
    no_cache: bool = False,
    cache_root: pathlib.Path,
) -> utils.RecognitionResult:
    cache = Cache(cache_root)

    dl = download(url, cache=cache, cache_root=cache_root)

    tc = transcode(dl.audio_path, dst_format="wav")

    _cache = None if no_cache else cache
    rec = recognize(tc.audio_path, model_alias=model_alias, cache=_cache)

    return utils.RecognitionResult(
        model_alias=rec.model_alias,
        language=rec.language,
        duration_sec=rec.duration_sec,
        segments=rec.segments,
        text=rec.text,
        video_id=dl.video_id,
        source_url=url,
        content_hash=rec.content_hash,
    )


def transcribe_file(
    audio_path: pathlib.Path,
    *,
    model_alias: str,
    format: str = "txt",
    language: str = "auto",
    no_cache: bool = False,
    cache_root: pathlib.Path,
) -> utils.RecognitionResult:
    cache = Cache(cache_root)

    tc = transcode(audio_path, dst_format="wav")

    _cache = None if no_cache else cache
    rec = recognize(tc.audio_path, model_alias=model_alias, cache=_cache)

    return rec
