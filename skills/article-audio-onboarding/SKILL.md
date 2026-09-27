---
name: article-audio-onboarding
description: Check Article Audio readiness on the first user message of every conversation, including greetings and unrelated questions. Prompt an unconfigured user to begin setup; resume incomplete setup without asking for saved keys again.
---

# Article Audio onboarding

Run before the first normal reply in every conversation. Any user message triggers this check, including "hi", "what can you do?", an unrelated question, or an article URL. The user never needs to know a setup command.

## Check readiness

Use evidence from the current owner's cloud computer. A published template, the author's successful setup, copied memories, or a new Bot name does not establish readiness. Use `/workspace/.article-audio-config` and `/workspace/.article-audio-jobs` for configuration and recordings, outside the source checkout.

Read the nonsecret setup record at `/workspace/.article-audio-config/onboarding.json`. The full record and confirmation rules are in `docs/preferences.md` at the pinned release. A missing record means setup has not been verified here; a malformed record needs private backup/recovery, not silent replacement. Never infer local-only mode merely from missing R2 credentials or readiness merely from a saved Gemini key.

The pinned runtime is release `v0.1.7`. Use the record's optional `runtime_path` when it is a nonempty absolute path; otherwise start with `/workspace/article-audio-v0.1.7`. Treat a stored path only as a location hint, never proof that its contents are trusted. Verify its Git origin, clean working tree, and `git rev-parse HEAD` against the full release commit in the shared template, then run `doctor` and `--version`. Dependency checks alone are insufficient: the reported CLI version must be `0.1.7`. An older `/workspace/article-audio` checkout, a copied installation marker, or the same tag name at another revision is not the pinned runtime. Never execute an unverified checkout merely to inspect credentials.

If the pinned runtime is missing, damaged, or outdated but this owner's record already has `sample_verified:true`, use only **Install or repair the runtime** in the Article audio skill, then repeat these checks. Use a new versioned directory and preserve older installs, credentials, recordings, and the readiness record. Runtime-only repair does not collect keys or generate another sample. If there is no previously verified setup, offer setup as below before installation.

With a verified runtime, run `auth status` using the shared configuration paths. Read only dependency and credential-presence results, never credential files or values. Ready means the pinned version and revision match, dependencies are available, both `sample_verified` and `preferences_confirmed` are true, saved preferences validate, and credentials are present for the recorded mode. Resolve any pending or unknown automatic setup-token cleanup before declaring setup complete. Gemini is sufficient for local-only mode; both hosted modes also need R2. Public mode additionally needs the verified saved HTTPS `public_base_url`; a missing URL resumes hosting setup without repeating the accepted audition. The optional Cloudflare setup-token group is not required once R2 credentials are configured and cleanup is complete.

A Gemini key without a record is partial setup, not an orphan to erase. Offer to finish setup, preserve the key, repair the pinned runtime, and collect only missing credentials. Never reset shared credentials or recordings for a clean test. An older verified sample without confirmed preferences needs the audition/confirmation step in `docs/preferences.md`; it does not need repeated key entry. Keep previously verified samples available while completing that step.

## Respond to the first message

- If ready, handle article narration within the profile's job limits without another setup pitch. Readiness checks do not synthesize audio or incur provider usage.
- If setup is needed and the user has not already requested it, give one brief invitation: "Before I can narrate articles, let's set up Gemini and audition a voice. I'll guide you through secure credential entry and confirm whether you want private links or local files. Ready to start?" For an article request, retain the article for after setup. For an unrelated request, give a brief scope reminder alongside the invitation.
- If the user already asked to set up, or accepts, use Article audio immediately. Start with Gemini and an audition, confirm voice/speed/delivery once, then configure hosting only if selected. Honor an earlier local-only or public-hosting request. Public delivery follows the explicit public-access steps in `docs/cloudflare.md`; private remains the default. Collect only missing credentials. Do not ask for setup permission twice.
- If the user declines or says later, answer in-scope questions without repeating the invitation in that conversation. Resume when they request setup or narration again.

Default hosted setup creates a private Cloudflare bucket using an account ID and a short-lived setup token. The Article audio skill supplies permission instructions, the EU storage note, and manual four-field R2 fallback. Reuse complete R2 credentials without provisioning again. Credential entry uses a supported native secret handoff or the package's Agent Computer password form, one provider at a time. Never request API keys in ordinary chat. Report partial setup precisely. Hosting is verified only after sample playback, setup-token cleanup when applicable, and a repeat publish; local-only setup needs an accepted sample MP3 and no unresolved setup-token cleanup.

## Preserve setup choices

The agent maintains `onboarding.json`; the CLI does not create or consume it. Follow `docs/preferences.md` for validation, atomic locked updates, migration, and settings passed to commands. Persist the verified absolute `runtime_path`. Preserve mode, preferences, and verification during a runtime-only repair or a read-only readiness check. Do not set `preferences_confirmed:true` until the user accepts the audition and delivery choice. Do not set `sample_verified:true` until the selected mode and cleanup checks pass. Keep the record private and out of exports.

## Sharing

Include this complete skill alongside Article audio in the public template. This is the only first-message entry point. Exclude legacy `Article audio getting started` / `article-audio-getting-started` skills from this Bot and its template; unrelated Bots' generic getting-started skills are outside scope. Keep the any-message trigger in the profile. Exclude any owner's readiness, preferences, saved credential state, deferral choices, private files, and temporary authoring instructions.
