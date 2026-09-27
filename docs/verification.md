# Verification

Local evidence from 2026-09-27. This distinguishes implemented behavior from integrations that still need a real account test.

## Confirmed locally

- 50 automated tests passed after adversarial review, including actual FFmpeg encoding and real loopback submissions of Gemini and R2 forms with dummy credentials.
- Ruff lint and formatting checks passed; Bash scripts passed syntax checks.
- The supplied test Gemini key successfully listed TTS models and generated three segments using `gemini-3.8-flash-tts` with Algenib.
- The original sample produced 52.810 seconds of MP3 audio, 44.1 kHz, mono, 128 kbps. FFmpeg decoded the complete file without errors.
- Repeating the same generation returned `cached: true`. Tests separately prove completed segments survive a failed run and concurrent work on the same job is rejected.
- R2 tests exercise content-addressed uploads, upload reuse, ranged reads, public delivery, signed delivery, managed-upload errors, and refusal to report success for an inaccessible link. These use mocked network boundaries.

## Distribution checks

- The source ZIP installed in a fresh temporary directory with no preinstalled `uv`. The setup script bootstrapped its pinned `uv`, installed the locked dependencies, and passed `doctor` and an offline sample `plan`.
- The command wrapper worked from outside the extracted source directory.
- The Python wheel and source distribution built successfully. The full source ZIP includes the skill and template materials.
- Source and each archive were checked for the actual test key, private job data, virtual environments, and recordings; none were included.
- The skill creator's validator accepted `skills/article-audio/SKILL.md`.
- Local tests ran on macOS with Python 3.14.3 and Python 3.11. The Linux CI matrix targets Python 3.11 and 3.13; GitHub has not executed it because of the account billing lock described below.

## Adversarial review changes in 0.1.1

The [two-axis review](review.md) records findings and their disposition. Regression coverage now includes damaged-credential recovery, metadata correction without new narration, grossly short fresh and cached audio, all R2 jurisdiction endpoints, and injected private files excluded from ZIP, source distribution, and wheel builds. The hosted setup instructions collect both providers before the sample upload test.

Version 0.1.1 was extracted into a fresh temporary directory and installed successfully. Its wrapper, offline plan, and private stdin import passed; rerunning setup retained both providers' dummy credentials outside the source directory. The wheel was installed independently and returned version 0.1.1. The final ZIP's contents matched the exact release list, and its SHA-256 matched the checksum file. Both review agents reported no remaining findings after the fixes.

## Still requires runtime testing

Version 0.1.2 adds pinned GitHub bootstrap instructions and first-request setup. Its release checks include consistency between installation tags, archive names, lockfile, and runtime version. The public template must additionally retain the full release commit SHA.

- First-use runtime installation in an imported Grok Bot and persistence across a new Bot chat. Template creation itself is verified below.
- The installed Grok runtime's native secure credential handoff. No general third-party secret-request API is assumed.
- A user entering credentials in the fallback form through Grok's Agent Computer browser.
- Real R2 upload, bucket permissions, expiring-link playback/seek, and any public custom domain. No R2 credentials were supplied for the local build.
- Human review of the voice, segment joins, and fidelity on a complete X Article. Valid MP3 decoding does not prove narration accuracy.
- Hosted GitHub Actions. The published workflow is blocked before starting jobs by an account billing lock; no hosted test result is available.

The local audition is kept outside the release archive. Credentials used for the live Gemini test are temporary and are not part of the project or distribution.

## First public release

[Version 0.1.2](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.2) was published from commit `fbdb6821f3eb7af7cde70d1ca86dd4ee67fd8b70`. The final local suite passed 51 tests. Lint, formatting, skill validation, and source/wheel builds passed. A clean source-archive installation passed doctor and an offline sample plan. Anonymous downloads of the published ZIP and skill succeeded; every ZIP file matched its source at the release commit.

Source ZIP SHA-256: `3a1a63239c8c84bbb2cee5ca5878b484e3bac42c395379ef6a626eb786ed8ed1`.

[GitHub run 36317827409](https://github.com/harrisrobin/article-audio/actions/runs/36317827409) created jobs for Python 3.11 and 3.13 but started no steps. GitHub's annotation says: "The job was not started because your account is locked due to a billing issue." This is not a failing test and is not a passing CI result. The account owner must resolve the lock before rerunning it.

## Published Grok Bot template

[Article Audio](https://x.ai/bot/u9M4WdBafSgCyS3GNHKla) is published as a public native template. Grok fetched the public skill, saved it through its skill system, and created the template. Native inspection confirmed the complete registered narration/bootstrap skill and the shared template's exact commit, ZIP checksum, first-use setup rule, X-access guidance, Article audio skill, and getting-started skill. No unrelated skills or routines appeared in the shared configuration. The public preview loaded without authentication and displayed Article Audio with the app-opening link.

The template-authoring Bot did not install the runtime or configure credentials, preserving the user's planned first-use test. Public template publication does not establish searchable Marketplace catalog inclusion. The main branch now links to the template; the pinned v0.1.2 assets remain unchanged.
