"""Build a source archive from an allowlist, never from the whole workspace."""

import hashlib
import stat
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    target = ROOT / "dist"
    target.mkdir(exist_ok=True)
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    archive = target / f"article-audio-{config['project']['version']}.zip"
    paths = [ROOT / file for file in config["tool"]["hatch"]["build"]["only-include"]]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(paths):
            if not path.is_file() or path.resolve() != path.absolute():
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
