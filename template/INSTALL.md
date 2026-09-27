# Install in Grok Bot and create a template

This directory is a profile and installation contract, not a proprietary Grok template file. The native share link must be created in Grok Bot after a working Bot is configured.

## Try the local build before publication

Run `python3 scripts/package.py` to produce `dist/article-audio-0.1.0.zip` and its SHA-256 file. Transfer the archive using an attachment if your Grok client supports it, or put it at a download location that the Bot can reach. Source-code attachments are supported; archive handling can vary by client. A GitHub repository or release asset is the simplest repeatable route once published.

Tell your Bot:

> Install the Article Audio package I supplied into /workspace/article-audio. Inspect the archive and run bash scripts/setup.sh. Read skills/article-audio/SKILL.md and docs/credential-setup.md. Save the skill as Article audio. Use /workspace/.article-audio-config for credentials and /workspace/.article-audio-jobs for recordings, outside the repository. Guide me through missing credentials with the supported secure handoff or the local form. Generate examples/sample.txt, then test a full article I provide. Do not upload anything publicly.

An archive should contain one top-level `article-audio/` directory. When extracting any downloaded archive, check for paths escaping the destination. Keep the supplied release checksum for verification. For a Git repository, check out the selected tag or commit rather than tracking a changing branch on every invocation.

## Create the shareable template

1. Use PROFILE.md as the Bot's role description and save or attach the Article audio skill.
2. Give the template a real public repository/release URL and pinned tag or commit after the source is published. This package intentionally does not invent a GitHub owner or publish the project automatically.
3. Include the credential-setup reference, or preserve the skill's instructions to load it from the installed package. The setup source must be reachable before any credentials are requested.
4. In Grok Bot, choose Share, then Create template. Inspect the template details before sharing it.
5. Test the template on a fresh account or installation with no script or credentials present. Verify first-run install, credential collection, generation, R2 upload, playback/seek, repeat-run caching, and continued operation after opening a new chat.

Template sharing copies configuration, skills, and routines. It does not clone the source machine or transfer logins. All Bots on the same account share one computer, so duplicating a Bot on your own account does not prove a clean installation. [Official template documentation](https://docs.x.ai/grok-bot/bots).
