import hashlib
import json
import os

import httpx
import pytest

from article_audio.cloudflare import OBJECT_WRITE, provision_r2
from article_audio.credentials import GROUPS, CredentialStore
from article_audio.errors import UserError

ACCOUNT = "a" * 32
SETUP_TOKEN = "setup-private-marker"
UPLOAD_TOKEN = "upload-private-marker" * 3
UPLOAD_ID = "b" * 32
PERMISSION = "c" * 32


@pytest.fixture
def store(tmp_path, monkeypatch):
    for group in GROUPS.values():
        for key in group:
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("R2_JURISDICTION", raising=False)
    result = CredentialStore(tmp_path / "config")
    result.save(
        {
            "GEMINI_API_KEY": "gemini-keep",
            "CLOUDFLARE_ACCOUNT_ID": ACCOUNT,
            "CLOUDFLARE_API_TOKEN": SETUP_TOKEN,
        }
    )
    return result


class CloudflareMock:
    def __init__(self):
        self.requests = []
        self.buckets = set()
        self.tokens = []
        self.fail = None
        self.public = False

    def __call__(self, request):
        self.requests.append(request)
        assert request.headers["Authorization"] == "Bearer " + SETUP_TOKEN
        assert request.url.host == "api.cloudflare.com"
        assert request.url.path.startswith(f"/client/v4/accounts/{ACCOUNT}/")
        path = request.url.path.split(ACCOUNT)[1]
        if self.fail:
            failure = self.fail(request)
            if failure is not None:
                return failure
        if path == "/tokens/permission_groups":
            assert request.url.params["name"] == OBJECT_WRITE
            result = [{"id": PERMISSION, "name": OBJECT_WRITE}]
        elif path == "/r2/buckets":
            name = json.loads(request.content)["name"]
            self.buckets.add(name)
            result = {"name": name}
        elif path.endswith("/domains/managed"):
            result = {"enabled": self.public}
        elif path.endswith("/domains/custom"):
            result = {"domains": []}
        elif path.startswith("/r2/buckets/"):
            name = path.split("/")[-1]
            if name not in self.buckets:
                return httpx.Response(404)
            result = {"name": name}
        elif path == "/tokens":
            self.tokens.append(json.loads(request.content))
            result = {"id": UPLOAD_ID, "value": UPLOAD_TOKEN}
        else:
            pytest.fail(f"Unexpected API request: {request.method} {path}")
        return httpx.Response(200, json={"success": True, "result": result})

    def provision(self, store, **kwargs):
        with httpx.Client(transport=httpx.MockTransport(self)) as http:
            return provision_r2(store, http, **kwargs)


def test_provision_saves_bucket_scoped_keys_clears_bootstrap_and_reuses(store):
    cloud = CloudflareMock()
    result = cloud.provision(store)
    bucket = result["bucket"]
    assert result["playback_verified"] is False
    assert cloud.tokens == [
        {
            "name": bucket + "-uploads",
            "policies": [
                {
                    "effect": "allow",
                    "resources": {f"com.cloudflare.edge.r2.bucket.{ACCOUNT}_default_{bucket}": "*"},
                    "permission_groups": [{"id": PERMISSION}],
                }
            ],
        }
    ]
    assert store.require("r2") == {
        "R2_ACCOUNT_ID": ACCOUNT,
        "R2_BUCKET": bucket,
        "R2_ACCESS_KEY_ID": UPLOAD_ID,
        "R2_SECRET_ACCESS_KEY": hashlib.sha256(UPLOAD_TOKEN.encode()).hexdigest(),
    }
    assert store.get("GEMINI_API_KEY") == "gemini-keep"
    assert store.status("cloudflare")["present"] == []
    assert SETUP_TOKEN not in store.path.read_text()
    assert UPLOAD_TOKEN not in store.path.read_text()
    assert not any(
        secret in json.dumps(result) for secret in (SETUP_TOKEN, UPLOAD_TOKEN, UPLOAD_ID)
    )
    count = len(cloud.requests)
    assert cloud.provision(store)["reused"] is True
    assert len(cloud.requests) == count


def test_bucket_create_timeout_reuses_reserved_bucket(store):
    cloud = CloudflareMock()

    def timeout(request):
        if request.method == "POST" and request.url.path.endswith("/r2/buckets"):
            cloud.buckets.add(json.loads(request.content)["name"])
            raise httpx.ReadTimeout(SETUP_TOKEN, request=request)

    cloud.fail = timeout
    with pytest.raises(UserError, match="Cloudflare setup request failed"):
        cloud.provision(store)
    cloud.fail = None
    result = cloud.provision(store)
    assert cloud.buckets == {result["bucket"]}
    assert (
        sum(r.method == "POST" and r.url.path.endswith("/r2/buckets") for r in cloud.requests) == 1
    )


