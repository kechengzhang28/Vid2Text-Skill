from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from vid2text import asr
from vid2text.errors import ModelError


def test_detect_arch_darwin_arm64(monkeypatch):
    monkeypatch.setattr(asr.sys, "platform", "darwin")
    monkeypatch.setattr(asr.os, "uname", lambda: type("u", (), {"machine": "arm64"})())
    assert asr._detect_arch() == "darwin-arm64"


def test_detect_arch_darwin_x64(monkeypatch):
    monkeypatch.setattr(asr.sys, "platform", "darwin")
    monkeypatch.setattr(asr.os, "uname", lambda: type("u", (), {"machine": "x86_64"})())
    assert asr._detect_arch() == "darwin-x64"


def test_detect_arch_linux(monkeypatch):
    monkeypatch.setattr(asr.sys, "platform", "linux")
    assert asr._detect_arch() == "linux-x64"


def test_detect_arch_windows(monkeypatch):
    monkeypatch.setattr(asr.sys, "platform", "win32")
    assert asr._detect_arch() == "win-x64"


def test_detect_arch_unsupported(monkeypatch):
    monkeypatch.setattr(asr.sys, "platform", "freebsd")
    with pytest.raises(ModelError, match="不支持的操作系统"):
        asr._detect_arch()


def test_parse_output_single_line():
    stdout = "[0.54-3.78] 甚至出现交易几乎停滞的情况。"
    assert asr._parse_output(stdout) == "甚至出现交易几乎停滞的情况。"


def test_parse_output_multi_line():
    stdout = "[0.00-1.00] 第一句。\n[1.00-2.00] 第二句。"
    assert asr._parse_output(stdout) == "第一句。\n第二句。"


def test_parse_output_empty_lines():
    stdout = "[0.00-1.00] 文本。\n\n[1.00-2.00] 更多。"
    assert asr._parse_output(stdout) == "文本。\n更多。"


def test_transcribe_success(tmp_path, monkeypatch):
    monkeypatch.setattr(asr, "_binary_path", lambda: Path("/fake/sense-voice"))
    monkeypatch.setattr(asr, "_model_path", lambda: Path("/fake/model.gguf"))

    mock_run = MagicMock()
    mock_run.return_value.stdout = "[0.54-3.78] 甚至出现交易几乎停滞的情况。"
    mock_run.return_value.stderr = ""
    mock_run.return_value.returncode = 0
    monkeypatch.setattr(asr.subprocess, "run", mock_run)

    text = asr.transcribe(Path(tmp_path) / "a.wav")

    assert text == "甚至出现交易几乎停滞的情况。"
    mock_run.assert_called_once()


def test_transcribe_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(asr, "_binary_path", lambda: Path("/fake/sense-voice"))
    monkeypatch.setattr(asr, "_model_path", lambda: Path("/fake/model.gguf"))

    mock_run = MagicMock()
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = "error: failed to read WAV file"
    mock_run.return_value.returncode = 2
    monkeypatch.setattr(asr.subprocess, "run", mock_run)

    with pytest.raises(ModelError, match="ASR 推理失败"):
        asr.transcribe(Path(tmp_path) / "a.wav")


def test_binary_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(asr, "_BINARY_DIR", Path("/nonexistent"))
    with pytest.raises(ModelError, match="未找到 ASR 二进制文件"):
        asr._binary_path()


def test_model_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(asr, "_MODEL_DIR", Path("/nonexistent"))
    with pytest.raises(ModelError, match="未找到 ASR 模型文件"):
        asr._model_path()
