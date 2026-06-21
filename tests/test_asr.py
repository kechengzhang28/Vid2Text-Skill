import sys
import types

import pytest

from vid2text import asr


def test_ensure_models_downloads_and_loads_once(monkeypatch):
    monkeypatch.setattr(asr, "_models", {})
    calls = {"download": 0, "load": 0}

    def fake_download(model_id, revision=None):
        calls["download"] += 1
        return f"/models/{model_id}"

    class FakeModel:
        def __init__(self, *a, **k):
            calls["load"] += 1

    fake_hub = types.ModuleType("modelscope.hub")
    fake_hub.snapshot_download = fake_download
    fake_ms = types.ModuleType("modelscope")
    fake_ms.hub = fake_hub
    fake_fun = types.ModuleType("funasr_onnx")
    fake_fun.Paraformer = FakeModel
    fake_fun.Fsmn_vad = FakeModel
    fake_fun.CT_Transformer = FakeModel
    monkeypatch.setitem(sys.modules, "modelscope", fake_ms)
    monkeypatch.setitem(sys.modules, "modelscope.hub", fake_hub)
    monkeypatch.setitem(sys.modules, "funasr_onnx", fake_fun)

    asr._ensure_models()
    asr._ensure_models()

    assert calls["download"] == 3
    assert calls["load"] == 3
    assert set(asr._models.keys()) == {"paraformer", "vad", "punc"}


from unittest.mock import MagicMock

from vid2text.errors import ModelError


def test_transcribe_paraformer_then_punc(tmp_path, monkeypatch):
    monkeypatch.setattr(asr, "_models", {})
    para = MagicMock(return_value=[{"preds": ("你好世界", ["你好", "世界"])}])
    punc = MagicMock(return_value=("你好世界。", ["。"]))
    monkeypatch.setattr(asr, "_ensure_models", lambda: None)
    monkeypatch.setitem(asr._models, "paraformer", para)
    monkeypatch.setitem(asr._models, "punc", punc)

    text = asr.transcribe(tmp_path / "a.wav")

    assert text == "你好世界。"
    para.assert_called_once()
    punc.assert_called_once_with("你好世界")


def test_transcribe_inference_error_wrapped(tmp_path, monkeypatch):
    monkeypatch.setattr(asr, "_models", {})
    para = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(asr, "_ensure_models", lambda: None)
    monkeypatch.setitem(asr._models, "paraformer", para)
    with pytest.raises(ModelError):
        asr.transcribe(tmp_path / "a.wav")
