# Install in Grok Bot and create a template

Source: [harrisrobin/article-audio](https://github.com/harrisrobin/article-audio). Pinned release: [v0.2.0](https://github.com/harrisrobin/article-audio/releases/tag/v0.2.0).

## Use an imported Bot

Open the [current Article Audio template linked in the repository](https://github.com/harrisrobin/article-audio#install-in-grok-bot), choose **Add to Grok Bot**, then send any message:

> Hi

If setup is incomplete, the Bot should offer guided setup in its first reply. Accept that invitation to begin. You can also request setup directly, without a second confirmation.

The Bot downloads the pinned GitHub release to its cloud computer and installs its own dependencies. It collects missing credentials through a supported secure handoff or its local password form. You do not need to copy scripts manually. Adding the Bot does not itself execute an installation hook.

For local-only audio, say “Set yourself up with Gemini only.” This skips R2. The Bot still needs a supported way to deliver the MP3, possibly for playback in another app. If it cannot deliver the file, it must explain the limitation and leave preview readiness incomplete.

## Create the public template

Create a dedicated Article Audio Bot. After publishing the package, [compile and upload its template bundle](../docs/template-bundles.md). The bundle contains the literal profile, both complete skills, four public memories, exact release commit, and source ZIP checksum. It reads only the verified release archive.

Send this preparation prompt with the bundle's release asset URL:

> Prepare this Bot from the published Article Audio template bundle and its matching SHA-256 sidecar. Verify the bundle checksum before using it. Use its complete profile text, both complete skill texts, and all four shared memories literally. Split memories longer than Grok's 500-character limit into consecutive sentence-boundary parts, each at most 500 characters, without changing any words. Preserve the original separators so each memory can be reconstructed exactly. Preserve its display metadata and exact release provenance. Do not summarize bodies or insert file-path placeholders. Replace the obsolete Article Audio getting-started skill with Article Audio onboarding. For this template-authoring task, only register the public instructions: do not install the runtime, collect credentials, synthesize audio, or upload recordings. Exclude all owner configuration, private content, unrelated skills, and temporary authoring restrictions from the shared snapshot. Read back the saved profile, skills, and every memory part; compare their complete text with the bundle, reconstructing split memories before checking their hashes. A source hash alone does not prove the host saved the complete text. Stop before publication if a host field truncates content.

Then choose **Share → Create template → Public link**. Inspect the generated template details. It must carry both complete skills, the public source and pinned revision, and the first-use rule. A statement that files are already installed on the author's computer is not a portable setup. Creating a public template is not documented as automatically listing it in the searchable Marketplace.

Use **Article Audio** as the Bot and template display name and **Article narrator** as its label. Verify any editable store display metadata too; do not rewrite opaque internal IDs or unrelated records just because they contain an old creation label. Keep exactly `article-audio` and `article-audio-onboarding`. Retire the legacy Article Audio getting-started skill from this Bot and template; leave other Bots' generic onboarding skills alone. Exclude owner preferences, setup records, and credentials from the snapshot.

## Update the existing public template

For later releases, keep the same template-authoring Bot. Compile a bundle from the new published release. Update the profile, both complete skills, public memories, pinned release commit, and ZIP checksum from that bundle. Open its **Share > Update template** action and review the proposed shared configuration. In the staged **Context > Instructions**, verify the complete PROFILE body, not just a short description. Open each skill and check its actual content through the final paragraph. Shared fields must contain literal source text. The share tool does not load a file from a `FILE:/path` marker, code expression, or a statement that a skill is installed. Reject placeholders and shortened bodies before publishing.

Open each shared memory's detail view too. Grok truncates facts longer than 500 characters. Follow [the native memory packing steps](../docs/template-bundles.md#fit-memories-into-native-fields): split long memories at sentence boundaries, preserve every word, then reconstruct and hash the saved parts against the bundle. The four canonical memories may require more than four native facts. A complete skill does not prove its companion memories are complete. If a native field truncates text, correct the staged payload or stop; do not publish the shortened memory or treat the bundle's source hash as saved-content verification.

Publish the reviewed update and confirm that **Copy link** still returns the existing public URL. Reload that URL and check the full profile through its final paragraph. The public preview does not prove the shared skill bodies are complete; inspect those in the native review. Do not choose Create template or create another authoring Bot for a normal release.

Editing a local Bot or pushing GitHub commits alone does not update a published template snapshot. Imported Bots are copies; do not assume they automatically receive new instructions. Keep credentials, setup completion records, and temporary authoring restrictions out of every update. **Delete Template** is a separate share-menu action, not part of releasing an update.

The earlier public ID `u9M4WdBafSgCyS3GNHKla` is deprecated. The current template is `zBuR546KeAs5X0iwlXkxt`; do not offer the older link as an installation option. Its authoring Bot was already deleted and no supported removal path has been found, so repository deprecation does not mean that old URL has been disabled.

## Validate a fresh import

Test on a fresh account/computer or a deliberately isolated test environment. Bots on the same account share files, browser sessions, credentials, and plugins; importing a second Bot alone is not a clean-install test.

Follow [the runtime acceptance test](../docs/runtime-test.md): greeting, installation, secure credential handoff, a fixed-voice MP3 preview in the selected delivery mode, automatic readiness, and a new conversation without repeated setup or confirmation prompts. Preserve configuration at `/workspace/.article-audio-config` and recordings at `/workspace/.article-audio-jobs`, outside the source checkout. Report shared-state reuse as recovery evidence rather than a clean import.

## Install without a template

Give an existing Bot the [published Article audio skill](https://raw.githubusercontent.com/harrisrobin/article-audio/v0.2.0/skills/article-audio/SKILL.md) and [onboarding skill](https://raw.githubusercontent.com/harrisrobin/article-audio/v0.2.0/skills/article-audio-onboarding/SKILL.md), and ask it to save both skills and set up Article Audio. The skills contain the Git clone command, prerequisite checks, and first-message setup flow. For a manual checkout:

```bash
git clone --branch v0.2.0 --depth 1 https://github.com/harrisrobin/article-audio.git article-audio
cd article-audio
bash scripts/setup.sh
```

Release assets also include `article-audio-0.2.0.zip` and its SHA-256 file. Verify the checksum and reject archive paths escaping the extraction destination. An archive contains one top-level `article-audio/` directory. Preserve existing source changes and saved credentials when upgrading.

[Official template documentation](https://docs.x.ai/grok-bot/bots) and [cloud computer behavior](https://docs.x.ai/grok-bot/computer-and-apps).
