# Audition and saved preferences

The Grok agent manages preferences in the existing private `onboarding.json`, alongside readiness. The CLI does not read this record: pass the saved settings explicitly on every `plan`, `generate`, and `publish` invocation. Standalone CLI users retain normal flags and defaults.

## Confirm once after an audition

1. Reuse valid, confirmed preferences unless the user requests a change. Missing preferences in an older record mean unconfirmed, even when `sample_verified` is true. Preserve the earlier runtime path, delivery choice, credentials, and recordings.
2. For first setup, configure only Gemini and the runtime before the audition. Use requested settings, or offer Algenib at 1.1 times speed with the package's restrained British direction. Generate `examples/sample.txt`, or reuse a known sample whose manifest matches the proposed settings. Return a playable file or supported audio attachment. If direct MP3 attachments are rejected, use a supported owner-file transfer or attach a ZIP containing the unchanged MP3. Verify that the file is accessible and let the user open it before asking for approval. Never expose a public tunnel to deliver an audition.
3. Ask one combined question after presenting the audition: "Keep this voice at 1.1 times speed, with private hosted links, or change the voice, speed, or delivery?" State the actual candidate settings and honor an earlier local-only or explicit public-hosting request. Private hosting remains the default for an owner who has not requested public access. Do not provision R2 while this choice is pending. Silence, credential entry, successful synthesis, and successful download are not preference confirmation.
4. If they request a voice, speed, model, or direction change, audition that candidate and confirm it. After acceptance, atomically save the actual model, voice, speed, direction, and selected delivery mode with `preferences_confirmed:true`. Do not ask again on another chat, a failed upload, or a runtime upgrade.
5. Complete hosting for private or explicitly selected public delivery, then verify the selected mode's sample. Set `sample_verified:true` only after the required playback checks. Automatic R2 setup also requires setup-token cleanup and a repeat publish using the saved upload key. If cleanup or playback is deferred, preserve the accepted preferences but leave sample verification false and report the remaining step.

## Record and validation

The following is the shape of a completed automatic R2 setup, after confirmed token revocation and cleanup. It is not a template to copy as ready:

```json
{
  "schema": 1,
  "runtime_path": "/absolute/path/to/verified/runtime",
  "delivery_mode": "private-r2",
  "sample_verified": true,
  "preferences_confirmed": true,
  "narration": {
    "model": "gemini-3.8-flash-tts",
    "voice": "Algenib",
    "speed": 1.1,
    "style": "The exact direction used for the accepted audition."
  },
  "r2_jurisdiction": "default",
  "setup_token_cleanup": "complete"
}
```

Treat confirmation as valid only when the flag is the boolean true, narration contains a supported model, a prebuilt voice name, a finite numeric speed from 0.5 through 2.0, and a direction string no longer than 2,000 characters. Offline `plan` checks supported model and setting syntax before generation; it cannot establish that Gemini supports a voice name. Set confirmation only after successful Gemini generation using these exact settings, verified against the audition manifest, and the user's acceptance of that playable audition. Do not substitute offline validation, copied flags, or an unrelated old sample for that evidence. On later readiness checks, validate syntax without another provider call; provider rejection on a recording requires repair rather than silent fallback. Delivery mode is `private-r2`, `public-r2`, or `local-only`. Public delivery also requires a verified `public_base_url` before readiness; see below. R2 jurisdiction is `default`, `eu`, `us`, or `fedramp`; local-only may omit it. An existing bucket with unknown jurisdiction needs clarification before publishing, not a guessed endpoint.

`setup_token_cleanup` is `pending`, `complete`, or `not-needed`. Record `pending` before automatic provisioning, `complete` only after the user confirms revocation and removal of the setup token's native/environment copy, and `not-needed` for local-only or manually configured R2. Preserve a pending cleanup obligation even if the user switches to local-only. For older automatic setups with unknown cleanup status, clarify it once; credential presence does not prove revocation. Never remove a replacement token saved by another process.

