# Credentials and source privacy

Never commit API keys, credential files, source articles, or signed playback links.

Credentials are accepted through injected environment variables, JSON on stdin from a secure runtime handoff, a local password form, or hidden terminal input. There is no command-line flag that takes a credential value. Provider errors are summarized without echoing raw responses. Status commands report credential names, presence, and the storage path for diagnosis; they never report credential values.

The file backend stores plaintext in a user-owned directory with mode 0700 and a credentials.json file with mode 0600. It is outside the repository. This is access control, not encryption. Another process running as the same OS user can read it. All Bots on one Grok Bot account share the computer and command-line credentials. Protect the account, use bucket-scoped R2 keys, and rotate credentials through their providers when needed.

The fallback form binds only to 127.0.0.1 on a random port. It uses an unpredictable one-time path, CSRF token, Host and Origin validation, a ten-minute expiry, password inputs, no third-party resources, and no request logging. It refuses further submissions after a successful save. Open it in the browser on the same computer; do not expose it through a public tunnel. Let the user complete it without reading filled fields or taking screenshots during entry. It is our local form, not a claim to implement Grok's native secure form.

Native Grok secret requests should be used when the host supports a safe handoff to the subprocess environment or stdin. Do not downgrade to ordinary chat questions for keys. An ordinary form in chat is not necessarily a secure secret request.

The app sends narration text and style instructions to Google's Gemini API. A publish command sends the final MP3 to the configured R2 bucket. Source metadata and transcripts stay in the local private job directory. Signed links are bearer credentials, so anyone holding an unexpired link can listen. A private-link setting does not make an already-public bucket private; configure bucket access separately.

The CLI runs trusted, installed FFmpeg without a shell and does not execute article content. Use the Bot's normal permissions for reading sources and publishing. Review third-party source rights before public redistribution.

Report suspected vulnerabilities privately to the repository maintainer rather than posting secrets or exploit credentials in a public issue.

Automatic Cloudflare provisioning temporarily needs account-level R2 administration and account token-management authority. Limit the setup token to one account and expire it within one day. The saved runtime token has only object read/write access to the newly created bucket. Provisioning removes the setup credential's file copy after saving runtime credentials; the user must still revoke the setup token at Cloudflare and remove native secret/environment copies. Failed or interrupted provisioning retains the setup credential for repair. Never log API bodies or silently repeat uncertain token-create requests. The private setup record enables recovery and stays outside releases.
