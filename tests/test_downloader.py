import pytest

from vid2text import downloader, utils
from vid2text.cache import Cache


@pytest.mark.parametrize(
    "url,vid",
    [
        ("https://www.bilibili.com/video/BV1xx411c7mD", "BV1xx411c7mD"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_extract_video_id(url, vid):
    assert downloader.extract_video_id(url) == vid


def test_invalid_url_raises_user_error():
    with pytest.raises(utils.UserError):
        downloader.extract_video_id("not a url")


def test_download_cache_hit_short_circuits(tmp_path, monkeypatch):
    c = Cache(tmp_path / "cache")
    called = {"dl": False}

    class FakeYDL:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def extract_info(self, url, download):
            called["dl"] = download
            return {"id": "BV1xx"}

        def download(self, _):
            called["dl"] = True

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYDL)
    (tmp_path / "cache" / "audio" / "BV1xx411c7mD.wav").write_bytes(b"\x00" * 44)
    downloader.download(
        "https://www.bilibili.com/video/BV1xx411c7mD",
        cache=c,
        cache_root=tmp_path / "cache",
    )
    assert called["dl"] is False