@pytest.mark.parametrize("failure", ["timeout", "malformed", "denied"])
def test_uncertain_token_request_requires_explicit_recovery(store, failure):
    cloud = CloudflareMock()

    def fail(request):
        if request.method == "POST" and request.url.path.endswith("/tokens"):
            if failure == "timeout":
                raise httpx.ReadTimeout(UPLOAD_TOKEN, request=request)
            if failure == "denied":
                return httpx.Response(403, text=UPLOAD_TOKEN)
            return httpx.Response(200, json={"success": True, "result": {"value": UPLOAD_TOKEN}})

    cloud.fail = fail
    with pytest.raises(UserError) as error:
        cloud.provision(store)
    assert UPLOAD_TOKEN not in str(error.value)
    count = len(cloud.requests)
    with pytest.raises(UserError, match="revoke any token") as error:
        cloud.provision(store)
    assert error.value.code == "token_recovery_required"
    assert len(cloud.requests) == count
    cloud.fail = None
    assert cloud.provision(store, retry_token=True)["configured"] is True
    assert len(cloud.buckets) == 1


@pytest.mark.parametrize("status", [401, 403, 429, 500, 302])
def test_permission_failure_stops_before_mutations_and_redacts(store, status):
    cloud = CloudflareMock()
    cloud.fail = lambda request: httpx.Response(
        status, text=SETUP_TOKEN, headers={"Location": "https://elsewhere.test"}
    )
    with pytest.raises(UserError) as error:
        cloud.provision(store)
    assert SETUP_TOKEN not in str(error.value)
    assert all(request.method == "GET" for request in cloud.requests)
    assert not (store.directory / "r2-setup.json").exists()


@pytest.mark.parametrize("domain", ["managed", "custom", "unknown"])
def test_public_or_unknown_bucket_never_gets_upload_credentials(store, domain):
    cloud = CloudflareMock()
    if domain == "managed":
        cloud.public = True
    else:
        cloud.fail = lambda r: (
            httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {"domains": [{"enabled": True}] if domain == "custom" else [{}]},
                },
            )
            if r.url.path.endswith("/domains/custom")
            else None
        )
    with pytest.raises(UserError) as error:
        cloud.provision(store)
    assert error.value.code == "bucket_not_private"
    assert cloud.tokens == []
    assert store.status("r2")["present"] == []


def test_partial_credentials_are_preserved(store):
    store.save({"R2_BUCKET": "existing"})
    cloud = CloudflareMock()
    with pytest.raises(UserError, match="Partial R2"):
        cloud.provision(store)
    assert cloud.requests == []
    assert store.get("R2_BUCKET") == "existing"


def test_wrong_account_and_invalid_account_never_call_api(store):
    cloud = CloudflareMock()
    path = store.directory / "r2-setup.json"
    path.write_text(
        json.dumps(
            {"account": "f" * 32, "bucket": "article-audio-123456789abc", "token_requested": False}
        )
    )
    path.chmod(0o600)
    with pytest.raises(UserError, match="different account"):
        cloud.provision(store)
    store.save({"CLOUDFLARE_ACCOUNT_ID": "bad/path"})
    with pytest.raises(UserError, match="32-character"):
        cloud.provision(store)
    assert cloud.requests == []


@pytest.mark.parametrize("unsafe", ["symlink", "fifo", "public", "json", "null"])
def test_unsafe_state_prevents_network_calls(store, tmp_path, unsafe):
    path = store.directory / "r2-setup.json"
    if unsafe == "symlink":
        path.symlink_to(tmp_path / "other")
    elif unsafe == "fifo":
        os.mkfifo(path, 0o600)
    else:
        path.write_text("null" if unsafe == "null" else "{}")
        path.chmod(0o644 if unsafe == "public" else 0o600)
    cloud = CloudflareMock()
    with pytest.raises(UserError):
        cloud.provision(store)
    assert cloud.requests == []


def test_nondefault_jurisdiction_uses_manual_fallback(store, monkeypatch):
    monkeypatch.setenv("R2_JURISDICTION", "eu")
    cloud = CloudflareMock()
    with pytest.raises(UserError, match="jurisdictional"):
        cloud.provision(store)
    assert cloud.requests == []
