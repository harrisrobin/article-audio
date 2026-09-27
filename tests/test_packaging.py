import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from uuid import uuid4


def test_release_builds_exclude_unlisted_private_files(tmp_path):
    root = Path(__file__).resolve().parents[1]
    project = tmp_path / "project"
    shutil.copytree(
        root,
        project,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".bootstrap",
            "dist",
            "artifacts",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
        ),
    )
    marker = f"PRIVATE ARTICLE {uuid4()}".encode()
    for name in ("docs/private.txt", "examples/private.md", "src/article_audio/private.txt"):
        (project / name).write_bytes(marker)
    subprocess.run(
        [sys.executable, "scripts/package.py"], cwd=project, check=True, capture_output=True
    )
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=project,
        check=True,
        capture_output=True,
    )
    checked = []
    for archive in (project / "dist").iterdir():
        if archive.suffix in (".zip", ".whl"):
            with zipfile.ZipFile(archive) as bundle:
                contents = [bundle.read(name) for name in bundle.namelist()]
        elif archive.name.endswith(".tar.gz"):
            with tarfile.open(archive) as bundle:
                contents = [bundle.extractfile(item).read() for item in bundle if item.isfile()]
        else:
            continue
        assert all(marker not in content for content in contents), archive.name
        checked.append(archive.name)
    assert len(checked) == 3
