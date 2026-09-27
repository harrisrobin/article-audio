import hashlib
import json
import os
import re
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from .credentials import GROUPS, CredentialStore
from .errors import UserError
from .files import atomic_write, file_lock, private_dir, read_private_json

API = "https://api.cloudflare.com/client/v4"
OBJECT_WRITE = "Workers R2 Storage Bucket Item Write"
PREVIEW = "Publish the fixed-voice sample using the saved bucket upload credentials."
REPLACED_SETUP = (
    "Newer Cloudflare setup credentials were preserved; keep replacement credentials intact. "
    + PREVIEW
)


class CloudflareAPI:
    def __init__(self, http: httpx.Client, account: str, token: str):
        self.http = http
        self.root = f"{API}/accounts/{account}"
        self.headers = {"Authorization": f"Bearer {token}"}

    def request(self, method: str, path: str, *, body=None, params=None, missing=False):
        try:
            response = self.http.request(
                method,
                self.root + path,
                headers=self.headers,
                json=body,
                params=params,
                timeout=30,
                follow_redirects=False,
            )
            if missing and response.status_code == 404:
                return None
            if response.status_code in (401, 403):
                raise UserError(
                    "Cloudflare denied setup. Check the account ID, token expiry, and Account > "
                    "Workers R2 Storage > Edit plus Account > Account API Tokens > Edit on that "
                    "account. R2 must be activated. See docs/cloudflare.md or use auth setup r2.",
                    "cloudflare_denied",
                )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise ValueError
            return payload["result"]
        except (httpx.HTTPError, ValueError, KeyError):
            # Responses and exception URLs can contain credentials. Never echo them.
            raise UserError(
                "Cloudflare setup request failed or returned an unexpected response. "
                "Check connectivity, token permissions and R2 activation. See docs/cloudflare.md.",
                "cloudflare_failed",
            ) from None

    def object_write_permission(self) -> str:
        result = self.request("GET", "/tokens/permission_groups", params={"name": OBJECT_WRITE})
        matches = (
            [
                item.get("id")
                for item in result
                if isinstance(item, dict) and item.get("name") == OBJECT_WRITE
            ]
            if isinstance(result, list)
            else []
        )
        if (
            len(matches) != 1
            or not isinstance(matches[0], str)
            or not re.fullmatch(r"[a-f0-9]{32}", matches[0])
        ):
            raise UserError(
                "Cloudflare's bucket write permission could not be resolved.", "cloudflare_failed"
            )
        return matches[0]

    def ensure_private_bucket(self, bucket: str) -> None:
        path = f"/r2/buckets/{bucket}"
        result = self.request("GET", path, missing=True)
        if result is None:
            result = self.request("POST", "/r2/buckets", body={"name": bucket})
        if not isinstance(result, dict) or result.get("name") != bucket:
            raise UserError("Cloudflare did not confirm the setup bucket.", "cloudflare_failed")
        managed = self.request("GET", path + "/domains/managed")
        custom = self.request("GET", path + "/domains/custom")
        if (
            not isinstance(managed, dict)
            or managed.get("enabled") is not False
            or not isinstance(custom, dict)
            or not isinstance(custom.get("domains"), list)
            or any(
                not isinstance(domain, dict) or domain.get("enabled") is not False
                for domain in custom["domains"]
            )
        ):
            raise UserError(
                "Setup bucket public access is enabled or could not be verified. "
                "Disable its r2.dev and custom-domain access in Cloudflare, then retry. "
                "No public settings were changed.",
                "bucket_not_private",
            )


@dataclass
class SetupState:
    account: str
    bucket: str
    token_requested: bool = False

    @classmethod
    def load(cls, path: Path, account: str):
        try:
            raw = read_private_json(path)
            if raw is None and not path.exists():
                return cls(account, "article-audio-" + secrets.token_hex(6))
            if (
                not isinstance(raw, dict)
                or set(raw) != {"account", "bucket", "token_requested"}
                or not isinstance(raw["account"], str)
                or not re.fullmatch(r"[a-f0-9]{32}", raw["account"])
                or not isinstance(raw["bucket"], str)
                or not re.fullmatch(r"article-audio-[a-f0-9]{12}", raw["bucket"])
                or type(raw["token_requested"]) is not bool
            ):
                raise ValueError
            state = cls(**raw)
        except ValueError:
            raise UserError(
                "R2 setup record is damaged. Preserve r2-setup.json and use the manual "
                "four-field setup, or reconcile its bucket and token in Cloudflare first.",
                "unsafe_storage",
            ) from None
        if state.account != account:
            raise UserError(
                "R2 setup belongs to a different account. Use the original account "
                "or a separate --config-dir; no resources were changed."
            )
        return state

    def save(self, path: Path):
        atomic_write(path, json.dumps(asdict(self)).encode())

    @property
    def token_name(self):
        return self.bucket + "-uploads"