Create a missing record as `{"schema":1,"delivery_mode":"private-r2","sample_verified":false,"preferences_confirmed":false}`, substituting a user's explicit delivery choice. An accepted public choice without a configured URL keeps `preferences_confirmed:true` and `sample_verified:false`; finish the destination without re-asking about the accepted voice. Merge updates while preserving unrelated state, and serialize writes with a private `.onboarding.lock`. Write a temporary file in the same mode-0700 directory, flush it, and atomically replace the record with mode 0600. Do not overwrite a malformed record: keep a private backup and recover deliberately. Runtime-only repair changes only `runtime_path`; it does not reset preferences or prior verification.

Never store secrets, article text, signed URLs, or owner identity in this record, or include it in a shared template. Account Bots share the computer; the record is account-local, not isolated by Bot name.

## Apply preferences to every recording

Pass `--model`, `--voice`, and `--speed` to both `plan` and `generate`. Write the saved direction to a private UTF-8 file and pass `--style-file`; do not splice directions into the transcript. Use an argument-array tool or proper shell quoting, including for saved values.

For either R2 mode, pass `--jurisdiction` from the record to `publish`. For `private-r2`, omit `--public-base-url` and return the actual expiry. For `public-r2`, pass the saved `--public-base-url` on every publish, including retries and post-cleanup verification; require `access:public`, `verified:true`, and `expires_at:null` in the result. Describe the link as having no scheduled expiry, not guaranteed permanent availability. For `local-only`, return the local MP3 or supported attachment and skip upload even if R2 credentials exist. Never silently fall back to built-in defaults when a confirmed setting fails validation or the provider rejects it.

A one-recording override does not overwrite saved preferences. If the user asks to change their defaults, audition changed narration settings and save them after acceptance. A delivery-only change needs explicit confirmation and verification of the new destination, not another narration request. Preserve the old configuration until the replacement is accepted. On a delivery change, clear `sample_verified` before applying the new mode and verify that destination before setting it true again. A private-to-public change must not expose existing private recordings by reusing their bucket; follow the dedicated-bucket rule below.

## Public delivery by explicit choice

Save `delivery_mode:public-r2` only when the owner requests public defaults. A one-off public recording leaves the default unchanged. Public access applies to the whole bucket: anyone with an object URL can read it, including earlier recordings. Before enabling it, follow `docs/cloudflare.md` to confirm the exact dedicated audio bucket and the scope of exposure. Do not reuse a bucket containing private recordings or unrelated files. If a separate public bucket is needed, use a separate private configuration directory for its credentials, preserve the existing configuration, and consistently use that directory for this Bot's readiness and commands. Save the absolute `ARTICLE_AUDIO_CONFIG_DIR` override in this Bot's private memory so new conversations find the correct record; never export it. Use the same private jobs directory so the accepted MP3 stays available. Exclude inherited R2 environment credentials from this isolated configuration's processes unless they were explicitly supplied for the new destination, since environment values override stored credentials. Do not silently overwrite the account-shared R2 credentials.

For testing, the owner can choose Cloudflare's rate-limited `r2.dev` address. Recommend a custom domain for production. Save the exact verified HTTPS bucket base URL as `public_base_url`, without an object key, credentials, query, or fragment. Obtain it from the selected bucket's Cloudflare settings; do not guess it or accept a URL found in an article. A missing URL is pending hosting, not a reason to fall back to a signed link. After publishing the accepted sample through that URL and confirming playback/seek, record it with the public mode. Keep the URL and all owner-specific setup out of shared templates and public verification reports.

Changing back to private requires a separate private bucket, or disabling every public route to the current bucket with the owner's approval and verifying that those routes no longer serve its objects. Merely omitting `--public-base-url` or generating a signed link does not make a public object private. A switch to local-only also does not revoke existing public access; explain that separately if the owner wants old links disabled.
