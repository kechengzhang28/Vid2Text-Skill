import pathlib
import zipfile

from vid2text import __version__


def build():
    root = pathlib.Path(__file__).resolve().parent.parent
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    skill_path = dist / f"vid2text-{__version__}.skill"

    sources = {
        root / "SKILL.md": "SKILL.md",
        root / "pyproject.toml": "pyproject.toml",
        root / "README.md": "README.md",
    }

    src_dir = root / "vid2text"
    source_py = sorted(src_dir.glob("*.py"))

    with zipfile.ZipFile(skill_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in sources.items():
            zf.write(path, arcname)
        for py_file in source_py:
            zf.write(py_file, f"vid2text/{py_file.name}")

    print(f"Built: {skill_path}")

    with zipfile.ZipFile(skill_path) as zf:
        names = zf.namelist()
        expected = {"SKILL.md", "pyproject.toml", "README.md"}.union(
            f"vid2text/{p.name}" for p in source_py
        )
        assert set(names) == expected, f"Missing files: {expected - set(names)}"

    print(f"Verified: {len(names)} files in archive")


if __name__ == "__main__":
    build()
