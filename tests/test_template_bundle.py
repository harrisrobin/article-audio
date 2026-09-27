import hashlib
import importlib.util
import io
import json
import os
import stat
import sys
import warnings
import zipfile
from pathlib import Path
from urllib.parse import unquote

import httpx
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compile_template.py"
SPEC = importlib.util.spec_from_file_location("compile_template", SCRIPT)
assert SPEC and SPEC.loader
compile_template = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compile_template
SPEC.loader.exec_module(compile_template)

COMMIT = "a" * 40
TAG_OBJECT = "b" * 40
REAL_HTTPX_CLIENT = httpx.Client


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def public_spec() -> dict:
    return {
        "schema_version": 1,
        "display_name": "Article Audio",
        "label": "Article narrator",
        "template_id": "zBuR546KeAs5X0iwlXkxt",
        "memories": [
            {
                "id": "release",
                "text": (
                    "Install from {repository_url} at {tag}, commit {commit_sha}. "
                    "Archive {zip_url}, SHA-256 {zip_sha256}."
                ),
            },
            {"id": "first_message", "text": "Greet the owner without a FILE: placeholder."},
            {"id": "setup_and_privacy", "text": "Keep credentials private."},
            {"id": "narration_scope", "text": "Narrate faithfully."},
        ],
    }


def release_files(*, version: str = "0.1.8", spec: dict | None = None) -> dict[str, bytes]:
    profile = f"# Article Audio\n\nInstall release v{version}. Café.\n".encode()
    narration = (
        "---\n"
        "name: article-audio\n"
        "description: Narrate complete articles.\n"
        "---\n\n"
        f"# Article audio\n\nUse v{version}.\n"
    ).encode()
    onboarding = (
        "---\n"
        "name: article-audio-onboarding\n"
        "description: Set up Article Audio securely.\n"
        "---\n\n"
        f"# Onboarding\n\nUse v{version}.\n"
    ).encode()
    files = {
        "template/PROFILE.md": profile,
        "skills/article-audio/SKILL.md": narration,
        "skills/article-audio-onboarding/SKILL.md": onboarding,
        "template/public.json": json.dumps(spec or public_spec(), ensure_ascii=False).encode(),
        "src/article_audio/__init__.py": f'__version__ = "{version}"\n'.encode(),
        "uv.lock": (
            f'version = 1\n\n[[package]]\nname = "article-audio"\nversion = "{version}"\n'
        ).encode(),
    }
    allowlist = ["pyproject.toml", *sorted(files)]
    files["pyproject.toml"] = (
        "[project]\n"
        'name = "article-audio"\n'
        f'version = "{version}"\n\n'
        "[tool.hatch.build]\n"
        f"only-include = {json.dumps(allowlist)}\n"
    ).encode()
    return files


def zip_release(
    files: dict[str, bytes],
    *,
    duplicate: str | None = None,
    unsafe_name: str | None = None,
    symlink: str | None = None,
) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            info = zipfile.ZipInfo(f"article-audio/{path}")
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = stat.S_IFLNK | 0o777 if path == symlink else stat.S_IFREG | 0o644
            info.external_attr = mode << 16
            archive.writestr(info, content)
        if duplicate:
            info = zipfile.ZipInfo(f"article-audio/{duplicate}")
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(info, files[duplicate])
        if unsafe_name:
            info = zipfile.ZipInfo(unsafe_name)
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, b"unsafe")
    return output.getvalue()


