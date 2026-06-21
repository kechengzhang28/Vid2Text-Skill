import re

from .errors import UserError

_BV_RE = re.compile(r"BV[0-9A-Za-z]{10}")


def extract_bvid(text: str) -> str:
    m = _BV_RE.search(text)
    if not m:
        raise UserError(f"无法从输入中提取 BV 号: {text}")
    return m.group(0)
