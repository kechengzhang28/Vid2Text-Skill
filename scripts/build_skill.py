import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SRC = ROOT / "vid2text"
INIT = SRC / "__init__.py"
SKILL_MD = ROOT / "SKILL.md"
PYPROJECT = ROOT / "pyproject.toml"
BIN = ROOT / "bin"
MODELS = ROOT / "models"
DIST = ROOT / "dist"

_MODEL_FILE = "sense-voice-small-q4_k.gguf"

_EXPECTED_PY = {"__init__.py", "asr.py", "cli.py", "downloader.py", "errors.py", "transcoder.py"}


def _read_version() -> str:
    text = INIT.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not m:
        raise ValueError(f"无法从 {INIT} 提取 __version__")
    return m.group(1)


def _collect_arch_dirs() -> list[str]:
    if not BIN.exists():
        return []
    return [d.name for d in BIN.iterdir() if d.is_dir()]


def build() -> Path:
    version = _read_version()
    DIST.mkdir(parents=True, exist_ok=True)
    artifact = DIST / f"vid2text-{version}.skill"

    with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(SKILL_MD, "SKILL.md")
        zf.write(PYPROJECT, "pyproject.toml")

        for py in sorted(SRC.glob("*.py")):
            zf.write(py, f"vid2text/{py.name}")

        model_path = MODELS / _MODEL_FILE
        if model_path.exists():
            zf.write(model_path, f"models/{_MODEL_FILE}")

        for arch_dir in _collect_arch_dirs():
            arch_bin_dir = BIN / arch_dir
            for binary in arch_bin_dir.iterdir():
                if binary.is_file():
                    zf.write(binary, f"bin/{arch_dir}/{binary.name}")

    actual = set(zipfile.ZipFile(artifact).namelist())

    if "SKILL.md" not in actual:
        raise RuntimeError("产物缺少 SKILL.md")
    if "pyproject.toml" not in actual:
        raise RuntimeError("产物缺少 pyproject.toml")
    if not any(e.startswith("vid2text/") for e in actual):
        raise RuntimeError("产物缺少 vid2text/ 目录")

    print(f"Built: {artifact}")
    return artifact


if __name__ == "__main__":
    build()
