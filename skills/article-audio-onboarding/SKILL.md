---
name: article-audio-onboarding
description: Check Article Audio readiness on the first user message of every conversation. Invite an unconfigured user to begin setup and resume incomplete setup without asking for saved keys again.
---

# Article Audio onboarding

Run before the first normal reply in every conversation. Use evidence from this owner's cloud computer. A published template or another owner's setup does not establish readiness.

Read `/workspace/.article-audio-config/onboarding.json`. Follow `docs/preferences.md` from the pinned release for schema 2 validation and schema 1 migration. A missing record means setup is incomplete. Back up and recover a malformed record instead of replacing it. Preserve saved credentials and recordings.

The pinned runtime is release `v0.2.0`. Use a valid absolute `runtime_path`, or `/workspace/article-audio-v0.2.0`. Verify the Git origin, clean tree, full release commit, CLI version 0.2.0, and `doctor` before executing package operations. Evaluate schema 1 migration first. Only a valid migrated or existing schema 2 record with `preview_ready:true` qualifies for runtime-only repair; preserve its delivery and credentials. An old customized or unknown preview needs the fixed-preset preview and delivery checks.

Ready means the runtime checks pass, `preview_ready` is boolean true, the delivery record validates, and the required credentials are present. Gemini is sufficient for local-only. Both R2 modes need R2 credentials. Public mode also needs a verified HTTPS `public_base_url`. Do not require playback, seeking, voice approval, or setup-token revocation confirmation.

If setup is incomplete and the user has not already requested or accepted setup, invite the user once. Name private hosted MP3 delivery as the default, local-only as an option, and public hosting as an explicit choice. Explain that local-only skips R2 but needs supported MP3 file delivery, possibly for playback in another app. If the host cannot deliver the file, report that limitation and leave preview readiness false. A generic setup request does not select delivery. Acceptance of an invitation selects private hosting only when the invitation named that default.

After acceptance or an explicit setup request, use Article audio immediately. Collect only missing credentials, choose delivery, generate the fixed preview, and complete its technical delivery checks. Preserve an article request for after setup. If the user declines, do not repeat the invitation in that conversation.

The agent maintains `onboarding.json`; the CLI does not consume it. Persist the verified runtime path and the selected delivery. Set `preview_ready:true` only after the fixed preview passes media checks and the selected delivery succeeds. A hosted preview must be a verified direct MP3 link, never a ZIP. Publication already uses the saved bucket upload credentials; no repeat publish is required.

Automatic R2 setup uses an account ID and a setup token that expires within one day. The provisioner removes only a matching local credential copy. Do not claim that local removal revokes the provider token, and do not ask for revocation confirmation. Keep manual R2 setup and uncertain upload-token recovery available.

Include this complete skill with Article audio in the public template. Exclude owner state, credentials, private files, and temporary authoring instructions.
