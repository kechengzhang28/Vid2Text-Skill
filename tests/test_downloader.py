import pytest

from vid2text import downloader
from vid2text.errors import UserError


def test_extract_bvid_from_full_url():
    assert downloader.extract_bvid("https://www.bilibili.com/video/BV1wDEK6MEM2") == "BV1wDEK6MEM2"


def test_extract_bvid_bare():
    assert downloader.extract_bvid("BV1wDEK6MEM2") == "BV1wDEK6MEM2"


def test_extract_bvid_with_query():
    assert downloader.extract_bvid("https://www.bilibili.com/video/BV1wDEK6MEM2?t=30&spm=xx") == "BV1wDEK6MEM2"


def test_extract_bvid_no_match():
    with pytest.raises(UserError):
        downloader.extract_bvid("https://youtube.com/watch?v=abc")


from vid2text.errors import NetworkError


def test_get_cid_success(monkeypatch):
    monkeypatch.setattr(downloader, "_api_get", lambda url: {"code": 0, "data": {"cid": 12345}})
    assert downloader._get_cid("BV1wDEK6MEM2") == 12345


def test_get_cid_api_error(monkeypatch):
    monkeypatch.setattr(downloader, "_api_get", lambda url: {"code": -400, "message": "无效"})
    with pytest.raises(NetworkError):
        downloader._get_cid("BV1wDEK6MEM2")


def test_get_audio_url_success(monkeypatch):
    monkeypatch.setattr(
        downloader, "_api_get",
        lambda url: {"code": 0, "data": {"dash": {"audio": [{"baseUrl": "https://x/audio.m4a"}]}}},
    )
    assert downloader._get_audio_url("BV1wDEK6MEM2", 12345) == "https://x/audio.m4a"


def test_get_audio_url_empty(monkeypatch):
    monkeypatch.setattr(downloader, "_api_get", lambda url: {"code": 0, "data": {"dash": {"audio": []}}})
    with pytest.raises(NetworkError):
        downloader._get_audio_url("BV1wDEK6MEM2", 12345)


def test_download_bilibili_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "_get_cid", lambda b: 1)
    monkeypatch.setattr(downloader, "_get_audio_url", lambda b, c: "https://x/a.m4a")

    def fake_dl(url, dest):
        dest.write_bytes(b"audio-bytes")
    monkeypatch.setattr(downloader, "_download_to_file", fake_dl)

    p = downloader._download_bilibili(
        "https://www.bilibili.com/video/BV1wDEK6MEM2", tmp_path
    )
    assert p.name == "BV1wDEK6MEM2.m4a"
    assert p.read_bytes() == b"audio-bytes"


def test_download_dispatches_full_url(tmp_path, monkeypatch):
    seen = {}
    def fake(text, out):
        seen["bvid"] = downloader.extract_bvid(text)
        out.mkdir(parents=True, exist_ok=True)
        return out / "x.m4a"
    monkeypatch.setattr(downloader, "_download_bilibili", fake)
    downloader.download("https://www.bilibili.com/video/BV1wDEK6MEM2", tmp_path)
    assert seen["bvid"] == "BV1wDEK6MEM2"


def test_download_dispatches_bare_bvid(tmp_path, monkeypatch):
    seen = {}
    def fake(text, out):
        seen["bvid"] = downloader.extract_bvid(text)
        return out / "x.m4a"
    monkeypatch.setattr(downloader, "_download_bilibili", fake)
    downloader.download("BV1wDEK6MEM2", tmp_path)
    assert seen["bvid"] == "BV1wDEK6MEM2"


def test_download_unsupported_platform(tmp_path):
    with pytest.raises(NetworkError):
        downloader.download("https://youtube.com/watch?v=abc", tmp_path)
