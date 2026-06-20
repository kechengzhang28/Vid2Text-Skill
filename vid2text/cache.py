from __future__ import annotations

import hashlib
import pathlib


def content_hash(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def text_key(content_hash: str, model_alias: str) -> str:
    return f"{content_hash}-{model_alias}"


class Cache:
    def __init__(self, root: pathlib.Path):
        self.root = pathlib.Path(root)
        (self.root / "audio").mkdir(parents=True, exist_ok=True)
        (self.root / "text").mkdir(parents=True, exist_ok=True)

    def _text_path(self, key: str) -> pathlib.Path:
        return self.root / "text" / f"{key}.txt"

    def write_text(self, key: str, text: str) -> pathlib.Path:
        path = self._text_path(key)
        path.write_text(text, encoding="utf-8")
        return path

    def read_text(self, key: str) -> str | None:
        path = self._text_path(key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_entries(self) -> list[str]:
        return sorted(p.name for p in (self.root / "text").glob("*.txt"))

    def clear(self) -> None:
        for sub in ("audio", "text"):
            for p in (self.root / sub).glob("*"):
                p.unlink()
