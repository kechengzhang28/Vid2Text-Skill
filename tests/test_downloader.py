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
