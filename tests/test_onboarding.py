import threading
from urllib.parse import urlencode

import httpx

from article_audio.credentials import CredentialStore
from article_audio.onboarding import SetupServer


def test_local_form_rejects_cross_origin_and_saves_without_echo(tmp_path):
    store = CredentialStore(tmp_path / "credentials")
    server = SetupServer(store, "gemini", lifetime=30)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(trust_env=False) as client:
            page = client.get(server.url)
            assert page.status_code == 200
            assert 'type="password"' in page.text
            assert page.headers["cache-control"] == "no-store"
            data = urlencode({"csrf": server.token, "GEMINI_API_KEY": "private-test-key"})
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://bad.test",
            }
            assert client.post(server.url, content=data, headers=headers).status_code == 403
            assert not store.path.exists()
            headers["Origin"] = server.origin
            saved = client.post(server.url, content=data, headers=headers)
            assert saved.status_code == 200
            assert "private-test-key" not in saved.text
            assert store.get("GEMINI_API_KEY") == "private-test-key"
            assert client.post(server.url, content=data, headers=headers).status_code == 410
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
