# Article Audio

Turn a complete article into a narrated MP3 with Gemini TTS, then optionally host it on Cloudflare R2. Includes a portable CLI, an agent skill, and Grok Bot setup instructions. MIT licensed.

The Bot reads the article using its existing X or browser access and supplies a UTF-8 transcript. This package handles narration, resumable audio generation, credential storage, and delivery. It does not scrape X or summarize articles.

## Install in Grok Bot

Use the current public template linked from the [repository installation section](https://github.com/harrisrobin/article-audio#install-in-grok-bot), then send any message, even **hi**. The v0.1.4 native template is being refreshed; meanwhile, use the manual skill-install instructions below. If setup is incomplete, the Bot should invite you to set up Gemini and private R2 hosting.

The Bot downloads the pinned [v0.1.4 release](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.4) from GitHub onto its cloud computer and uses the [Article audio skill](skills/article-audio/SKILL.md). The readiness check happens on the first message of every conversation. Installation starts when you accept the setup invitation or explicitly request setup. No install-time hook is assumed. See the [installation instructions](template/INSTALL.md) for manual setup and fresh-install testing.

Hosted setup collects Gemini credentials and guides automatic Cloudflare bucket setup, then generates and uploads a sample to verify the listening link. The [Cloudflare plugin is optional](docs/cloudflare.md); its account login does not automatically supply this CLI's S3 credentials.

The package includes a [Bot profile](template/PROFILE.md) and instructions for creating your own template. A native public template is separate from searchable Marketplace catalog inclusion, which is not confirmed.

## Run locally

Requires macOS or Linux, Python 3.11+, and FFmpeg with ffprobe. Windows users can use Linux through WSL. Install FFmpeg with `brew install ffmpeg` on macOS, or `sudo apt-get update && sudo apt-get install -y ffmpeg` on Debian/Ubuntu.

From the source directory:

```bash
bash scripts/setup.sh
bash scripts/article-audio auth setup gemini
```

Setup creates a local Python environment from the lockfile. The second command prints a one-time local URL. Open it in a browser on the same computer, enter your [Gemini API key](https://aistudio.google.com/apikey), and submit. The form expires after ten minutes. For hidden terminal input, use `auth setup gemini --method terminal`.

Generate the included original sample:

```bash
bash scripts/article-audio plan examples/sample.txt
bash scripts/article-audio generate examples/sample.txt --title 'Room for your attention'
```

The JSON result contains `audio_path`, duration, actual model and voice, and cache status. Progress is emitted separately on stderr. Rerun the same command to resume completed segments after a failure or reuse an existing MP3.

Supplying a corrected title, author, or source URL updates the saved metadata even when audio is cached. Omitted metadata fields keep their previous values.

## Narration settings

Defaults: **Gemini 3.8 Flash TTS**, **Algenib**, restrained British delivery, **1.1× speed**, MP3 at **44.1 kHz / mono / 128 kbps**. FFmpeg changes speed while preserving pitch. The model controls the performance, so audition a short sample before processing a backlog.

```bash
bash scripts/article-audio generate /path/to/transcript.txt \
  --model gemini-3.8-flash-tts \
  --voice Algenib \
  --speed 1.1 \
  --title 'Article title' \
  --author 'Author' \
  --source-url 'https://x.com/example/article/123'
```

`--style-file /path/to/direction.txt` supplies voice direction separately from the narration. With Gemini 3.8, direction is sent in speech metadata; legacy models receive a labeled transcript and direction prompt. `models` lists TTS models available to your key; `generate --help` shows models this package supports. There is no silent model fallback.

Segments default to 3,000 characters, favoring paragraph and whitespace boundaries. `--chunk-chars` accepts 32–6,000. Exact text slices preserve the full transcript, but generated speech can still mispronounce or omit words; decoding success is not a transcript accuracy check. Separate requests can have audible changes in prosody. Smaller segments can help with provider limits but may create more joins.

A gross-truncation check rejects audio shorter than one second per 100 alphanumeric characters, applied only when at least 200 such characters are present. It checks new and cached WAVs plus the combined MP3, accounting for playback speed. This deliberately loose floor catches implausibly brief output, not ordinary omissions or silence; audition is still required. Invalid cached audio is regenerated on retry.

Inputs are capped at 1 MB and generation at 100 segments by default. Use `plan` before a long article and increase `--max-chunks` deliberately if needed. Duration is an estimate, not a price quote; Gemini usage is billed by your provider. Transient requests have at most three attempts, and an ambiguous timeout can still incur provider usage.

## Host on R2

Automatic setup needs your Cloudflare account ID and one short-lived setup token. Follow the [dashboard instructions and exact permissions](docs/cloudflare.md#create-the-setup-token): **Account > Workers R2 Storage > Edit** and **Account > Account API Tokens > Edit**, restricted to one account, expiring within one day. R2 must be activated; account token creation requires Super Administrator access.

```bash
bash scripts/article-audio auth setup cloudflare
bash scripts/article-audio auth provision-r2
bash scripts/article-audio publish /path/from/generate/audio.mp3
```

The form explains how to create the token. Provisioning creates a private bucket and saves a separate upload key restricted to it. After successful sample playback, revoke the setup token and remove any native secret/environment copy. The CLI removes its file copy, which does not revoke it at Cloudflare. Keep the upload token and repeat `publish` to confirm ongoing access.

Already have a bucket, need a specific jurisdiction, or prefer not to grant token-management access? Use the existing four-field fallback with `bash scripts/article-audio auth setup r2`. It collects the account ID, bucket name, and bucket-scoped S3 Access Key ID and Secret Access Key. [Manual steps and interrupted-setup recovery](docs/cloudflare.md).

The result includes `audio_url` and `expires_at`. Private signed links last **seven days** by default; `--expires` accepts 1–604800 seconds. Anyone holding the link can listen until it expires. Run `publish` again to renew it; matching uploads are reused. Signed links are returned, not saved in manifests.

For jurisdictional buckets, use `--jurisdiction eu`, `us`, or `fedramp`, or set `R2_JURISDICTION`. Ordinary buckets use `default`. [Setup and plugin details](docs/cloudflare.md).

For a permanent public URL, configure an R2 public custom domain first, then explicitly use:

```bash
bash scripts/article-audio publish /path/to/audio.mp3 \
  --public-base-url https://audio.example.com
```

This flag does not configure DNS or change bucket permissions. Public recordings are accessible to anyone. A signed URL also does not make an already-public bucket private. Both delivery modes verify metadata, object bytes, and a ranged request to the actual listening URL before reporting success.

## Credentials and saved work

Run `auth status` for credential presence and `doctor` for dependencies. Neither prints secret values. Gemini credentials are needed only for narration; R2 credentials are needed only for uploads.

Grok Bot's supported native secure handoff is preferred when it can inject an environment or stdin stream. `auth import-env gemini`, `auth import-env r2`, and `auth import-json` support those handoffs. If native handoff is unavailable, the local password form runs in the Bot's Agent Computer browser. **Generic native-form compatibility is not verified.** See the [credential setup contract](docs/credential-setup.md).

Defaults are `~/.config/article-audio` for credentials and `~/.local/share/article-audio/jobs` for recordings, respecting `XDG_CONFIG_HOME` and `XDG_DATA_HOME`. Override them with `ARTICLE_AUDIO_CONFIG_DIR` and `ARTICLE_AUDIO_DATA_DIR`. Grok installations use `/workspace/.article-audio-config` and `/workspace/.article-audio-jobs`. Keep these paths consistent across calls and outside the checkout.

The credential file is **plaintext**, protected by mode 0600 inside a mode 0700 directory. Other processes and Bots running as the same OS user can read it. Environment variables override saved credentials. Re-run setup to rotate saved values. Never put keys into ordinary chat, source files, command arguments, or a shared template. [Security and privacy details](SECURITY.md).

## Develop and distribute

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run python -m pytest -q
uv build
python3 scripts/package.py
```

The source ZIP in `dist/` contains code, locked dependencies, skill, template instructions, and tests. ZIP, source distribution, and wheel share an explicit file allowlist in `pyproject.toml`; adding a new release file requires listing it there. Stray files under `docs`, `examples`, or the package directory are excluded. Review listed files for secrets before releasing: an allowlist cannot detect private text inserted into an approved source file. The Python wheel installs the CLI; use the source ZIP for the complete Bot installation materials.

Tests cover secure collection, redaction, provider errors, exact input coverage, resumability, concurrency, real FFmpeg encoding, and mocked R2 delivery. See [verification evidence and remaining runtime checks](docs/verification.md). The CI workflow is included; a local test run is not a hosted CI result.

## References

[Gemini speech generation](https://ai.google.dev/gemini-api/docs/speech-generation), [R2 with boto3](https://developers.cloudflare.com/r2/examples/aws/boto3/), [Grok security](https://docs.x.ai/grok-bot/approvals-security-and-privacy), and [Grok templates](https://docs.x.ai/grok-bot/bots).

Inspired by [Steve Ruiz's article narration](https://x.com/steveruizok/status/2101406564582138346) and [Mouad Mabrouk's recreation](https://x.com/mmabrouk_/status/2101669633161916628). The sample text is original and does not redistribute their source article or audio.
