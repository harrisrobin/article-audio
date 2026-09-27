---
name: article-audio-onboarding
description: Check Article Audio readiness on the first user message of every conversation, including greetings and unrelated questions. Prompt an unconfigured user to begin setup; resume incomplete setup without asking for saved keys again.
---

# Article Audio onboarding

Run before the first normal reply in every conversation. Any user message triggers this check, including "hi", "what can you do?", an unrelated question, or an article URL. The user never needs to know a setup command.

## Check readiness

Use evidence from the current owner's cloud computer. A published template, the author's successful setup, copied memories, or a new Bot name does not establish readiness. Use `/workspace/.article-audio-config` and `/workspace/.article-audio-jobs` for configuration and recordings, outside the source checkout.

Read the nonsecret setup record at `/workspace/.article-audio-config/onboarding.json`. Its schema is `{"schema":1,"delivery_mode":"private-r2","sample_verified":false}`; `delivery_mode` also accepts `local-only`. A missing or invalid record means setup has not been verified here. Never infer local-only mode merely from missing R2 credentials.

If the CLI is absent, setup is needed. If installed, use its `doctor` and `auth status` commands with those configuration paths. Read only dependency and credential-presence results, never credential files or values. Ready means dependencies available, `sample_verified` true in the current computer's record, and credentials present for the recorded mode. Gemini is sufficient for local-only mode; private hosted audio also needs R2. Missing dependencies require repair; saved credentials should be reused.

## Respond to the first message

- If ready, answer the user's request without another setup pitch. Readiness checks do not themselves synthesize audio or incur provider usage.
- If setup is needed and the user has not already requested setup, give one brief setup invitation: "Before I can narrate articles, let's set up Gemini and private audio links. I'll guide you through secure credential entry. Ready to start?" Offer local-only audio if the user prefers it. For an article request, acknowledge the article and retain it for after setup. A brief answer to a general question can accompany the invitation.
- If the user already asked to set up, or accepts the invitation, record the chosen delivery mode and use the Article audio skill immediately. Default to private R2 hosting unless they choose local-only. Install or repair the pinned package, collect only missing credentials, then generate and verify the sample for the selected mode. Do not ask for setup permission twice.
- If the user declines or says later, continue answering questions and do not repeat the invitation in that conversation. Resume when they request setup or narration again.

Default hosted setup creates a private Cloudflare bucket using an account ID and a short-lived setup token. The Article audio skill supplies the permission instructions and manual four-field R2 fallback. Reuse complete R2 credentials without provisioning again. Credential entry uses a supported native secret handoff or the package's Agent Computer password form, one provider at a time. Never request API keys in ordinary chat. Report partial setup precisely. Hosted setup is complete only after a generated sample has a verified private listening link; local-only setup requires a working sample MP3.

## Preserve setup choices

The agent maintains `onboarding.json`; the CLI does not create it. On first accepted setup or a mode change, atomically write the schema above with the selected mode and `sample_verified:false`. After successful sample verification, set `sample_verified:true`. Preserve an existing record while merely checking readiness. Keep the directory mode 0700 and the record mode 0600. Store no keys, signed links, article content, or owner identity in it. This durable record distinguishes completed local-only setup from interrupted hosted setup across conversations. Keep it outside exports and source archives.

## Sharing

Include this complete skill alongside Article audio in the public template. Keep the any-message trigger in the Bot description and shared first-use rule, so this skill is reached even for a greeting. Exclude any owner's readiness, saved credential state, deferral choices, private files, or temporary authoring restrictions from the template.
