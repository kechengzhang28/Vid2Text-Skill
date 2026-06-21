from pathlib import Path

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


import subprocess


def test_transcode_skips_wav(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"wav")
    assert transcoder.transcode(wav, tmp_path) == wav


def test_transcode_success(tmp_path, monkeypatch):
    monkeypatch.setattr(transcoder, "_resolve_ffmpeg", lambda: "/usr/bin/ffmpeg")
    src = tmp_path / "a.m4a"
    src.write_bytes(b"x")

    def fake_run(cmd, capture_output):
        Path(cmd[-1]).write_bytes(b"wav-out")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(transcoder.subprocess, "run", fake_run)
    out = transcoder.transcode(src, tmp_path)
    assert out.suffix == ".wav"
    assert out.read_bytes() == b"wav-out"


def test_transcode_failure_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(transcoder, "_resolve_ffmpeg", lambda: "/usr/bin/ffmpeg")
    src = tmp_path / "a.m4a"
    src.write_bytes(b"x")
    monkeypatch.setattr(
        transcoder.subprocess, "run",
        lambda cmd, capture_output: subprocess.CompletedProcess(cmd, 1, stderr=b"err"),
    )
    with pytest.raises(TranscodeError):
        transcoder.transcode(src, tmp_path)
