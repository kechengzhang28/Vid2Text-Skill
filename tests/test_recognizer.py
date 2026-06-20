from vid2text import recognizer, utils


def test_model_mapping():
    assert recognizer.resolve_model("paraformer").asr_id.startswith("iic/speech_paraformer")
    assert recognizer.resolve_model("sensevoice").asr_id == "iic/Speech_SENSE_Voice_Small"


def test_invalid_alias():
    import pytest

    with pytest.raises(utils.UserError):
        recognizer.resolve_model("whisper")


def test_recognize_returns_result(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"\x00" * 44)

    class FakeModel:
        def generate(self, input, **k):
            return [{"text": "你好", "timestamp": [[0, 2000]], "confidence": 0.9}]

    monkeypatch.setattr(recognizer, "_load_auto_model", lambda spec: FakeModel())
    res = recognizer.recognize(audio, model_alias="paraformer", cache=None)
    assert res.model_alias == "paraformer"
    assert res.language == "zh"
    assert res.segments[0].text == "你好"