def provision_r2(store: CredentialStore, http: httpx.Client, *, retry_token=False) -> dict:
    private_dir(store.directory)
    with file_lock(store.directory / ".r2-setup.lock"):
        configured = store.snapshot("r2")
        if all(configured.values()):
            snapshot = store.snapshot("cloudflare")
            removed = store.save({}, remove_if_matches=snapshot, if_unchanged=configured)
            return {
                "configured": True,
                "reused": True,
                "setup_token_removed_from_file": removed,
                "next_step": "Use the existing bucket's jurisdiction. "
                + (PREVIEW if removed else REPLACED_SETUP),
            }
        if any(configured.values()):
            raise UserError(
                "Partial R2 credentials already exist. Complete auth setup r2, "
                "or use a separate --config-dir for automatic setup."
            )
        if os.environ.get("R2_JURISDICTION", "default") != "default":
            raise UserError(
                "Automatic setup creates a default-jurisdiction bucket. Use manual "
                "auth setup r2 for jurisdictional buckets, or unset R2_JURISDICTION."
            )
        values = store.require("cloudflare")
        account = values["CLOUDFLARE_ACCOUNT_ID"].lower()
        if not re.fullmatch(r"[a-f0-9]{32}", account):
            raise UserError("CLOUDFLARE_ACCOUNT_ID must be a 32-character Cloudflare account ID.")
        token = CredentialStore.validate(values)["CLOUDFLARE_API_TOKEN"]
        api = CloudflareAPI(http, account, token)
        path = store.directory / "r2-setup.json"
        state = SetupState.load(path, account)
        if state.token_requested and not retry_token:
            raise UserError(
                f"A previous token request may have succeeded. In Cloudflare Account API Tokens, "
                f"revoke any token named {state.token_name} before retrying with "
                "auth provision-r2 --retry-token. Do not delete the bucket. "
                "Alternatively use auth setup r2 with manually created credentials.",
                "token_recovery_required",
            )
        permission = api.object_write_permission()
        state.save(path)
        api.ensure_private_bucket(state.bucket)
        state.token_requested = True
        state.save(path)
        # Persist intent before POST. An interrupted request cannot safely be repeated.
        result = api.request(
            "POST",
            "/tokens",
            body={
                "name": state.token_name,
                "policies": [
                    {
                        "effect": "allow",
                        "resources": {
                            f"com.cloudflare.edge.r2.bucket.{account}_default_{state.bucket}": "*"
                        },
                        "permission_groups": [{"id": permission}],
                    }
                ],
            },
        )
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("id"), str)
            or not re.fullmatch(r"[a-f0-9]{32}", result["id"])
            or not isinstance(result.get("value"), str)
            or not 40 <= len(result["value"]) <= 8192
            or any(ord(char) < 33 for char in result["value"])
        ):
            raise UserError(
                "Cloudflare did not return usable token credentials. Retry setup "
                "for recovery instructions.",
                "cloudflare_failed",
            )
        try:
            removed = store.save(
                {
                    "R2_ACCOUNT_ID": account,
                    "R2_BUCKET": state.bucket,
                    "R2_ACCESS_KEY_ID": result["id"],
                    "R2_SECRET_ACCESS_KEY": hashlib.sha256(result["value"].encode()).hexdigest(),
                },
                remove_if_matches=values,
                if_absent=GROUPS["r2"],
            )
        except UserError as error:
            if error.code == "credentials_changed":
                try:
                    removed = store.save({}, remove_if_matches=values)
                    cleanup = (
                        "The setup-token file copy was removed. " + PREVIEW
                        if removed
                        else REPLACED_SETUP
                    )
                except (UserError, OSError):
                    cleanup = (
                        "The setup-token file copy could not be removed. Revoke the "
                        "token used for this run and remove only its file/native/environment "
                        "copies; preserve any replacement credentials."
                    )
                raise UserError(
                    f"R2 credentials changed during setup and were preserved. Revoke the unused "
                    f"Cloudflare upload token named {state.token_name}. The new bucket remains; "
                    "no existing bucket was changed. "
                    + cleanup
                    + " Keep the existing manual upload credentials.",
                    "credentials_changed",
                ) from None
            raise
        return {
            "configured": True,
            "reused": False,
            "bucket": state.bucket,
            "jurisdiction": "default",
            "setup_token_removed_from_file": removed,
            "next_step": PREVIEW if removed else REPLACED_SETUP,
        }
