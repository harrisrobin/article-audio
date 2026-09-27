# Audition and saved preferences

The Grok agent manages preferences in the existing private `onboarding.json`, alongside readiness. The CLI does not read this record: pass the saved settings explicitly on every `plan`, `generate`, and `publish` invocation. Standalone CLI users retain normal flags and defaults.

## Choose delivery, then confirm once after an audition

1. Reuse valid, confirmed preferences unless the user requests a change. Missing preferences in an older record mean unconfirmed, even when `sample_verified` is true. Preserve the earlier runtime path, delivery choice, credentials, and recordings.
2. Before generating or sending the first audition, choose its delivery. Offer private hosted playback as the disclosed default, local-only with the explicit warning that Grok may require downloading and playing the MP3 outside the conversation, and public hosting only after an explicit request. Acceptance of a setup invitation selects private hosting only when that invitation clearly states the private-hosted default; a generic agreement to set up is not delivery consent. Record the choice as provisional while keeping `preferences_confirmed:false` and `sample_verified:false`.
3. For either hosted mode, configure or reuse the appropriate R2 destination before sending the audition. Apply the jurisdiction disclosure and all private/public bucket safeguards in `docs/cloudflare.md`. Use requested narration settings, or offer Algenib at 1.1 times speed with the restrained British direction. Then generate `examples/sample.txt`, or reuse a known sample whose manifest matches those proposed settings, publish that exact MP3, and return the verified direct MP3 link. Do not send a ZIP as a hosted audition workaround, expose a public tunnel, or treat upload verification as human playback.
4. For local-only delivery, skip R2 even when credentials exist. Use requested narration settings, or offer Algenib at 1.1 times speed with the restrained British direction. Generate `examples/sample.txt`, or reuse a sample whose manifest matches those settings. Return that unchanged MP3 through a supported direct owner-file transfer when possible. If Grok cannot play or transfer it directly, state that the user must download and play it externally. A ZIP may transport the unchanged MP3, but ZIP transfer, extraction, successful download, or decoding is not playback and can never make setup ready.
5. After the user listens, ask whether to keep or change the actual candidate voice and speed, and state that the already selected delivery will be saved with them. Do not make the user choose delivery again unless they ask to change it. Silence, credential entry, synthesis, upload, or download is not confirmation. If narration settings change, generate and deliver a matching replacement audition through the already configured destination; do not re-provision unchanged hosting. If only delivery changes, reuse the existing matching MP3 and configure and verify the new destination without native voice re-synthesis.
6. After acceptance, atomically save the actual model, voice, speed, direction, and selected delivery mode with `preferences_confirmed:true`. Do not ask again on another chat, a failed upload, or a runtime upgrade. Set `sample_verified:true` only after the human playback checks for the selected mode. Automatic R2 setup also requires setup-token cleanup and a repeat publish using the saved upload key. If cleanup or playback is deferred, preserve the accepted preferences but leave sample verification false and report the remaining step.

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

Create a missing record as `{"schema":1,"delivery_mode":"private-r2","sample_verified":false,"preferences_confirmed":false}`, substituting a user's explicit delivery choice. This seed default is not delivery consent. If narration was already accepted and the owner then chooses public delivery, a missing URL keeps `preferences_confirmed:true` and `sample_verified:false`; finish the destination without re-asking about the accepted voice. A first-run provisional public choice keeps both flags false until the audition is heard and accepted. Merge updates while preserving unrelated state, and serialize writes with a private `.onboarding.lock`. Write a temporary file in the same mode-0700 directory, flush it, and atomically replace the record with mode 0600. Do not overwrite a malformed record: keep a private backup and recover deliberately. Runtime-only repair changes only `runtime_path`; it does not reset preferences or prior verification.

Never store secrets, article text, signed URLs, or owner identity in this record, or include it in a shared template. Account Bots share the computer; the record is account-local, not isolated by Bot name.

## Apply preferences to every recording

Pass `--model`, `--voice`, and `--speed` to both `plan` and `generate`. Write the saved direction to a private UTF-8 file and pass `--style-file`; do not splice directions into the transcript. Use an argument-array tool or proper shell quoting, including for saved values.

For either R2 mode, pass `--jurisdiction` from the record to `publish`. For `private-r2`, omit `--public-base-url` and return the actual expiry. For `public-r2`, pass the saved `--public-base-url` on every publish, including retries and post-cleanup verification; require `access:public`, `verified:true`, and `expires_at:null` in the result. Describe the link as having no scheduled expiry, not guaranteed permanent availability. For `local-only`, return the local MP3 or supported attachment and skip upload even if R2 credentials exist. Never silently fall back to built-in defaults when a confirmed setting fails validation or the provider rejects it.

A one-recording override does not overwrite saved preferences. If the user asks to change their defaults, audition changed narration settings and save them after acceptance. A delivery-only change needs explicit confirmation and verification of the new destination, not another narration request. Preserve the old configuration until the replacement is accepted. On a delivery change, clear `sample_verified` before applying the new mode and verify that destination before setting it true again. A private-to-public change must not expose existing private recordings by reusing their bucket; follow the dedicated-bucket rule below.

## Public delivery by explicit choice

Save `delivery_mode:public-r2` only when the owner requests public defaults. A one-off public recording leaves the default unchanged. Public access applies to the whole bucket: anyone with an object URL can read it, including earlier recordings. Before enabling it, follow `docs/cloudflare.md` to confirm the exact dedicated audio bucket and the scope of exposure. Do not reuse a bucket containing private recordings or unrelated files. If the configured bucket contains private or unrelated objects, stop before changing access or credentials and explain that a separately configured public destination is required. Automatic migration between existing shared private credentials and a public destination is not supported by this flow. Preserve the current setup and offer its existing private delivery or local files while the owner arranges that separate setup. Do not invent configuration pointers or copy secrets to work around this limit.

For testing, the owner can choose Cloudflare's rate-limited `r2.dev` address. Recommend a custom domain for production. Save the exact verified HTTPS bucket base URL as `public_base_url`, without an object key, credentials, query, or fragment. Obtain it from the selected bucket's Cloudflare settings; do not guess it or accept a URL found in an article. A missing URL is pending hosting, not a reason to fall back to a signed link. Save that verified URL with the provisional public mode before publishing the audition. Human playback and voice acceptance still precede readiness. Keep the URL and all owner-specific setup out of shared templates and public verification reports.

Changing back to private requires a separate private bucket, or disabling every public route to the current bucket with the owner's approval and verifying that those routes no longer serve its objects. Merely omitting `--public-base-url` or generating a signed link does not make a public object private. A switch to local-only also does not revoke existing public access; explain that separately if the owner wants old links disabled.