class GitHubFixture:
    def __init__(
        self,
        *,
        files: dict[str, bytes] | None = None,
        zip_bytes: bytes | None = None,
        release_overrides: dict | None = None,
        annotated: bool = False,
        retarget: bool = False,
        tree_overrides: dict | None = None,
        sidecar: bytes | None = None,
        version: str = "0.1.8",
    ):
        self.version = version
        self.tag = f"v{version}"
        self.files = files or release_files(version=version)
        self.zip_bytes = zip_bytes or zip_release(self.files)
        self.zip_name = f"article-audio-{version}.zip"
        self.sidecar_name = f"{self.zip_name}.sha256"
        digest = hashlib.sha256(self.zip_bytes).hexdigest()
        self.sidecar = sidecar or f"{digest}  {self.zip_name}\n".encode()
        assets = [
            {
                "id": 1,
                "name": self.zip_name,
                "url": "https://api.github.com/repos/harrisrobin/article-audio/releases/assets/1",
                "size": len(self.zip_bytes),
                "digest": f"sha256:{digest}",
                "state": "uploaded",
            },
            {
                "id": 2,
                "name": self.sidecar_name,
                "url": "https://api.github.com/repos/harrisrobin/article-audio/releases/assets/2",
                "size": len(self.sidecar),
                "state": "uploaded",
            },
        ]
        self.release = {
            "tag_name": self.tag,
            "draft": False,
            "prerelease": False,
            "published_at": "2026-09-27T12:00:00Z",
            "target_commitish": "main",
            "assets": assets,
        }
        self.release.update(release_overrides or {})
        self.annotated = annotated
        self.retarget = retarget
        self.ref_requests = 0
        tree = [
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": git_blob_sha(content),
            }
            for path, content in self.files.items()
        ]
        self.tree = {"truncated": False, "tree": tree}
        self.tree.update(tree_overrides or {})
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = unquote(request.url.path)
        if path.endswith(f"/releases/tags/{self.tag}"):
            return httpx.Response(200, json=self.release)
        if path.endswith(f"/git/ref/tags/{self.tag}"):
            self.ref_requests += 1
            if self.retarget and self.ref_requests > 1:
                return httpx.Response(200, json={"object": {"type": "commit", "sha": "c" * 40}})
            kind = "tag" if self.annotated else "commit"
            sha = TAG_OBJECT if self.annotated else COMMIT
            return httpx.Response(200, json={"object": {"type": kind, "sha": sha}})
        if path.endswith(f"/git/tags/{TAG_OBJECT}"):
            return httpx.Response(200, json={"object": {"type": "commit", "sha": COMMIT}})
        if path.endswith(f"/git/trees/{COMMIT}"):
            return httpx.Response(200, json=self.tree)
        if path.endswith("/releases/assets/1"):
            return httpx.Response(200, content=self.zip_bytes)
        if path.endswith("/releases/assets/2"):
            return httpx.Response(200, content=self.sidecar)
        return httpx.Response(404)

    def client(self) -> httpx.Client:
        return REAL_HTTPX_CLIENT(transport=httpx.MockTransport(self.handler), trust_env=False)


def compile_fixture(tmp_path: Path, fixture: GitHubFixture):
    tmp_path.mkdir(parents=True, exist_ok=True)
    with fixture.client() as client:
        return compile_template.compile_published_release(fixture.tag, tmp_path / "bundle", client)


