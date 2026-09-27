# Grok Bot publication and self-setup research

Research date: 2026-09-27. Sources are first-party xAI/SpaceXAI and Cursor pages.

## Decision

Publish **Article Audio first as a public Bot template**. That is the only documented self-service Bot-sharing route: in Grok Bot choose **Share → Create template → Public link**, then recipients open the preview and choose **Add to Grok Bot**. A public template is not documented as automatically becoming an indexed listing on the public [Grok Bot Marketplace](https://x.ai/bot/marketplace).

Treat an indexed Marketplace listing as a separate, currently undocumented publication step. The public Marketplace and individual indexed Bot pages exist, but the official sources reviewed do not expose a submit form, eligibility rules, review criteria, or a documented route from a template link to indexing.

## Verified

### Public template sharing

- A template carries the Bot's identity, description, skills, and routines. It does **not** carry the creator's computer, logins, conversation history, or files. Adding it creates a copy on the recipient's account. [Create and manage Bots](https://docs.x.ai/grok-bot/bots#share-a-bot)
- Anyone with a public link can view and install the full shared configuration. The creator must remove secrets, private URLs, customer data, and other confidential material. [Third-party bot terms](https://x.ai/legal/bot-sharing-terms)
- Team admins can disable public template sharing. Enterprise teams default to public sharing off; other teams default to allowing it. [Grok Bot for teams and enterprises](https://docs.x.ai/grok-bot/teams-and-enterprises#public-template-sharing)
- Grok Bot access currently requires a paid individual Cursor plan, Cursor Teams, or a linked eligible individual SuperGrok subscription. The desktop app is required to finish adding a shared Bot. [Get started](https://docs.x.ai/grok-bot/get-started)

### Marketplace discovery is a distinct surface

- The public [Grok Bot Marketplace](https://x.ai/bot/marketplace) is an indexed catalog with search, categories, featured entries, creator names, stable detail URLs, and **Add/Import Bot** actions.
- An indexed Bot's detail page can expose its memories, skills, routines, and integrations. Its Import Bot action resolves to the same kind of `x.ai/bot/...` install preview used by shared Bots. Example: [dr eggbot](https://x.ai/bot/marketplace/bots/dr-eggbot-v2).
- Neither the Bot-sharing docs nor the public Marketplace page says that creating a public template submits, reviews, or indexes it. No official Bot Marketplace submission form or publication guide was found.

### What the installed Bot can do

- Each account has one persistent cloud computer with a browser, command line, and filesystem. Durable project files belong under `/workspace`; all Bots on that account see the same files, cookies, sessions, and command-line credentials. [Use the computer and apps](https://docs.x.ai/grok-bot/computer-and-apps)
- A skill is reusable instructions containing steps, inputs/access requirements, validation, outputs, and approval boundaries. Shared templates include skills. [Skills and routines](https://docs.x.ai/grok-bot/skills-routines-and-automations)
- Marketplace Bots already use first-run instructions in shared configuration. For example, the indexed [dr eggbot](https://x.ai/bot/marketplace/bots/dr-eggbot-v2) says, “On first run after import, run /setup-pstack...” This verifies that first-run bootstrap instructions are an existing Marketplace design pattern.
- The indexed [last30days Bot](https://x.ai/bot/marketplace/bots/last30days) explicitly installs its skill from a public GitHub repository, registers the skill with Grok Bot, and guides first-run setup. Its published configuration names the installation command, Python requirement, and credential-preservation rules. This is direct precedent for GitHub-based self-setup, though it does not establish an install-time execution hook.
- Files under `/workspace` are durable, but manually installed packages are replaceable during computer updates or recovery. An existing checkout or version marker alone is not evidence that the runtime still works. [Use the computer and apps](https://docs.x.ai/grok-bot/computer-and-apps#work-with-files)

### Cursor plugins are a different publication unit

- Cursor's Marketplace accepts a **public Git repository** containing an Agent Plugin (`plugin.json`), Cursor Plugin (`.cursor-plugin/plugin.json`), or multi-plugin marketplace manifest. Submission is through [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish); official plugins are manually reviewed. [Plugin reference](https://cursor.com/docs/reference/plugins), [Plugins](https://cursor.com/docs/plugins)
- Grok Bot users install supported plugins from the in-app Marketplace and authorize them separately. Installs are account-wide. [Connect plugins](https://cursor.com/help/grok-bot/connect-plugins)
- This does not document Bot-template publication or Grok Bot Marketplace indexing. Cursor's broader plugin catalog includes editor-oriented components, so universal Grok Bot compatibility is not documented.

## Inferred implementation design

The portable Bot can bootstrap Article Audio on the **first user message**, rather than at install time:

1. Include the self-contained Article audio skill and a first-run rule in the shared template.
2. When the user first asks it to start, check the installed revision, Python environment, FFmpeg, and the CLI's `doctor` result. Keep configuration and recordings outside the checkout.
3. If source is missing, clone/download the public GitHub repository into `/workspace/article-audio` at the exact commit supplied by the template. Verify a release archive's checksum before extracting it. Never overwrite local changes or an unrelated existing directory.
4. Run the repository's idempotent setup script when needed. Install missing system prerequisites through the cloud computer's supported mechanism, then verify the runtime. Do not treat a version marker as sufficient after computer recovery.
5. Ask for missing Gemini and R2 credentials through a supported secure handoff or the package's password form, one provider at a time. Never collect them in chat or put them in the public template.
6. Generate the sample, upload it privately, and verify playback before declaring setup complete. On later requests, reuse working installations and saved credentials.

This design is consistent with documented template contents, skills, terminal/filesystem access, and Marketplace first-run patterns. It still needs a native end-to-end test because the docs do not promise that imported first-run instructions will execute automatically or that every shell/network operation will pass approval and network policy.

## Unknown or unverified

- **Indexed Bot publication:** no documented submit route, eligibility threshold, review process, acceptance criteria, category selection flow, or SLA was found for `x.ai/bot/marketplace`.
- **Template-to-index behavior:** no official source says a public template is automatically discoverable or considered for Marketplace indexing.
- **Install-time hooks:** no Bot-template manifest, lifecycle event, post-install hook, or automatic install-time code execution is documented. Assume no code runs until the user messages the Bot.
- **First-message guarantee:** profile/skill instructions can tell the Bot to bootstrap, and the cloud computer can run commands, but automatic obedience on the first message is an implementation pattern rather than a documented lifecycle guarantee.
- **Native Marketplace UI:** an account-specific or staged catalog submission control may exist without public documentation.

## Clean-install caveat

Installing a second copy on the same account is **not a clean-install test**. All Bots on that account share the same `/workspace`, browser state, sign-ins, command-line credentials, and installed account-wide plugins. Test idempotency on the normal account, but test a genuinely fresh install with a separate Cursor user/computer or a deliberately reset test environment. Do not infer cleanliness from a new Bot conversation or a duplicated/imported Bot.
