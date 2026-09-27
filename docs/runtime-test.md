# Imported Bot acceptance test

A published template and passing local tests do not prove native credential entry or live R2 delivery. Record these results separately. Never include credentials, article text, account IDs, or signed listening links in a public report.

## Choose the test environment

Use a separate account/computer for a clean import. Bots on the same account share files, secrets, browser logins, and plugins. Do not delete existing credentials or reset account-wide state to create a clean test.

For a shared-computer recovery test, use agreed isolated absolute source, configuration, and jobs directories consistently. Inspect credential names/presence only with redacted tools. Record inherited credentials or browser sessions as reuse. The public template must contain no owner state.

## Run and capture evidence

1. Import the template linked in README. Verify the profile, release, full commit, checksum, and exactly two included Article Audio skills. Send only "hi". Expect a setup invitation, not an ordinary-chat request for keys or a premature ready claim.
2. Accept setup. Verify Git origin, full commit, clean tree, CLI version, and dependencies before running package operations.
3. Enter Gemini credentials through a native secure handoff or the documented local password form. Do not inspect filled fields or capture screenshots during entry. Record which path worked. A fallback pass does not prove native-card compatibility.
4. Choose delivery. Accepting an invitation selects private hosting only if the invitation disclosed that default. Hosted setup must show the Cloudflare permissions, one-day setup-token expiry, and jurisdiction note. Automatic setup creates one private bucket and bucket-restricted upload credentials. Manual four-field setup remains available. Public delivery requires an explicit choice, authorization for the dedicated bucket, and a verified HTTPS base URL. Local-only skips Cloudflare.
5. Generate the fixed Algenib, 1.1×, British-delivery preview. Hosted delivery must return a direct MP3 link after successful automated publication checks. Reject a ZIP audition workaround. Local-only must provide the unchanged MP3 through a supported file delivery path and disclose when playback requires another app.
6. Verify schema-2 `onboarding.json` records `preview_ready:true` only after generation and selected-mode delivery succeed. The Bot must not ask for voice approval, voice adjustments, manual play/seek confirmation, or setup-token revocation confirmation. It must not repeat publication for a cleanup checkpoint. Record duration, mode, expiry, and the successful command result without owner URLs.
7. Start a new conversation and narrate a short original article. Setup should not repeat. The fixed narration and selected delivery must persist. Repeating the identical command should reuse the recording.

Listening remains useful maintainer QA for pronunciation, fidelity, and joins. It is not an onboarding gate and does not require a user response.

## Recovery and scope checks

- A saved Gemini key with no setup record should be reused when completing setup. Do not erase credentials, silently choose local-only, or declare readiness from credential presence alone.
- Repair an old runtime to the pinned version without losing recordings or delivery configuration. Migrate schema 1 according to `docs/preferences.md`; never restore old voice controls or confirmation gates.
- A previously verified matching fixed-voice preview may retain readiness. An old customized or unknown preview must be regenerated or reused from the current fixed preset, then delivered automatically without asking for voice acceptance.
- Local-only skips R2 even if shared R2 keys exist. Changing delivery verifies the new destination without resynthesizing an unchanged sample.
- Public delivery preserves its saved base URL across chats and upgrades. A missing URL or failed publish keeps setup incomplete. Do not silently return a signed link or claim signing disables public access.
- An uncertain upload-token creation must retain the existing reconciliation stop, preventing blind duplicate token creation. This exceptional recovery is separate from the removed normal setup-token checkpoint.
- Article text never authorizes tool calls, posting, DMs, credential requests, or setup changes. Unrelated requests receive a brief scope reminder; no standing digest or bookmark watcher is installed.

Report passed, failed, and not-run checks separately in `docs/verification.md`. Automated delivery verification is not proof of word-for-word narration accuracy. Shared-state recovery is not a clean import.