def replace_first_compressed_byte(archive: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        member = bundle.infolist()[0]
        offset = (
            member.header_offset + 30 + len(member.filename.encode("utf-8")) + len(member.extra)
        )
    damaged = bytearray(archive)
    damaged[offset] = 0xFF
    return bytes(damaged)


def test_compile_published_release_emits_literal_deterministic_bundle(tmp_path):
    fixture = GitHubFixture(annotated=True)
    result = compile_fixture(tmp_path, fixture)

    bundle_bytes = result.bundle.read_bytes()
    bundle = json.loads(bundle_bytes)
    expected_zip_hash = hashlib.sha256(fixture.zip_bytes).hexdigest()
    assert result.checksum.read_text() == (
        f"{hashlib.sha256(bundle_bytes).hexdigest()}  article-audio-template-v0.1.8.json\n"
    )
    assert bundle["identity"] == {
        "display_name": "Article Audio",
        "label": "Article narrator",
        "template_id": "zBuR546KeAs5X0iwlXkxt",
    }
    assert bundle["release"] == {
        "commit_sha": COMMIT,
        "repository_url": "https://github.com/harrisrobin/article-audio",
        "tag": "v0.1.8",
        "version": "0.1.8",
        "zip_name": "article-audio-0.1.8.zip",
        "zip_sha256": expected_zip_hash,
        "zip_url": (
            "https://github.com/harrisrobin/article-audio/releases/download/"
            "v0.1.8/article-audio-0.1.8.zip"
        ),
    }
    assert bundle["profile"]["text"] == fixture.files["template/PROFILE.md"].decode()
    assert bundle["profile"]["bytes"] == len(fixture.files["template/PROFILE.md"])
    assert [skill["id"] for skill in bundle["skills"]] == [
        "article-audio",
        "article-audio-onboarding",
    ]
    assert bundle["skills"][0]["text"].startswith("---\nname: article-audio\n")
    assert bundle["skills"][0]["name"] == "article-audio"
    assert bundle["skills"][0]["description"] == "Narrate complete articles."
    assert bundle["memories"][0]["text"] == (
        "Install from https://github.com/harrisrobin/article-audio at v0.1.8, "
        f"commit {COMMIT}. Archive "
        "https://github.com/harrisrobin/article-audio/releases/download/v0.1.8/"
        f"article-audio-0.1.8.zip, SHA-256 {expected_zip_hash}."
    )
    assert "generated_at" not in bundle
    assert str(tmp_path) not in bundle_bytes.decode()


def test_main_uses_anonymous_client_and_reports_artifacts(tmp_path, monkeypatch, capsys):
    fixture = GitHubFixture()
    clients: list[httpx.Client] = []

    def client_factory(**kwargs):
        assert kwargs["trust_env"] is False
        client = fixture.client()
        clients.append(client)
        return client

    monkeypatch.setattr(compile_template.httpx, "Client", client_factory)
    output = tmp_path / "cli-bundle"
    assert compile_template.main(["v0.1.8", "--output-dir", str(output)]) == 0
    stdout = capsys.readouterr().out
    assert str(output / "article-audio-template-v0.1.8.json") in stdout
    assert COMMIT in stdout
    assert clients
    assert all("authorization" not in request.headers for request in fixture.requests)


@pytest.mark.parametrize(
    ("release_overrides", "message"),
    [
        ({"draft": True}, "published stable release"),
        ({"prerelease": True}, "published stable release"),
        ({"tag_name": "v0.1.9"}, "release tag"),
        ({"published_at": None}, "published stable release"),
        ({"assets": []}, "release assets"),
    ],
)
def test_rejects_invalid_release_metadata(tmp_path, release_overrides, message):
    fixture = GitHubFixture(release_overrides=release_overrides)
    with pytest.raises(compile_template.CompileError, match=message):
        compile_fixture(tmp_path, fixture)


def test_rejects_duplicate_release_asset(tmp_path):
    fixture = GitHubFixture()
    fixture.release["assets"].append(dict(fixture.release["assets"][0]))
    with pytest.raises(compile_template.CompileError, match="release assets"):
        compile_fixture(tmp_path, fixture)


@pytest.mark.parametrize(
    "asset_change",
    [
        lambda asset: asset.__setitem__("id", 0),
        lambda asset: asset.__setitem__("id", "1"),
        lambda asset: asset.__setitem__("url", asset["url"] + "?download=1"),
        lambda asset: asset.__setitem__(
            "url", "https://api.github.com/repos/harrisrobin/article-audio/releases/assets/2"
        ),
    ],
)
def test_rejects_noncanonical_release_asset_identity(tmp_path, asset_change):
    fixture = GitHubFixture()
    asset_change(fixture.release["assets"][0])
    with pytest.raises(compile_template.CompileError, match="release assets"):
        compile_fixture(tmp_path, fixture)


def test_main_bounds_github_metadata_responses(tmp_path, monkeypatch, capsys):
    fixture = GitHubFixture()
    monkeypatch.setattr(compile_template, "MAX_API_BYTES", 20)
    monkeypatch.setattr(compile_template.httpx, "Client", lambda **kwargs: fixture.client())
    assert compile_template.main(["v0.1.8", "--output-dir", str(tmp_path / "bundle")]) == 2
    assert capsys.readouterr().err == "error: GitHub metadata exceeds the size limit\n"


@pytest.mark.parametrize(
    ("zip_mutation", "message"),
    [
        ({"duplicate": "template/PROFILE.md"}, "archive entries"),
        ({"unsafe_name": "article-audio/../secret"}, "archive entries"),
        ({"symlink": "template/PROFILE.md"}, "archive entries"),
    ],
)
def test_rejects_unsafe_archive_entries(tmp_path, zip_mutation, message):
    files = release_files()
    fixture = GitHubFixture(files=files, zip_bytes=zip_release(files, **zip_mutation))
    fixture.sidecar = (
        f"{hashlib.sha256(fixture.zip_bytes).hexdigest()}  {fixture.zip_name}\n".encode()
    )
    fixture.release["assets"][0]["digest"] = (
        f"sha256:{hashlib.sha256(fixture.zip_bytes).hexdigest()}"
    )
    with pytest.raises(compile_template.CompileError, match=message):
        compile_fixture(tmp_path, fixture)


def test_corrupt_deflate_is_a_static_compiler_failure(tmp_path, monkeypatch, capsys):
    valid = GitHubFixture()
    fixture = GitHubFixture(
        files=valid.files,
        zip_bytes=replace_first_compressed_byte(valid.zip_bytes),
    )
    with pytest.raises(compile_template.CompileError, match="source archive is invalid"):
        compile_fixture(tmp_path / "public", fixture)

    monkeypatch.setattr(compile_template.httpx, "Client", lambda **kwargs: fixture.client())
    result = compile_template.main(["v0.1.8", "--output-dir", str(tmp_path / "main" / "bundle")])
    captured = capsys.readouterr()
    assert result == 2
    assert captured.err == "error: source archive is invalid\n"
    assert "Traceback" not in captured.err


def test_rejects_nul_in_original_zip_member_name(tmp_path):
    files = release_files()
    altered = dict(files)
    profile = altered.pop("template/PROFILE.md")
    altered["template/PROFILE.mdXXX"] = profile
    archive = zip_release(altered).replace(
        b"article-audio/template/PROFILE.mdXXX",
        b"article-audio/template/PROFILE.md\x00XX",
    )
    fixture = GitHubFixture(files=files, zip_bytes=archive)
    with pytest.raises(compile_template.CompileError, match="unsafe archive entries"):
        compile_fixture(tmp_path, fixture)


def test_rejects_checksum_tree_and_truncated_tree_mismatches(tmp_path):
    bad_checksum = GitHubFixture(sidecar=(b"0" * 64) + b"  article-audio-0.1.8.zip\n")
    with pytest.raises(compile_template.CompileError, match="checksum"):
        compile_fixture(tmp_path / "checksum", bad_checksum)

    wrong_tree = GitHubFixture()
    wrong_tree.tree["tree"][0]["sha"] = "0" * 40
    with pytest.raises(compile_template.CompileError, match="tag commit"):
        compile_fixture(tmp_path / "tree", wrong_tree)

    truncated = GitHubFixture(tree_overrides={"truncated": True})
    with pytest.raises(compile_template.CompileError, match="truncated"):
        compile_fixture(tmp_path / "truncated", truncated)

    wrong_mode = GitHubFixture()
    wrong_mode.tree["tree"][0]["mode"] = "120000"
    with pytest.raises(compile_template.CompileError, match="tag commit"):
        compile_fixture(tmp_path / "mode", wrong_mode)


def test_rejects_tag_retarget_and_malformed_asset_attestation(tmp_path):
    with pytest.raises(compile_template.CompileError, match="changed during compilation"):
        compile_fixture(tmp_path / "retarget", GitHubFixture(retarget=True))

    wrong_digest = GitHubFixture()
    wrong_digest.release["assets"][0]["digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(compile_template.CompileError, match="asset digest"):
        compile_fixture(tmp_path / "digest", wrong_digest)

    wrong_size = GitHubFixture()
    wrong_size.release["assets"][0]["size"] += 1
    with pytest.raises(compile_template.CompileError, match="asset size"):
        compile_fixture(tmp_path / "size", wrong_size)


def test_enforces_download_and_expanded_member_limits(tmp_path, monkeypatch):
    fixture = GitHubFixture()
    monkeypatch.setattr(compile_template, "MAX_DOWNLOAD_BYTES", len(fixture.zip_bytes) - 1)
    with pytest.raises(compile_template.CompileError, match="size limit"):
        compile_fixture(tmp_path / "download", fixture)

    monkeypatch.setattr(compile_template, "MAX_DOWNLOAD_BYTES", 2 * 1024 * 1024)
    monkeypatch.setattr(compile_template, "MAX_MEMBER_BYTES", 8)
    with pytest.raises(compile_template.CompileError, match="member exceeds"):
        compile_fixture(tmp_path / "member", GitHubFixture())


@pytest.mark.parametrize(
    "change",
    [
        lambda value: value.update(extra=True),
        lambda value: value.__setitem__("template_id", "bad template/id"),
        lambda value: value.__setitem__("display_name", ""),
        lambda value: value.__setitem__("label", "line\nbreak"),
        lambda value: value.__setitem__("schema_version", True),
        lambda value: value["memories"].pop(),
        lambda value: value["memories"][1].__setitem__("id", "release"),
        lambda value: value["memories"][1].__setitem__("text", "FILE:/tmp/private.md"),
        lambda value: value["memories"][0].__setitem__("text", "Unknown {owner_secret}"),
        lambda value: value["memories"][0].__setitem__("text", "Bad {tag!r}"),
        lambda value: value["memories"][0].__setitem__("text", "Bad {tag[0]}"),
        lambda value: value["memories"][0].__setitem__("text", "Bad {tag:>10}"),
        lambda value: value["memories"][0].__setitem__(
            "text",
            ("{repository_url} {tag} {commit_sha} {zip_url} {zip_sha256} {{unknown}}"),
        ),
        lambda value: value["memories"][1].update(extra="wrong"),
    ],
)
def test_rejects_malformed_public_metadata(tmp_path, change):
    spec = public_spec()
    change(spec)
    fixture = GitHubFixture(files=release_files(spec=spec))
    fixture.zip_bytes = zip_release(fixture.files)
    fixture.__init__(files=fixture.files, zip_bytes=fixture.zip_bytes)
    with pytest.raises(compile_template.CompileError, match="public template metadata"):
        compile_fixture(tmp_path, fixture)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda files: files.__setitem__(
            "src/article_audio/__init__.py", b'__version__ = "9.9.9"\n'
        ),
        lambda files: files.__setitem__(
            "skills/article-audio/SKILL.md",
            b"---\nname: wrong\ndescription: Wrong.\n---\n\nUse v0.1.8.\n",
        ),
        lambda files: files.__setitem__("template/PROFILE.md", b"Install release v0.1.7.\n"),
        lambda files: files.pop("template/public.json"),
    ],
)
def test_rejects_inconsistent_release_sources(tmp_path, mutate):
    files = release_files()
    mutate(files)
    fixture = GitHubFixture(files=files)
    with pytest.raises(compile_template.CompileError):
        compile_fixture(tmp_path, fixture)


