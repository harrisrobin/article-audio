# Credential setup for Grok Bot

The CLI needs `GEMINI_API_KEY` for narration. Hosted setup defaults to `CLOUDFLARE_ACCOUNT_ID` plus one short-lived `CLOUDFLARE_API_TOKEN`, then `auth provision-r2` creates a private bucket and stores the four R2 upload fields. Reuse complete existing R2 credentials. For manual setup, retain `auth setup r2` and its four fields: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and `R2_BUCKET`.

Before requesting a Cloudflare token, show the dashboard steps, exact permissions, account scope, and expiry from [Cloudflare setup](cloudflare.md). Explain its temporary account token-management authority and offer the manual fallback. Gemini keys come from [Google AI Studio](https://aistudio.google.com/apikey).

Run `auth status` to discover missing names. It never prints values. Complete one provider at a time; reuse the saved Gemini key. Ask only for Gemini in local-only mode. Presence of the optional Cloudflare setup group is not needed after R2 is configured.

## Native handoff, when supported

The Grok Bot runtime owns native secure forms. Its documentation describes secure cards and named environment-variable secrets, but the installed host must provide a supported handoff to this process. This package therefore has no invented `request_secret` call or guessed form schema.

Try the native secure card for each missing secret first, including Cloudflare and manual R2 secrets. Do not infer that R2 requires the browser form because it has multiple fields. When the tool can inject environment variables, request the exact missing names. Run `auth import-env gemini` or `auth import-env r2` to persist runtime credentials. For the temporary Cloudflare setup token, run `auth provision-r2` directly in the injected environment; avoid persisting it unnecessarily. Environment variables override saved values during use.

If the host safely supplies a JSON file or stdin stream instead, pass it directly to `auth import-json` on stdin. Do not read its contents into the conversation or build a shell command containing the values. The JSON object uses the credential names above as keys. Saved values merge with existing credentials.

If the native tool only stores credentials for a connector and cannot hand them to the process, it cannot configure this script by itself. Use the local form below. Never use an ordinary chat question as a substitute for secure collection.

## Local password form

Run this on the Bot's computer in a terminal process that remains alive:

```bash
export ARTICLE_AUDIO_CONFIG_DIR=/workspace/.article-audio-config
bash /workspace/article-audio-v0.1.8/scripts/article-audio auth setup gemini
```

The first JSON line contains a one-time `setup_url`. Open that exact URL in the browser on the same Bot computer. The user takes control and fills the password field, or a supported host secret-handoff mechanism fills it without exposing the value to the model. After submitting, the page reports success and the command exits. `auth setup cloudflare` shows the two-field automatic-setup form with token instructions. `auth setup r2` keeps the four-field manual fallback.

The URL expires after ten minutes. It does not work in a browser on the user's laptop unless the script is also running there. Do not expose or tunnel the form publicly. Do not inspect the filled password inputs or capture screenshots during credential entry. Retry by starting a fresh form if it expires.

For a human at a terminal, `auth setup gemini --method terminal` uses hidden input. Both form and terminal modes save values for future calls. Re-run setup to rotate a key.

## Recover a damaged credential file

Ordinary rotation works when the saved file is valid. Setup deliberately refuses to overwrite unreadable or damaged storage, because another provider's key might otherwise be lost.

For a mode error, verify that the file is a regular file owned by your account, then restore mode 0600 inside the private mode-0700 directory and retry. Do not follow or change a symlink's target.

For malformed JSON, unsupported saved fields, or a file larger than 65,536 bytes, move `credentials.json` to a private backup name in the same mode-0700 directory, then collect each provider again with `auth setup`. Keep the backup protected with mode 0600. Do not print its contents or put it in the source checkout. This preserves the old file while allowing a fresh store; repeating setup before moving it cannot repair it. A nonregular path, such as a named pipe, is rejected immediately; replace that path with a regular credential file through setup.

## Storage and verification

Defaults: `$XDG_CONFIG_HOME/article-audio/credentials.json`, or `~/.config/article-audio/credentials.json` when XDG_CONFIG_HOME is unset. `ARTICLE_AUDIO_CONFIG_DIR` or `--config-dir` overrides the directory. Use `/workspace/.article-audio-config` consistently in Grok Bot for durable storage outside the source checkout.

The directory is mode 0700 and the file is mode 0600. Values are plaintext at rest. Every process and Bot running as that OS user can access them. The package refuses symlink credential files and insecure file permissions. Keep keys out of the shared template and repository.

After saving, run `auth status`, `models`, and a short generation. Status only establishes presence, not validity. A successful model-list request verifies some Gemini access; successful synthesis is the actual speech test. R2 credentials are validated through upload and ranged retrieval when you publish.

Native form compatibility must be tested on the installed Grok Bot version. The local form is implemented and independently testable. [Official secret-handoff documentation](https://cursor.com/help/grok-bot/secrets).

## Diagnose a saved native secret before requesting it again

A card marked Saved proves vault storage, not subprocess delivery. Check the exact variable names and supported handoff in the installed tool's schema, then run `auth status` in a fresh host execution context. Read names/presence only. A normal child process inherits its parent's environment; starting a child with `env -i` clears injected secrets and cannot test a fresh host injection. Do not print values to test whether masking works. If names remain saved in the Bot's Secrets UI but unavailable to the CLI, report an unverified host handoff and offer the local form once. Do not repeatedly request or replace the same native secret. See [Grok secret storage](https://cursor.com/help/grok-bot/secrets).

If a local form reports a cross-origin rejection, stop repeated entry and inspect the installed runtime version and nonsecret request-origin behavior. Keep exact Host, Origin, and CSRF validation intact. Releases before 0.1.7 used `Referrer-Policy: no-referrer`, which can make an ordinary browser form POST send `Origin: null`. Upgrade the runtime before retrying; accepting null origins is not the repair.
