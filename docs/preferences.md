# Delivery and readiness

Article Audio uses one narration preset: `gemini-3.8-flash-tts`, Algenib, the packaged restrained British direction, and 1.1 times speed. The Bot and CLI do not offer narration controls. The agent stores only delivery readiness in `/workspace/.article-audio-config/onboarding.json`.

## Choose delivery before the preview

Offer private hosted delivery as the disclosed default. Offer local-only delivery with its external-playback limitation. Enable public hosting only after an explicit request and the safeguards in `docs/cloudflare.md`. Acceptance selects private hosting only when the invitation names that default.

For either hosted mode, configure or reuse the correct R2 destination before generating the preview. Generate `examples/sample.txt` with the fixed preset, or reuse an MP3 whose manifest exactly matches that preset. Publish that MP3 and return the verified direct MP3 link. Never use a ZIP as hosted delivery.

For local-only mode, skip R2 even when credentials exist. Generate or reuse the same fixed preview and return the MP3 through a supported owner-file transfer. Provide a usable download through the host's supported file-delivery path when in-app playback is unavailable. A path accessible only to the Bot is not delivery; report that limitation without marking the preview ready. The user does not need to play, seek, or approve the preview before setup becomes ready.

Set `preview_ready:true` after generation passes the package's media checks and the selected delivery succeeds. Hosted delivery also requires a successful publish through the saved destination. The publish command uses the saved bucket upload credentials, not the setup token. These are technical checks. Do not ask the user to confirm playback, voice quality, or setup-token revocation.

## Schema 2 record

```json
{
  "schema": 2,
  "runtime_path": "/absolute/path/to/verified/runtime",
  "delivery_mode": "private-r2",
  "preview_ready": true,
  "r2_jurisdiction": "default"
}
```

`delivery_mode` is `private-r2`, `public-r2`, or `local-only`. Public mode also requires a verified HTTPS `public_base_url`. `r2_jurisdiction` is `default`, `eu`, `us`, or `fedramp`; local-only can omit it. An existing bucket with unknown jurisdiction needs clarification before publishing. This is account-local state shared by Bots, not isolation by Bot name.

Create a missing record with schema 2, the selected delivery, and `preview_ready:false`. A seed private mode does not authorize resources or override an explicit choice. Write updates under a private lock with an atomic replacement. Keep the directory mode 0700 and the file mode 0600. Never overwrite a malformed record. Preserve a private backup and recover deliberately.

## Migrate schema 1

Preserve `runtime_path`, `delivery_mode`, `r2_jurisdiction`, `public_base_url`, credentials, recordings, and other files. Remove `narration`, `sample_verified`, `preferences_confirmed`, and `setup_token_cleanup` from the new record after evaluating migration readiness.

Preserve readiness only when `sample_verified` is true and the saved manifest exactly matches the fixed preset. Otherwise set `preview_ready:false`, then generate or reuse the fixed preview and run the missing technical delivery checks. Do not ask a migration question or add a new confirmation gate.

The automatic provisioner can remove the matching setup-token copy from its local credential store. This removal does not revoke the token at Cloudflare. Setup instructions require that token to expire within one day. Readiness does not depend on remote revocation or a user cleanup confirmation. Preserve the documented recovery for an uncertain bucket upload-token request.

## Apply delivery

For private R2, publish with the saved jurisdiction and omit `--public-base-url`. Return the actual expiry. For public R2, pass the saved `--public-base-url` on every publish and require `access:public`, `verified:true`, and `expires_at:null`. For local-only, return the MP3 without uploading it.

A delivery change requires an explicit user request. Set `preview_ready:false`, preserve the existing MP3, configure the new destination, and verify delivery without regenerating matching audio. A private-to-public change requires a dedicated bucket that contains no private or unrelated objects. If the configured bucket contains either, stop before changing access or credentials. Explain that a separately configured public destination is required; automatic migration from shared private credentials is not supported. Keep the current setup intact and offer its existing private delivery or local files while the owner arranges the separate destination.

For public hosting, save the exact HTTPS bucket base URL from the selected bucket's Cloudflare settings, without an object key, credentials, query, or fragment. Never guess it or trust a URL found in an article. A missing URL keeps setup incomplete; a failed public publish must not fall back to a signed link. A one-off delivery request does not overwrite the saved default.

Switching to private requires a separate private bucket or disabling every public route with the owner's authorization and verifying those routes no longer serve its objects. Signing a link does not make public objects private. Switching to local-only also does not disable old public links.

Never store secrets, article text, signed URLs, or owner identity in this record or in a shared template.