def test_legacy_release_without_public_metadata_fails_without_local_fallback(tmp_path):
    files = release_files(version="0.1.7")
    files.pop("template/public.json")
    allowlist = ["pyproject.toml", *sorted(path for path in files if path != "pyproject.toml")]
    files["pyproject.toml"] = (
        "[project]\n"
        'name = "article-audio"\n'
        'version = "0.1.7"\n\n'
        "[tool.hatch.build]\n"
        f"only-include = {json.dumps(allowlist)}\n"
    ).encode()
    local = tmp_path / "template"
    local.mkdir(parents=True)
    (local / "public.json").write_text(json.dumps(public_spec()))
    fixture = GitHubFixture(files=files, version="0.1.7")
    with pytest.raises(
        compile_template.CompileError,
        match=r"release v0\.1\.7 does not support template bundles",
    ):
        compile_fixture(tmp_path / "run", fixture)


@pytest.mark.parametrize("body", ["", "FILE:/tmp/skill-v0.1.8.md"])
def test_rejects_skill_with_empty_or_placeholder_only_body(tmp_path, body):
    files = release_files()
    files["skills/article-audio/SKILL.md"] = (
        f"---\nname: article-audio\ndescription: Narrate with release v0.1.8.\n---\n{body}"
    ).encode()
    with pytest.raises(compile_template.CompileError, match="skill frontmatter"):
        compile_fixture(tmp_path, GitHubFixture(files=files))


