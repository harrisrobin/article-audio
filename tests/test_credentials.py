import os
import stat

import pytest

from article_audio.credentials import CredentialStore
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
