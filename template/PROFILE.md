# Article Audio

Turn the articles I send or select from my bookmarks into full, pleasant audio readings. Use the Article audio skill and its installed portable CLI. Use my existing X access to retrieve articles. Preserve the author's argument and detail; summarize only when requested.

On the first setup or narration request, use the Article audio skill to install https://github.com/harrisrobin/article-audio at release v0.1.2 on your cloud computer. Check and repair missing dependencies even if files already exist. Configure both Gemini and private R2 hosting unless I request local-only audio. Ask for missing API credentials using a native secure secret handoff when available, or guide me through the package's local password form, one provider at a time. Store credentials outside the source project and reuse them. Never ask me to paste keys into ordinary chat. Complete hosted setup with a generated sample and a verified private playback link.

Default to the configured Gemini model and voice, and private R2 links. Offer a short audition before a long first recording. Return the article's title, source link, duration, MP3 link, and link expiry. Reuse completed work and resume failures. Tell me clearly if only local generation succeeded.

The shared template must include the Article audio skill and the pinned public release. Keep account credentials, private content, and temporary playback links out of shared configuration. Files in another account's workspace are not evidence that this installation exists.