def test_rejects_unpaired_unicode_surrogate_in_public_metadata(tmp_path):
    files = release_files()
    spec = public_spec()
    spec["memories"][1]["text"] = "bad\ud800value"
    files["template/public.json"] = json.dumps(spec).encode("ascii")
    with pytest.raises(compile_template.CompileError, match="public template metadata"):
        compile_fixture(tmp_path, GitHubFixture(files=files))


def test_rejects_malformed_toml_shapes_without_internal_tracebacks(tmp_path):
    bad_project = release_files()
    bad_project["pyproject.toml"] = b"project = 1\n[tool.hatch.build]\nonly-include = []\n"
    with pytest.raises(compile_template.CompileError, match="source metadata"):
        compile_fixture(tmp_path / "project", GitHubFixture(files=bad_project))

    duplicate_lock = release_files()
    duplicate_lock["uv.lock"] += b'\n[[package]]\nname = "article-audio"\nversion = "0.1.8"\n'
    with pytest.raises(compile_template.CompileError, match="source metadata"):
        compile_fixture(tmp_path / "lock", GitHubFixture(files=duplicate_lock))

    malformed_lock = release_files()
    malformed_lock["uv.lock"] = b'version = 1\npackage = ["not-a-table"]\n'
    with pytest.raises(compile_template.CompileError, match="source metadata"):
        compile_fixture(tmp_path / "lock-shape", GitHubFixture(files=malformed_lock))


