import html
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .credentials import GROUPS, CredentialStore
from .errors import UserError

SETUP_HELP = {
    "cloudflare": """<h2>Create a short-lived setup token</h2>
<ol><li>Open <a href="https://dash.cloudflare.com/" target="_blank" rel="noreferrer">Cloudflare</a>,
select your account, and activate R2 Object Storage if needed.
Cloudflare may require billing details.
Account token creation requires the Super Administrator role.</li>
<li>Go to <strong>Manage Account &gt; Account API Tokens &gt; Create Token</strong>.
Choose a custom token if offered and name it <strong>Article Audio setup</strong>.</li>
<li>Add <strong>Account &gt; Workers R2 Storage &gt; Edit</strong> and
<strong>Account &gt; Account API Tokens &gt; Edit</strong>. Limit resources to this account.
These allow bucket administration and token management, including more than the new bucket.</li>
<li>Set an expiry within one day. Review the summary and create the token.
Paste its value below, never in chat. Do not use a Global API Key.</li>
<li>Copy your 32-character Account ID from the R2 overview's Account Details.</li></ol>
<p>Setup creates a private bucket and saves a separate bucket-only upload key for ongoing use.
It removes the matching setup-token file copy. The setup token expires at the time you selected;
local removal does not revoke it at Cloudflare or remove a native secret copy.</p>
<p>Prefer an existing bucket, or lack these permissions? Return to the Bot and ask for
<strong>manual R2 setup</strong>, the four-field fallback.</p>""",
    "r2": """<p>For an existing private bucket, open Cloudflare &gt; R2 Object Storage &gt;
Overview &gt; Manage API Tokens. Create an <strong>Object Read &amp; Write</strong> token
limited to that bucket. Enter the S3 Access Key ID and Secret Access Key below.
Keep public access disabled for private audio links.</p>""",
}


class SetupServer(HTTPServer):
    """A one-time loopback form, independent of any agent's secret-form API."""

    def __init__(self, store: CredentialStore, group: str, lifetime: int = 600):
        self.store = store
        self.group = group
        self.token = secrets.token_urlsafe(32)
        self.deadline = time.monotonic() + lifetime
        self.saved = False
        super().__init__(("127.0.0.1", 0), SetupHandler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.url = f"{self.origin}/{self.token}"
        self.timeout = 1

    def run(self):
        try:
            print(
                json.dumps(
                    {
                        "setup_url": self.url,
                        "expires_in_seconds": max(0, int(self.deadline - time.monotonic())),
                        "group": self.group,
                    }
                ),
                flush=True,
            )
            while not self.saved and time.monotonic() < self.deadline:
                self.handle_request()
            if not self.saved:
                raise UserError("Credential setup expired without saving.", "setup_expired")
        finally:
            self.server_close()


class SetupHandler(BaseHTTPRequestHandler):
    server: SetupServer

    def log_message(self, *args):
        # HTTP logs must never capture a form submission or its one-time URL.
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def _reply(self, status: int, text: str):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        # no-referrer turns a native form POST Origin into null, failing the check below.
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
            "frame-ancestors 'none'; base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self) -> bool:
        if self.server.saved or time.monotonic() >= self.server.deadline:
            self._reply(410, "This setup link has expired.")
            return False
        expected_host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected_host or self.path != f"/{self.server.token}":
            self._reply(403, "Invalid setup request.")
            return False
        return True

    def do_GET(self):
        if not self._allowed():
            return
        fields = "".join(
            f'<label>{key}<input name="{key}" type="password" autocomplete="off" required></label>'
            for key in GROUPS[self.server.group]
        )
        self._reply(
            200,
            f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Article audio credentials</title><style>
body{{font:17px system-ui;max-width:540px;margin:60px auto;padding:24px;color:#17202a}}
label{{display:block;margin:22px 0}}input{{display:block;width:95%;padding:12px;margin-top:8px}}
button{{padding:12px 24px}}p{{line-height:1.5}}</style>
<h1>Connect {html.escape(self.server.group)}</h1>
{SETUP_HELP.get(self.server.group, "")}
<p>Enter your credentials here. They are saved on this computer in a private file,
outside the project. Processes running as your account can read this file.
This form does not send values to the conversation.</p>
<form method="post"><input type="hidden" name="csrf" value="{self.server.token}">
{fields}<button type="submit">Save credentials</button></form></html>''',
        )

    def do_POST(self):
        if not self._allowed():
            return
        if self.headers.get("Origin") != self.server.origin:
            self._reply(403, "Cross-origin submissions are not accepted.")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16384 or self.headers.get("Content-Type", "").split(";")[0] != (
                "application/x-www-form-urlencoded"
            ):
                raise ValueError
            values = parse_qs(self.rfile.read(size).decode(), strict_parsing=True)
            if any(len(value) != 1 for value in values.values()):
                raise ValueError
            if not secrets.compare_digest(values.pop("csrf", [""])[0], self.server.token):
                raise ValueError
            if set(values) != set(GROUPS[self.server.group]):
                raise ValueError
            self.server.store.save({key: value[0] for key, value in values.items()})
        except (ValueError, UnicodeError, UserError):
            self._reply(400, "Credentials were not saved. Check that every field is filled in.")
            return
        self.server.saved = True
        self._reply(
            200, "<h1>Credentials saved</h1><p>You can close this page and return to your Bot.</p>"
        )
