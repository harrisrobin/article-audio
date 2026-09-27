# Portable article audio

Build locally and transfer a versioned package to Grok Bot. The Bot already reads X Articles, so it supplies a complete UTF-8 transcript. The CLI does not scrape X or rewrite the article.

Python 3.11+ runs on macOS and Linux. A small HTTP client calls Gemini. FFmpeg encodes MP3. boto3 uploads to R2. Default model is gemini-3.8-flash-tts, voice Algenib, speed 1.1; model and voice are explicit options. Local generation works without R2 credentials.

Secrets come from environment injection or a user-owned credentials file outside the repository. A native Grok secure request is preferred when its runtime supports delivery to a file or environment. No public arbitrary-secret API was found, so the package must not claim a native integration is verified. A one-time loopback password form and hidden terminal input provide an executable fallback. Files use mode 0600 in a directory with mode 0700, with atomic writes and no value-bearing status output. Storage is not encryption and is accessible to other processes running as the same user.

Generation splits exact transcript slices with a conservative character cap. Each job is content-addressed by transcript and all generation settings, locked against concurrent duplicate work, and resumes validated completed segments. Output is not marked complete after truncation, empty audio, or decoding errors. Gemini failures use bounded retries for transient statuses; authentication and unsupported-model failures stop immediately. No silent model fallback.

R2 publishing is explicit and separate from synthesis. Private signed links are the default. Public URLs require explicit configuration. Cache keys include content and settings. Upload metadata, length and a ranged GET must pass before returning success. Presigned links are returned to the user but not persisted in job manifests.

The open-source distribution includes source, tests, a lockfile, a setup script, an agent skill, a template profile, and a license. It contains no API keys or user's article content. The shareable Grok template is created inside Grok after runtime validation; this repository supplies its portable ingredients.