def test_rejects_extra_or_missing_allowlisted_archive_member(tmp_path):
    files = release_files()
    files["unlisted.txt"] = b"extra"
    with pytest.raises(compile_template.CompileError, match="allowlist"):
        compile_fixture(tmp_path, GitHubFixture(files=files))


def test_rejects_existing_output_without_changing_it(tmp_path):
    output = tmp_path / "bundle"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep")
    with GitHubFixture().client() as client:
        with pytest.raises(compile_template.CompileError, match="already exists"):
            compile_template.compile_published_release("v0.1.8", output, client)
    assert marker.read_text() == "keep"
    assert list(output.iterdir()) == [marker]


def test_write_failure_removes_only_this_run_output(tmp_path, monkeypatch):
    output = tmp_path / "bundle"

    def failing_link(source, destination):
        raise OSError("injected failure")

    monkeypatch.setattr(compile_template.os, "link", failing_link)
    with pytest.raises(compile_template.CompileError, match="could not write"):
        compile_fixture(tmp_path, GitHubFixture())
    assert not output.exists()


def test_output_publication_never_removes_a_racing_preexisting_file(tmp_path, monkeypatch):
    output = tmp_path / "bundle"
    real_link = os.link
    calls = 0

    def racing_link(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            Path(destination).write_bytes(b"other writer")
            raise FileExistsError("injected race")
        return real_link(source, destination)

    monkeypatch.setattr(compile_template.os, "link", racing_link)
    with pytest.raises(compile_template.CompileError, match="could not write"):
        compile_fixture(tmp_path, GitHubFixture())
    assert output.is_dir()
    files = list(output.iterdir())
    assert len(files) == 1
    assert files[0].name == "article-audio-template-v0.1.8.json"
    assert files[0].read_bytes() == b"other writer"


def test_cleanup_preserves_replacement_of_first_published_output(tmp_path, monkeypatch):
    output = tmp_path / "bundle"
    real_link = os.link
    calls = 0

    def racing_link(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            checksum = output / "article-audio-template-v0.1.8.json.sha256"
            checksum.unlink()
            checksum.write_bytes(b"replacement inode")
            raise OSError("injected second-link failure")
        return real_link(source, destination)

    monkeypatch.setattr(compile_template.os, "link", racing_link)
    with pytest.raises(compile_template.CompileError, match="could not write"):
        compile_fixture(tmp_path, GitHubFixture())
    checksum = output / "article-audio-template-v0.1.8.json.sha256"
    assert checksum.read_bytes() == b"replacement inode"


def test_output_is_byte_deterministic_and_ignores_workspace_and_credentials(tmp_path, monkeypatch):
    fixture = GitHubFixture()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-be-read")
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-read")
    (tmp_path / "template").mkdir()
    (tmp_path / "template" / "PROFILE.md").write_text("PRIVATE LOCAL PROFILE")

    first = compile_fixture(tmp_path / "first", fixture).bundle.read_bytes()
    second = compile_fixture(tmp_path / "second", GitHubFixture()).bundle.read_bytes()
    assert first == second
    assert b"PRIVATE LOCAL PROFILE" not in first
    assert b"must-not-be-read" not in first


def test_main_returns_concise_error_without_traceback(tmp_path, monkeypatch, capsys):
    fixture = GitHubFixture(release_overrides={"draft": True})
    monkeypatch.setattr(compile_template.httpx, "Client", lambda **kwargs: fixture.client())
    result = compile_template.main(["v0.1.8", "--output-dir", str(tmp_path / "bundle")])
    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "error: release is not a published stable release\n"
    assert "Traceback" not in captured.err
