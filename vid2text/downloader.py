import re
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from .errors import NetworkError
from .errors import UserError

_BV_RE = re.compile(r"BV[0-9A-Za-z]{10}")


def extract_bvid(text: str) -> str:
    m = _BV_RE.search(text)
    if not m:
        raise UserError(f"无法从输入中提取 BV 号: {text}")
    return m.group(0)


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def _api_get(url: str) -> dict:
    req = Request(url, headers=_HEADERS)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        raise NetworkError(f"请求 B站 API 失败: {url}") from e


def _get_cid(bvid: str) -> int:
    data = _api_get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    if data.get("code") != 0:
        raise NetworkError(f"获取视频信息失败: {data.get('message')}")
    return data["data"]["cid"]


def _get_audio_url(bvid: str, cid: int) -> str:
    url = (
        "https://api.bilibili.com/x/player/playurl"
        f"?bvid={bvid}&cid={cid}&qn=0&fnval=4048&fourk=1"
    )
    data = _api_get(url)
    if data.get("code") != 0:
        raise NetworkError(f"获取播放地址失败: {data.get('message')}")
    try:
        return data["data"]["dash"]["audio"][0]["baseUrl"]
    except (KeyError, IndexError):
        raise NetworkError("未找到可用的音频流")
