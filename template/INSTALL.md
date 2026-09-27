# Install in Grok Bot and create a template

Source: [harrisrobin/article-audio](https://github.com/harrisrobin/article-audio). Pinned release: [v0.1.4](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.4).

## Use an imported Bot

Open the [Article Audio template](https://x.ai/bot/u9M4WdBafSgCyS3GNHKla), choose **Add to Grok Bot**, then send any message:

> Hi

If setup is incomplete, the Bot should offer guided setup in its first reply. Accept that invitation to begin. You can also request setup directly, without a second confirmation.

The Bot downloads the pinned GitHub release to its cloud computer and installs its own dependencies. It collects missing credentials through a supported secure handoff or its local password form. You do not need to copy scripts manually. Adding the Bot does not itself execute an installation hook.

For local-only audio, say “Set yourself up with Gemini only.” This means MP3 files on the Bot's cloud computer, not your laptop.

## Create the public template

Create a dedicated Article Audio Bot. Set its description from [PROFILE.md](PROFILE.md). Send this preparation prompt after publishing the release:

> Prepare this Bot as the public Article Audio template. Read https://raw.githubusercontent.com/harrisrobin/article-audio/v0.1.4/skills/article-audio/SKILL.md and register its complete contents as the Article audio skill. Also read skills/article-audio-onboarding/SKILL.md at the same release and register it as Article Audio onboarding, replacing any older generated getting-started skill in the template. Save https://github.com/harrisrobin/article-audio.git and release v0.1.4 as the installation source. Resolve and remember the full release commit SHA so a future install can verify it. Preserve the skill's first-use GitHub installation, runtime checks, separate configuration paths, and Gemini plus private R2 onboarding. Default to automatic bucket provisioning with an account ID and short-lived Cloudflare token, showing the documented dashboard steps and both exact permissions before secret entry. Retain the manual four-field R2 fallback. The imported Bot must check readiness on the first message of every conversation, including greetings or unrelated questions, and prompt for setup when incomplete. An explicit setup request starts setup immediately; a refusal suppresses repeated invitations in that conversation. For this template-authoring task, only register the instructions: do not install the runtime, request credentials, synthesize audio, or upload anything. Include no account-specific credentials, private files, signed links, or unrelated memories. Confirm the saved skill is available before stopping.

Then choose **Share → Create template → Public link**. Inspect the generated template details. It must carry both complete skills, the public source and pinned revision, and the first-use rule. A statement that files are already installed on the author's computer is not a portable setup. Creating a public template is not documented as automatically listing it in the searchable Marketplace.

## Validate a fresh import

Test on a fresh account/computer or a deliberately isolated test environment. Bots on the same account share files, browser sessions, credentials, and plugins; importing a second Bot alone is not a clean-install test.

First send only "hi" and verify that the reply offers setup without collecting keys in chat. Accept, then verify download, dependency installation, both credential forms, sample generation, private R2 upload, playback/seek, repeated-request reuse, and operation after a new chat. Preserve configuration at `/workspace/.article-audio-config` and recordings at `/workspace/.article-audio-jobs`, outside the source checkout. Native credential handoff and live R2 still require this runtime test.

## Install without a template

Give an existing Bot the public skill URL above and ask it to save the skill and set up Article Audio. The skill contains the actual Git clone command and prerequisite checks. For a manual checkout:

```bash
git clone --branch v0.1.4 --depth 1 https://github.com/harrisrobin/article-audio.git article-audio
cd article-audio
bash scripts/setup.sh
```

Release assets also include `article-audio-0.1.4.zip` and its SHA-256 file. Verify the checksum and reject archive paths escaping the extraction destination. An archive contains one top-level `article-audio/` directory. Preserve existing source changes and saved credentials when upgrading.

[Official template documentation](https://docs.x.ai/grok-bot/bots) and [cloud computer behavior](https://docs.x.ai/grok-bot/computer-and-apps).
