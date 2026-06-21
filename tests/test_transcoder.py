import pytest

from vid2text import transcoder
from vid2text.errors import TranscodeError


def test_resolve_ffmpeg_from_path(monkeypatch):
    monkeypatch.setattr(transcoder.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert transcoder._resolve_ffmpeg() == "/usr/bin/ffmpeg"


def test_resolve_ffmpeg_missing(monkeypatch):
    monkeypatch.setattr(transcoder.shutil, "which", lambda name: None)
    monkeypatch.setattr(transcoder.sys, "frozen", False, raising=False)
    with pytest.raises(TranscodeError):
        transcoder._resolve_ffmpeg()
