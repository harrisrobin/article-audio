# Credential setup for Grok Bot

The CLI needs GEMINI_API_KEY for narration. Uploads additionally need R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_BUCKET. Ask for the R2 group only when hosted delivery is needed.

Use `auth status` to discover missing names. It never prints values. Gemini keys come from [Google AI Studio](https://aistudio.google.com/apikey). Create R2 object read/write credentials scoped to the chosen bucket in Cloudflare. Leave the bucket private for signed links.

## Native handoff, when supported

The Grok Bot runtime owns native secure forms. Its documentation confirms supported secret requests but does not provide a general public API for arbitrary third-party scripts. This package therefore has no invented `request_secret` call or guessed form schema.

If the Bot exposes a secure secret-request tool that can inject environment variables, request the exact missing names. Then run `auth import-env gemini` or `auth import-env r2` in that injected environment to save them. Environment variables override saved values during use.

If the host safely supplies a JSON file or stdin stream instead, pass it directly to `auth import-json` on stdin. Do not read its contents into the conversation or build a shell command containing the values. The JSON object uses the credential names above as keys. Saved values merge with existing credentials.

If the native tool only stores credentials for a connector and cannot hand them to the process, it cannot configure this script by itself. Use the local form below. Never use an ordinary chat question as a substitute for secure collection.

## Local password form

Run this on the Bot's computer in a terminal process that remains alive:

```bash
export ARTICLE_AUDIO_CONFIG_DIR=/workspace/.article-audio-config
bash /workspace/article-audio/scripts/article-audio auth setup gemini
```

The first JSON line contains a one-time `setup_url`. Open that exact URL in the browser on the same Bot computer. The user takes control and fills the password field, or a supported host secret-handoff mechanism fills it without exposing the value to the model. After submitting, the page reports success and the command exits. `auth setup r2` works the same way for hosting.

The URL expires after ten minutes. It does not work in a browser on the user's laptop unless the script is also running there. Do not expose or tunnel the form publicly. Do not inspect the filled password inputs or capture screenshots during credential entry. Retry by starting a fresh form if it expires.

For a human at a terminal, `auth setup gemini --method terminal` uses hidden input. Both form and terminal modes save values for future calls. Re-run setup to rotate a key.

## Storage and verification

Defaults: `$XDG_CONFIG_HOME/article-audio/credentials.json`, or `~/.config/article-audio/credentials.json` when XDG_CONFIG_HOME is unset. `ARTICLE_AUDIO_CONFIG_DIR` or `--config-dir` overrides the directory. Use `/workspace/.article-audio-config` consistently in Grok Bot for durable storage outside the source checkout.

The directory is mode 0700 and the file is mode 0600. Values are plaintext at rest. Every process and Bot running as that OS user can access them. The package refuses symlink credential files and insecure file permissions. Keep keys out of the shared template and repository.

After saving, run `auth status`, `models`, and a short generation. Status only establishes presence, not validity. A successful model-list request verifies some Gemini access; successful synthesis is the actual speech test. R2 credentials are validated through upload and ranged retrieval when you publish.

Native form compatibility must be tested on the installed Grok Bot version. The local form is implemented and independently testable. [Official secret-handoff documentation](https://docs.x.ai/grok-bot/approvals-security-and-privacy).
