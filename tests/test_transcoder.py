from pathlib import Path

import pytest

from vid2text import transcoder
from vid2text.errors import TranscodeError


def test_transcode_skips_wav(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"wav")
    assert transcoder.transcode(wav, tmp_path) == wav


def test_transcode_success(tmp_path, monkeypatch):
    src = tmp_path / "a.m4a"
    src.write_bytes(b"x")
    out = tmp_path / "a.wav"

    class FakeFrame:
        pass

    class FakePacket:
        pass

    class FakeResampler:
        def resample(self, frame):
            return [frame]

    class FakeOutputStream:
        def encode(self, frame=None):
            return [FakePacket()]

    class FakeOutputContainer:
        def add_stream(self, *args, **kwargs):
            return FakeOutputStream()

        def mux(self, packet):
            pass

        def close(self):
            pass

    class FakeInputStream:
        audio = [object()]

    class FakeInputContainer:
        def __init__(self, path):
            pass

        @property
        def streams(self):
            return FakeInputStream()

        def decode(self, audio=0):
            return [FakeFrame()]

        def close(self):
            pass

    monkeypatch.setattr(transcoder.av, "open", lambda path, mode=None: (
        FakeInputContainer(path) if mode is None else FakeOutputContainer()
    ))
    monkeypatch.setattr(
        transcoder.av.audio.resampler, "AudioResampler",
        lambda **kw: FakeResampler(),
    )

    result = transcoder.transcode(src, tmp_path)
    assert result.name == "a.wav"


def test_transcode_failure_raises(tmp_path, monkeypatch):
    src = tmp_path / "a.m4a"
    src.write_bytes(b"x")

    def boom(path, mode=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(transcoder.av, "open", boom)
    with pytest.raises(TranscodeError):
        transcoder.transcode(src, tmp_path)
