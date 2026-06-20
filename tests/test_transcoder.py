import subprocess

import pytest

from vid2text import transcoder, utils


def test_transcode_invokes_ffmpeg(tmp_path, monkeypatch):
    src = tmp_path / "in.m4a"
    src.write_bytes(b"")
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(transcoder.subprocess, "run", fake_run)
    result = transcoder.transcode(src, dst_format="wav")
    assert result.dst_format == "wav"
    assert "-ar" in calls["cmd"] and "16000" in calls["cmd"]
    assert "-ac" in calls["cmd"] and "1" in calls["cmd"]


def test_transcode_failure_raises_dependency(monkeypatch, tmp_path):
    src = tmp_path / "in.m4a"
    src.write_bytes(b"")

    def boom(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(transcoder.subprocess, "run", boom)
    with pytest.raises(utils.DependencyError):
        transcoder.transcode(src, "wav")
