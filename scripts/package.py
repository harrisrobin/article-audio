"""Build a source archive from an allowlist, never from the whole workspace."""

import hashlib
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "SECURITY.md", ".gitignore")
DIRECTORIES = ("src", "tests", "scripts", "skills", "template", "docs", "examples", ".github")
EXTENSIONS = {".py", ".md", ".sh", ".yml", ".yaml", ".txt"}


def main():
    target = ROOT / "dist"
    target.mkdir(exist_ok=True)
    archive = target / "article-audio-0.1.0.zip"
    paths = [ROOT / file for file in FILES]
    for directory in DIRECTORIES:
        paths.extend(
            path
            for path in (ROOT / directory).rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and (path.suffix in EXTENSIONS or path.name == "article-audio")
            and "__pycache__" not in path.parts
        )
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(paths):
            if not path.is_file() or path.is_symlink():
                raise RuntimeError("Missing or unsafe release input")
            info = zipfile.ZipInfo(f"article-audio/{path.relative_to(ROOT)}")
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = path.suffix == ".sh" or path.name == "article-audio"
            info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
            bundle.writestr(info, path.read_bytes())
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive.name}\n")
    print(f"{archive}\nSHA256 {checksum}")


if __name__ == "__main__":
    main()
