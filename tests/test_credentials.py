import os
import stat
import subprocess
import sys

import pytest

from article_audio.credentials import GROUPS, CredentialStore
from article_audio.errors import UserError


def test_credentials_persist_privately_and_status_never_contains_values(tmp_path):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "fake-secret"})
    loaded = CredentialStore(tmp_path / "settings")
    assert loaded.get("GEMINI_API_KEY") == "fake-secret"
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.directory.stat().st_mode) == 0o700
    assert "fake-secret" not in str(loaded.status("gemini"))
    assert loaded.status("gemini")["missing"] == []


def test_environment_overrides_saved_value(tmp_path, monkeypatch):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "saved"})
    monkeypatch.setenv("GEMINI_API_KEY", "injected")
    assert store.get("GEMINI_API_KEY") == "injected"


def test_merging_credentials_retains_existing_values(tmp_path):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "saved"})
    store.save({"R2_BUCKET": "audio"})
    assert store.get("GEMINI_API_KEY") == "saved"
    assert store.get("R2_BUCKET") == "audio"


def test_rejects_unknown_fields_without_echoing_value(tmp_path):
    store = CredentialStore(tmp_path / "settings")
    with pytest.raises(UserError) as error:
        store.save({"anything": "private-value"})
    assert "private-value" not in str(error.value)
    assert not store.path.exists()


def test_refuses_symlink_credential_file(tmp_path):
    directory = tmp_path / "settings"
    directory.mkdir(mode=0o700)
    target = tmp_path / "victim"
    target.write_text("{}")
    (directory / "credentials.json").symlink_to(target)
    with pytest.raises(UserError):
        CredentialStore(directory).save({"GEMINI_API_KEY": "secret"})
    assert target.read_text() == "{}"


def test_refuses_world_readable_existing_secrets(tmp_path):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "secret"})
    os.chmod(store.path, 0o644)
    with pytest.raises(UserError):
        store.get("GEMINI_API_KEY")


@pytest.mark.parametrize(
    "damaged",
    ['{"GEMINI_API_KEY":"private-marker",BROKEN', '{"unknown":"private-marker"}', "x" * 65537],
    ids=["json", "schema", "size"],
)
def test_corrupt_credentials_preserve_file_and_give_working_recovery_steps(tmp_path, damaged):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "private-marker"})
    store.path.write_text(damaged)
    broken = store.path.read_bytes()
    with pytest.raises(UserError) as error:
        store.save({"GEMINI_API_KEY": "replacement"})
    assert error.value.code == "unsafe_storage"
    assert "Move" in str(error.value) and "private-marker" not in str(error.value)
    assert store.path.read_bytes() == broken
    backup = store.directory / "credentials.backup"
    store.path.rename(backup)
    store.save({"GEMINI_API_KEY": "replacement"})
    assert store.get("GEMINI_API_KEY") == "replacement"
    assert backup.read_bytes() == broken


def test_insecure_permissions_can_be_repaired_without_losing_other_provider(tmp_path):
    store = CredentialStore(tmp_path / "settings")
    store.save({"GEMINI_API_KEY": "before", "R2_BUCKET": "audio"})
    store.path.chmod(0o644)
    with pytest.raises(UserError, match="0600"):
        store.save({"GEMINI_API_KEY": "after"})
    store.path.chmod(0o600)
    store.save({"GEMINI_API_KEY": "after"})
    assert store.get("R2_BUCKET") == "audio"
    assert store.get("GEMINI_API_KEY") == "after"


def test_fifo_credential_path_fails_without_hanging(tmp_path):
    directory = tmp_path / "settings"
    directory.mkdir(mode=0o700)
    os.mkfifo(directory / "credentials.json", 0o600)
    result = subprocess.run(
        [sys.executable, "-m", "article_audio", "--config-dir", str(directory), "auth", "status"],
        capture_output=True,
        text=True,
        timeout=2,
        env={key: value for key, value in os.environ.items() if key != "GEMINI_API_KEY"},
    )
    assert result.returncode == 2
    assert "regular file" in result.stdout


def test_removing_last_group_leaves_a_valid_empty_store(tmp_path):
    store = CredentialStore(tmp_path / "config")
    store.save({"CLOUDFLARE_API_TOKEN": "temporary"})
    store.save({}, remove_if_matches={"CLOUDFLARE_API_TOKEN": "temporary"})
    assert store.status("cloudflare")["present"] == []
    store.save({"GEMINI_API_KEY": "new"})
    assert store.get("GEMINI_API_KEY") == "new"


@pytest.mark.parametrize("operation", ["require", "status"])
def test_group_read_uses_one_configuration_during_rotation(tmp_path, monkeypatch, operation):
    for key in GROUPS["r2"]:
        monkeypatch.delenv(key, raising=False)
    old = {key: "old-" + key for key in GROUPS["r2"]}
    new = {key: "new-" + key for key in GROUPS["r2"]}
    if operation == "status":
        old = {"R2_ACCOUNT_ID": "old-account"}
    reader = CredentialStore(tmp_path / "config")
    writer = CredentialStore(reader.directory)
    writer.save(old)
    read = reader._read

    def rotate_after_read():
        values = read()
        writer.save(new)
        return values

    monkeypatch.setattr(reader, "_read", rotate_after_read)
    result = getattr(reader, operation)("r2")
    if operation == "require":
        assert result == old
    else:
        assert result["present"] == ["R2_ACCOUNT_ID"]
        assert set(result["missing"]) == set(GROUPS["r2"]) - {"R2_ACCOUNT_ID"}


def test_complete_environment_group_does_not_require_saved_file(tmp_path, monkeypatch):
    store = CredentialStore(tmp_path / "config")
    expected = {key: "injected-" + key for key in GROUPS["r2"]}
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(store, "_read", lambda: pytest.fail("File backend should not be read"))
    assert store.require("r2") == expected
