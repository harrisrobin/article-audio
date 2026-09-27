import threading
from urllib.parse import urlencode

import httpx
import pytest

from article_audio.credentials import GROUPS, CredentialStore
from article_audio.onboarding import SetupServer


@pytest.mark.parametrize("group", ["gemini", "r2", "cloudflare"])
def test_local_form_rejects_cross_origin_and_saves_without_echo(tmp_path, group):
    store = CredentialStore(tmp_path / "credentials")
    if group == "r2":
        store.save({"GEMINI_API_KEY": "previously-saved-gemini-key"})
    values = {key: f"private-test-{key}" for key in GROUPS[group]}
    server = SetupServer(store, group, lifetime=30)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(trust_env=False) as client:
            page = client.get(server.url)
            assert page.status_code == 200
            assert 'type="password"' in page.text
            assert page.headers["cache-control"] == "no-store"
            assert all(f'name="{key}"' in page.text for key in values)
            if group == "cloudflare":
                assert "Account API Tokens &gt; Edit" in page.text
                assert "Workers R2 Storage &gt; Edit" in page.text
                assert "manual R2 setup" in page.text
            data = urlencode({"csrf": server.token, **values})
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://bad.test",
            }
            assert client.post(server.url, content=data, headers=headers).status_code == 403
            assert all(store.get(key) is None for key in values)
            headers["Origin"] = server.origin
            saved = client.post(server.url, content=data, headers=headers)
            assert saved.status_code == 200
            assert all(value not in saved.text for value in values.values())
            assert CredentialStore(store.directory).require(group) == values
            if group == "r2":
                assert store.get("GEMINI_API_KEY") == "previously-saved-gemini-key"
            assert client.post(server.url, content=data, headers=headers).status_code == 410
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
