import pytest

from vid2text import pipeline, utils
from vid2text.cache import Cache, content_hash, text_key


def _spy(monkeypatch, order, name, result):
    def _impl(*a, **k):
        order.append(name)
        return result

    monkeypatch.setattr(pipeline, name, _impl)


def test_pipeline_runs_stages_in_order(monkeypatch, tmp_path):
    order: list[str] = []
    dl = utils.DownloadResult("BV1xx", tmp_path / "a.wav", 12.0)
    tc = utils.TranscodeResult(tmp_path / "a.wav", "m4a", "wav")
    rc = utils.RecognitionResult(
        model_alias="paraformer",
        language="zh",
        duration_sec=12.0,
        segments=[utils.Segment(0, 2, "你好", 0.9)],
        text="你好",
        video_id="BV1xx",
        source_url="https://x",
    )
    _spy(monkeypatch, order, "download", dl)
    _spy(monkeypatch, order, "transcode", tc)
    _spy(monkeypatch, order, "recognize", rc)

    pipeline.run(
        "https://www.bilibili.com/video/BV1xx",
        model_alias="paraformer",
        no_cache=True,
        cache_root=tmp_path / "cache",
    )
    assert order == ["download", "transcode", "recognize"]


def test_pipeline_transcribe_cache_hit_skips_recognize(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"\x00" * 44)
    c_hash = content_hash(audio)
    cache = Cache(tmp_path / "cache")
    cache.write_text(text_key(c_hash, "paraformer"), "预置转写结果")
    order: list[str] = []
    tc = utils.TranscodeResult(audio.with_suffix(".wav"), "wav", "wav")
    _spy(monkeypatch, order, "transcode", tc)

    rec_result = pipeline.transcribe_file(
        audio, model_alias="paraformer", cache_root=tmp_path / "cache"
    )
    assert rec_result.text == "预置转写结果"
    assert rec_result.model_alias == "paraformer"
    assert order == ["transcode"]


def test_pipeline_transcode_failure_aborts(monkeypatch, tmp_path):
    order: list[str] = []
    dl = utils.DownloadResult("BV1xx411c7mD", tmp_path / "a.wav", 12.0)
    _spy(monkeypatch, order, "download", dl)

    def fake_transcode(*a, **k):
        order.append("transcode")
        raise utils.DependencyError("ffmpeg failed")

    monkeypatch.setattr(pipeline, "transcode", fake_transcode)
    _spy(
        monkeypatch,
        order,
        "recognize",
        utils.RecognitionResult("paraformer", "zh", 0.0, [], ""),
    )

    with pytest.raises(utils.DependencyError):
        pipeline.run(
            "https://www.bilibili.com/video/BV1xx411c7mD",
            model_alias="paraformer",
            no_cache=True,
            cache_root=tmp_path / "cache",
        )
    assert order == ["download", "transcode"]
