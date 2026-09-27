# Install in Grok Bot and create a template

Source: [harrisrobin/article-audio](https://github.com/harrisrobin/article-audio). Pinned release: [v0.1.7](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.7).

## Use an imported Bot

Open the [current Article Audio template linked in the repository](https://github.com/harrisrobin/article-audio#install-in-grok-bot), choose **Add to Grok Bot**, then send any message:

> Hi

If setup is incomplete, the Bot should offer guided setup in its first reply. Accept that invitation to begin. You can also request setup directly, without a second confirmation.

The Bot downloads the pinned GitHub release to its cloud computer and installs its own dependencies. It collects missing credentials through a supported secure handoff or its local password form. You do not need to copy scripts manually. Adding the Bot does not itself execute an installation hook.

For local-only audio, say “Set yourself up with Gemini only.” This means MP3 files on the Bot's cloud computer, not your laptop.

## Create the public template

Create a dedicated Article Audio Bot. Set its description from [PROFILE.md](PROFILE.md). Send this preparation prompt after publishing the release:

> Prepare this Bot as the public Article Audio template. Read https://raw.githubusercontent.com/harrisrobin/article-audio/v0.1.7/skills/article-audio/SKILL.md and register its complete contents as the Article audio skill. Also read skills/article-audio-onboarding/SKILL.md at the same release and register it as Article Audio onboarding, replacing any older generated getting-started skill in the template. Save https://github.com/harrisrobin/article-audio.git and release v0.1.7 as the installation source. Resolve and remember the full release commit SHA so a future install can verify it. Preserve the profile's ONLY job and Anti-jobs blocks, first-use installation, runtime checks, separate configuration paths, and Gemini audition before hosting. Confirm voice, speed, and delivery once after playback; private hosting is the default, with public access only on an explicit owner request. Follow the dedicated-bucket and public-address setup rules and persist a verified public base URL for that mode. Persist preferences privately and pass them explicitly to each CLI invocation. Preserve partial setup and collect only missing keys. Default to automatic bucket provisioning with an account ID and short-lived Cloudflare token, showing the documented dashboard steps and both exact permissions before secret entry. Retain the manual four-field R2 fallback. The imported Bot must check readiness on the first message of every conversation, including greetings or unrelated questions, and prompt for setup when incomplete. An explicit setup request starts setup immediately; a refusal suppresses repeated invitations in that conversation. For this template-authoring task, only register the instructions: do not install the runtime, request credentials, synthesize audio, or upload anything. Include no account-specific credentials, private files, signed links, or unrelated memories. Confirm the saved skill is available before stopping.

Then choose **Share → Create template → Public link**. Inspect the generated template details. It must carry both complete skills, the public source and pinned revision, and the first-use rule. A statement that files are already installed on the author's computer is not a portable setup. Creating a public template is not documented as automatically listing it in the searchable Marketplace.

Use **Article Audio** as the Bot and template display name and **Article narrator** as its label. Verify any editable store display metadata too; do not rewrite opaque internal IDs or unrelated records just because they contain an old creation label. Keep exactly `article-audio` and `article-audio-onboarding`. Retire the legacy Article Audio getting-started skill from this Bot and template; leave other Bots' generic onboarding skills alone. Exclude owner preferences, setup records, and credentials from the snapshot.

## Update the existing public template

For later releases, keep the template-authoring Bot and update its profile, both complete skills, pinned release commit, and ZIP checksum using the preparation steps above. Open its **Share > Update template** action and review the proposed shared configuration. In the staged **Context > Instructions**, verify the complete PROFILE body, not just a short description. Open each skill and check its actual content through the final paragraph. Shared fields must contain literal source text. The share tool does not load a file from a `FILE:/path` marker, code expression, or a statement that a skill is installed. Reject placeholders and shortened bodies before publishing.

Publish the reviewed update and confirm that **Copy link** still returns the existing public URL. Reload that URL and check the full profile through its final paragraph. The public preview does not prove the shared skill bodies are complete; inspect those in the native review. Do not choose Create template or create another authoring Bot for a normal release.

Editing a local Bot or pushing GitHub commits alone does not update a published template snapshot. Imported Bots are copies; do not assume they automatically receive new instructions. Keep credentials, setup completion records, and temporary authoring restrictions out of every update. **Delete Template** is a separate share-menu action, not part of releasing an update.

The earlier public ID `u9M4WdBafSgCyS3GNHKla` is deprecated. The current template is `zBuR546KeAs5X0iwlXkxt`; do not offer the older link as an installation option. Its authoring Bot was already deleted and no supported removal path has been found, so repository deprecation does not mean that old URL has been disabled.

## Validate a fresh import

Test on a fresh account/computer or a deliberately isolated test environment. Bots on the same account share files, browser sessions, credentials, and plugins; importing a second Bot alone is not a clean-install test.

Follow [the runtime acceptance test](../docs/runtime-test.md): greeting, installation, secure credential handoff, audition and saved preferences, playback/seek in the selected R2 mode, setup-token revocation, repeat publish, and a new conversation without repeated setup. Preserve configuration at `/workspace/.article-audio-config` and recordings at `/workspace/.article-audio-jobs`, outside the source checkout. Report shared-state reuse as recovery evidence rather than a clean import.

## Install without a template

Give an existing Bot the public skill URL above and ask it to save the skill and set up Article Audio. The skill contains the actual Git clone command and prerequisite checks. For a manual checkout:

```bash
git clone --branch v0.1.7 --depth 1 https://github.com/harrisrobin/article-audio.git article-audio
cd article-audio
bash scripts/setup.sh
```

Release assets also include `article-audio-0.1.7.zip` and its SHA-256 file. Verify the checksum and reject archive paths escaping the extraction destination. An archive contains one top-level `article-audio/` directory. Preserve existing source changes and saved credentials when upgrading.

[Official template documentation](https://docs.x.ai/grok-bot/bots) and [cloud computer behavior](https://docs.x.ai/grok-bot/computer-and-apps).
