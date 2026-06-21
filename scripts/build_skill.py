import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SRC = ROOT / "vid2text"
INIT = SRC / "__init__.py"
SKILL_MD = ROOT / "SKILL.md"
PYPROJECT = ROOT / "pyproject.toml"
DIST = ROOT / "dist"

EXPECTED = {
    "SKILL.md",
    "pyproject.toml",
    "vid2text/__init__.py",
    "vid2text/asr.py",
    "vid2text/cli.py",
    "vid2text/downloader.py",
    "vid2text/errors.py",
    "vid2text/transcoder.py",
}


def _read_version() -> str:
    text = INIT.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise ValueError(f"无法从 {INIT} 提取 __version__")
    return m.group(1)


def build() -> Path:
    version = _read_version()
    DIST.mkdir(parents=True, exist_ok=True)
    artifact = DIST / f"vid2text-{version}.skill"

    with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(SKILL_MD, "SKILL.md")
        zf.write(PYPROJECT, "pyproject.toml")
        for py in sorted(SRC.glob("*.py")):
            zf.write(py, f"vid2text/{py.name}")

    actual = set(zipfile.ZipFile(artifact).namelist())
    assert actual == EXPECTED, f"产物文件列表不匹配:\n  实际: {sorted(actual)}\n  预期: {sorted(EXPECTED)}"

    print(f"Built: {artifact}")
    return artifact


if __name__ == "__main__":
    build()
