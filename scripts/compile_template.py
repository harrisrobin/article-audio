"""Compile a public Grok template bundle from one verified GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import string
import sys
import tempfile
import tomllib
import zipfile
import zlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

REPOSITORY = "harrisrobin/article-audio"
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
ARCHIVE_PREFIX = "article-audio/"
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024
MAX_API_BYTES = 1024 * 1024
MAX_ARCHIVE_MEMBERS = 128
MAX_MEMBER_BYTES = 1024 * 1024
MAX_EXPANDED_BYTES = 8 * 1024 * 1024
MAX_TAG_HOPS = 8
REQUIRED_SKILLS = (
    ("article-audio", "skills/article-audio/SKILL.md"),
    ("article-audio-onboarding", "skills/article-audio-onboarding/SKILL.md"),
)
MEMORY_IDS = ("release", "first_message", "setup_and_privacy", "narration_scope")
RELEASE_FIELDS = {
    "repository_url",
    "tag",
    "commit_sha",
    "zip_url",
    "zip_sha256",
}
SHA1_RE = re.compile(r"[0-9a-f]{40}")
TAG_RE = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
TEMPLATE_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
PLACEHOLDER_RE = re.compile(r"(?:FILE\s*:\s*\S+|\$\{[^{}]+\}|\{\{[^{}]+\}\})", re.IGNORECASE)


class CompileError(RuntimeError):
    """A safe, user-facing compiler failure."""


@dataclass(frozen=True)
class VerifiedRelease:
    tag: str
    version: str
    commit_sha: str
    zip_name: str
    zip_url: str
    zip_sha256: str
    files: dict[str, bytes]


@dataclass(frozen=True)
class BundlePaths:
    bundle: Path
    checksum: Path
    commit_sha: str
    zip_sha256: str
    bundle_sha256: str


def _get_json(client: httpx.Client, url: str) -> dict[str, Any]:
    try:
        with client.stream(
            "GET",
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        ) as response:
            response.raise_for_status()
            content = _read_response(response, MAX_API_BYTES, "GitHub metadata")
        value = json.loads(content)
    except (httpx.HTTPError, ValueError):
        raise CompileError("GitHub request failed") from None
    if not isinstance(value, dict):
        raise CompileError("GitHub returned invalid metadata")
    return value


def _read_response(response: httpx.Response, limit: int, subject: str) -> bytes:
    declared = response.headers.get("content-length")
    if declared and (not declared.isdigit() or int(declared) > limit):
        raise CompileError(f"{subject} exceeds the size limit")
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_bytes():
        size += len(chunk)
        if size > limit:
            raise CompileError(f"{subject} exceeds the size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _download(client: httpx.Client, url: str, limit: int) -> bytes:
    try:
        with client.stream(
            url=url, method="GET", headers={"Accept": "application/octet-stream"}
        ) as response:
            response.raise_for_status()
            content = _read_response(response, limit, "Release asset")
    except CompileError:
        raise
    except httpx.HTTPError:
        raise CompileError("GitHub request failed") from None
    return content


def _release_assets(release: dict[str, Any], tag: str, version: str) -> tuple[dict, dict]:
    if release.get("tag_name") != tag:
        raise CompileError("GitHub release tag does not match the requested release tag")
    if (
        release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(release.get("published_at"), str)
        or not release["published_at"]
    ):
        raise CompileError("release is not a published stable release")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise CompileError("release assets are missing or ambiguous")
    zip_name = f"article-audio-{version}.zip"
    names = (zip_name, f"{zip_name}.sha256")
    selected: list[dict[str, Any]] = []
    for name in names:
        matches = [
            asset for asset in assets if isinstance(asset, dict) and asset.get("name") == name
        ]
        if len(matches) != 1 or matches[0].get("state") != "uploaded":
            raise CompileError("release assets are missing or ambiguous")
        asset_id = matches[0].get("id")
        url = matches[0].get("url")
        expected_url = f"{API_ROOT}/releases/assets/{asset_id}"
        if type(asset_id) is not int or asset_id <= 0 or url != expected_url:
            raise CompileError("release assets are missing or ambiguous")
        selected.append(matches[0])
    return selected[0], selected[1]


def _resolve_tag(client: httpx.Client, tag: str) -> tuple[str, dict[str, Any]]:
    reference = _get_json(client, f"{API_ROOT}/git/ref/tags/{tag}")
    current = reference.get("object")
    seen: set[str] = set()
    tag_hops = 0
    while True:
        if not isinstance(current, dict):
            break
        kind = current.get("type")
        sha = current.get("sha")
        if not isinstance(sha, str) or not SHA1_RE.fullmatch(sha) or sha in seen:
            break
        seen.add(sha)
        if kind == "commit":
            return sha, reference
        if kind != "tag" or tag_hops >= MAX_TAG_HOPS:
            break
        tag_hops += 1
        current = _get_json(client, f"{API_ROOT}/git/tags/{sha}").get("object")
    raise CompileError("release tag does not resolve to one commit")


def _verify_sidecar(sidecar: bytes, zip_name: str, archive: bytes) -> str:
    try:
        text = sidecar.decode("ascii")
    except UnicodeDecodeError:
        raise CompileError("release checksum is invalid") from None
    match = re.fullmatch(rf"([0-9a-f]{{64}})  {re.escape(zip_name)}\n", text)
    digest = hashlib.sha256(archive).hexdigest()
    if not match or match.group(1) != digest:
        raise CompileError("release checksum does not match the source archive")
    return digest


def _archive_files(archive: bytes) -> dict[str, bytes]:
    try:
        bundle = zipfile.ZipFile(BytesIO(archive))
    except (UnicodeDecodeError, zipfile.BadZipFile):
        raise CompileError("source archive is invalid") from None
    files: dict[str, bytes] = {}
    expanded = 0
    try:
        members = bundle.infolist()
        if not members or len(members) > MAX_ARCHIVE_MEMBERS:
            raise CompileError("source archive has too many entries")
        for member in members:
            name = member.filename
            path = PurePosixPath(name)
            mode = member.external_attr >> 16
            if (
                member.orig_filename != name
                or "\x00" in member.orig_filename
                or member.is_dir()
                or member.flag_bits & 1
                or member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                or "\\" in name
                or not name.startswith(ARCHIVE_PREFIX)
                or path.as_posix() != name
                or any(part in {"", ".", ".."} for part in path.parts)
                or len(path.parts) < 2
                or stat.S_IFMT(mode) != stat.S_IFREG
            ):
                raise CompileError("source archive contains unsafe archive entries")
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            if relative in files:
                raise CompileError("source archive contains duplicate archive entries")
            if member.file_size > MAX_MEMBER_BYTES:
                raise CompileError("source archive member exceeds the size limit")
            expanded += member.file_size
            if expanded > MAX_EXPANDED_BYTES:
                raise CompileError("source archive exceeds the expanded size limit")
            try:
                content = bundle.read(member)
            except (OSError, RuntimeError, zipfile.BadZipFile, zlib.error):
                raise CompileError("source archive is invalid") from None
            if len(content) != member.file_size:
                raise CompileError("source archive is invalid")
            files[relative] = content
    finally:
        bundle.close()
    return files


def _parse_release_sources(files: dict[str, bytes], version: str) -> None:
    try:
        project = tomllib.loads(files["pyproject.toml"].decode("utf-8"))
        lockfile = tomllib.loads(files["uv.lock"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        raise CompileError("release source metadata is invalid") from None
    try:
        package = project["project"]
        allowlist = project["tool"]["hatch"]["build"]["only-include"]
    except (KeyError, TypeError):
        raise CompileError("release source metadata is invalid") from None
    if not isinstance(package, dict):
        raise CompileError("release source metadata is invalid")
    if package.get("name") != "article-audio" or package.get("version") != version:
        raise CompileError("release source version is inconsistent")
    if (
        not isinstance(allowlist, list)
        or any(not isinstance(path, str) for path in allowlist)
        or len(allowlist) != len(set(allowlist))
        or set(allowlist) != set(files)
    ):
        raise CompileError("source archive does not match the package allowlist")
    try:
        runtime = files["src/article_audio/__init__.py"].decode("utf-8")
        packages = lockfile["package"]
    except (KeyError, UnicodeDecodeError, TypeError):
        raise CompileError("release source metadata is invalid") from None
    if not isinstance(packages, list) or any(not isinstance(item, dict) for item in packages):
        raise CompileError("release source metadata is invalid")
    matches = [item for item in packages if item.get("name") == "article-audio"]
    if len(matches) != 1 or not isinstance(matches[0].get("version"), str):
        raise CompileError("release source metadata is invalid")
    locked = matches[0]["version"]
    runtime_match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']\s*$', runtime, re.MULTILINE)
    if not runtime_match or runtime_match.group(1) != version or locked != version:
        raise CompileError("release source version is inconsistent")
    for path in ("template/PROFILE.md", *(path for _, path in REQUIRED_SKILLS)):
        try:
            text = files[path].decode("utf-8")
        except (KeyError, UnicodeDecodeError):
            raise CompileError("required public source is missing or invalid") from None
        pins = set(re.findall(r"\bv(\d+\.\d+\.\d+)\b", text))
        if pins != {version}:
            raise CompileError("release source version pins are inconsistent")


def _verify_tree(client: httpx.Client, commit_sha: str, files: dict[str, bytes]) -> None:
    response = _get_json(client, f"{API_ROOT}/git/trees/{commit_sha}?recursive=1")
    if response.get("truncated") is not False:
        raise CompileError("release commit tree is truncated")
    entries = response.get("tree")
    if not isinstance(entries, list):
        raise CompileError("release commit tree is invalid")
    by_path = {
        entry.get("path"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    for path, content in files.items():
        entry = by_path.get(path)
        if (
            not isinstance(entry, dict)
            or entry.get("type") != "blob"
            or entry.get("mode") not in {"100644", "100755"}
            or entry.get("sha") != _git_blob_sha(content)
        ):
            raise CompileError("source archive does not match the release tag commit")


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _fetch_verified_release(tag: str, client: httpx.Client) -> VerifiedRelease:
    match = TAG_RE.fullmatch(tag)
    if not match:
        raise CompileError("tag must be a stable release such as v0.1.8")
    version = tag[1:]
    release = _get_json(client, f"{API_ROOT}/releases/tags/{tag}")
    zip_asset, sidecar_asset = _release_assets(release, tag, version)
    commit_sha, initial_reference = _resolve_tag(client, tag)
    archive = _download(client, zip_asset["url"], MAX_DOWNLOAD_BYTES)
    sidecar = _download(client, sidecar_asset["url"], 1024)
    digest = _verify_sidecar(sidecar, zip_asset["name"], archive)
    asset_digest = zip_asset.get("digest")
    if asset_digest is not None and asset_digest != f"sha256:{digest}":
        raise CompileError("GitHub asset digest does not match the source archive")
    declared_size = zip_asset.get("size")
    if not isinstance(declared_size, int) or declared_size != len(archive):
        raise CompileError("GitHub asset size does not match the source archive")
    files = _archive_files(archive)
    _parse_release_sources(files, version)
    _verify_tree(client, commit_sha, files)
    final_reference = _get_json(client, f"{API_ROOT}/git/ref/tags/{tag}")
    if final_reference.get("object") != initial_reference.get("object"):
        raise CompileError("release tag changed during compilation")
    zip_name = zip_asset["name"]
    zip_url = f"{REPOSITORY_URL}/releases/download/{tag}/{zip_name}"
    return VerifiedRelease(tag, version, commit_sha, zip_name, zip_url, digest, files)


def _public_spec(release: VerifiedRelease) -> dict[str, Any]:
    if "template/public.json" not in release.files:
        raise CompileError(
            f"release {release.tag} does not support template bundles: "
            "template/public.json is missing"
        )
    try:
        value = json.loads(release.files["template/public.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CompileError("public template metadata is invalid") from None
    expected_keys = {"schema_version", "display_name", "label", "template_id", "memories"}
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise CompileError("public template metadata is invalid")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or not _is_safe_display_text(value["display_name"])
        or not _is_safe_display_text(value["label"])
        or not isinstance(value["template_id"], str)
        or not TEMPLATE_ID_RE.fullmatch(value["template_id"])
        or not isinstance(value["memories"], list)
        or len(value["memories"]) != 4
    ):
        raise CompileError("public template metadata is invalid")
    ids: list[str] = []
    for memory in value["memories"]:
        if not isinstance(memory, dict) or set(memory) != {"id", "text"}:
            raise CompileError("public template metadata is invalid")
        identifier = memory["id"]
        text = memory["text"]
        if not isinstance(identifier, str) or not isinstance(text, str) or not text.strip():
            raise CompileError("public template metadata is invalid")
        try:
            text.encode("utf-8")
        except UnicodeEncodeError:
            raise CompileError("public template metadata is invalid") from None
        if PLACEHOLDER_RE.fullmatch(text.strip()):
            raise CompileError("public template metadata is invalid")
        ids.append(identifier)
    if tuple(ids) != MEMORY_IDS:
        raise CompileError("public template metadata is invalid")
    return value


def _is_safe_display_text(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 200
        and value.strip() == value
        and all(character.isprintable() for character in value)
    )


def _expand_release_memory(text: str, values: dict[str, str]) -> str:
    fields: list[str] = []
    try:
        parsed = list(string.Formatter().parse(text))
    except ValueError:
        raise CompileError("public template metadata is invalid") from None
    for _, field, format_spec, conversion in parsed:
        if field is None:
            continue
        if field not in RELEASE_FIELDS or format_spec or conversion:
            raise CompileError("public template metadata is invalid")
        fields.append(field)
    if set(fields) != RELEASE_FIELDS or len(fields) != len(RELEASE_FIELDS):
        raise CompileError("public template metadata is invalid")
    try:
        expanded = text.format_map(values)
    except (KeyError, ValueError):
        raise CompileError("public template metadata is invalid") from None
    if "{" in expanded or "}" in expanded:
        raise CompileError("public template metadata is invalid")
    return expanded


def _text_body(path: str, content: bytes) -> dict[str, Any]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise CompileError("required public source is missing or invalid") from None
    if not text.strip() or PLACEHOLDER_RE.fullmatch(text.strip()):
        raise CompileError("required public source is missing or invalid")
    return {
        "source_path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "text": text,
    }


def _skill_frontmatter(text: str, expected_name: str) -> tuple[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise CompileError("skill frontmatter is invalid")
    content = text[match.end() :].strip()
    if not content or PLACEHOLDER_RE.fullmatch(content):
        raise CompileError("skill frontmatter is invalid")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise CompileError("skill frontmatter is invalid")
        key, value = line.split(":", 1)
        if key not in {"name", "description"} or key in values or not value.strip():
            raise CompileError("skill frontmatter is invalid")
        values[key] = value.strip()
    if set(values) != {"name", "description"} or values["name"] != expected_name:
        raise CompileError("skill frontmatter is invalid")
    return values["name"], values["description"]


def _compose_bundle(release: VerifiedRelease) -> bytes:
    spec = _public_spec(release)
    profile = _text_body("template/PROFILE.md", release.files["template/PROFILE.md"])
    skills: list[dict[str, Any]] = []
    for identifier, path in REQUIRED_SKILLS:
        body = _text_body(path, release.files[path])
        name, description = _skill_frontmatter(body["text"], identifier)
        skills.append({"id": identifier, "name": name, "description": description, **body})
    provenance = {
        "repository_url": REPOSITORY_URL,
        "tag": release.tag,
        "commit_sha": release.commit_sha,
        "zip_url": release.zip_url,
        "zip_sha256": release.zip_sha256,
    }
    memories: list[dict[str, Any]] = []
    for memory in spec["memories"]:
        text = memory["text"]
        if memory["id"] == "release":
            text = _expand_release_memory(text, provenance)
        encoded = text.encode("utf-8")
        memories.append(
            {
                "id": memory["id"],
                "source_path": "template/public.json",
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "text": text,
            }
        )
    bundle = {
        "schema_version": 1,
        "identity": {
            "display_name": spec["display_name"],
            "label": spec["label"],
            "template_id": spec["template_id"],
        },
        "release": {
            **provenance,
            "version": release.version,
            "zip_name": release.zip_name,
        },
        "profile": profile,
        "skills": skills,
        "memories": memories,
    }
    return (json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_bundle(output_dir: Path, release: VerifiedRelease, bundle: bytes) -> BundlePaths:
    bundle_name = f"article-audio-template-{release.tag}.json"
    checksum_name = f"{bundle_name}.sha256"
    bundle_sha256 = hashlib.sha256(bundle).hexdigest()
    sidecar = f"{bundle_sha256}  {bundle_name}\n".encode("ascii")
    try:
        output_dir.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        raise CompileError("output directory already exists") from None
    except OSError:
        raise CompileError("could not create output directory") from None
    bundle_path = output_dir / bundle_name
    checksum_path = output_dir / checksum_name
    temporary_paths: dict[Path, tuple[int, int]] = {}
    created_paths: dict[Path, tuple[int, int]] = {}
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b", dir=output_dir, prefix=".bundle-", delete=False
        ) as file:
            temporary_bundle = Path(file.name)
            temporary_paths[temporary_bundle] = _file_identity(os.fstat(file.fileno()))
            file.write(bundle)
            file.flush()
            os.fsync(file.fileno())
        with tempfile.NamedTemporaryFile(
            mode="w+b", dir=output_dir, prefix=".checksum-", delete=False
        ) as file:
            temporary_checksum = Path(file.name)
            temporary_paths[temporary_checksum] = _file_identity(os.fstat(file.fileno()))
            file.write(sidecar)
            file.flush()
            os.fsync(file.fileno())
        os.link(temporary_checksum, checksum_path)
        created_paths[checksum_path] = temporary_paths[temporary_checksum]
        os.link(temporary_bundle, bundle_path)
        created_paths[bundle_path] = temporary_paths[temporary_bundle]
        for path, identity in temporary_paths.items():
            if not _unlink_if_owned(path, identity):
                raise OSError("temporary output changed during publication")
        temporary_paths.clear()
        directory_fd = os.open(output_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException as error:
        for path, identity in reversed(created_paths.items()):
            _unlink_if_owned(path, identity)
        for path, identity in temporary_paths.items():
            _unlink_if_owned(path, identity)
        try:
            output_dir.rmdir()
        except OSError:
            pass
        if isinstance(error, OSError):
            raise CompileError("could not write template bundle") from None
        raise
    return BundlePaths(
        bundle_path, checksum_path, release.commit_sha, release.zip_sha256, bundle_sha256
    )


def _file_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _unlink_if_owned(path: Path, identity: tuple[int, int]) -> bool:
    try:
        current = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    if _file_identity(current) != identity:
        return False
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def compile_published_release(tag: str, output_dir: Path, client: httpx.Client) -> BundlePaths:
    """Verify one published release and create its deterministic template bundle."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise CompileError("output directory already exists")
    release = _fetch_verified_release(tag, client)
    bundle = _compose_bundle(release)
    return _write_bundle(output_dir, release, bundle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with httpx.Client(trust_env=False, follow_redirects=True, timeout=30.0) as client:
            result = compile_published_release(args.tag, args.output_dir, client)
    except CompileError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"bundle {result.bundle}")
    print(f"checksum {result.checksum}")
    print(f"commit {result.commit_sha}")
    print(f"source zip SHA-256 {result.zip_sha256}")
    print(f"bundle SHA-256 {result.bundle_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
