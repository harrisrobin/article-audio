# Build a public template bundle

Publish the package release and its source ZIP plus checksum before compiling its template bundle. Run the compiler from an installed source checkout with Python 3.11 or newer:

```bash
uv run python scripts/compile_template.py v0.2.1 --output-dir dist/template-v0.2.1
```

Use an explicit published stable tag. The command does not accept a branch, a draft release, a prerelease, or local preview content. It makes anonymous GitHub requests and does not need Gemini, Cloudflare, or GitHub credentials. Releases without `template/public.json` are unsupported.

The compiler verifies the release ZIP's checksum and compares its files with the resolved tag commit. It reads the profile, both skills, and public metadata from that ZIP. Edits in your checkout do not change those contents. See [the design contract](template-compiler-design.md) for verification requirements.

On success, the output directory contains the JSON bundle and its SHA-256 sidecar. Use a new output directory for each attempt; the compiler preserves existing output. Attach both files to the same release:

```bash
gh release upload v0.2.1 \
  dist/template-v0.2.1/article-audio-template-v0.2.1.json \
  dist/template-v0.2.1/article-audio-template-v0.2.1.json.sha256
```

Do not replace an already published bundle with different bytes. Investigate any discrepancy between an existing asset and a newly compiled bundle.

## Prepare Grok's native review

Download the bundle and its checksum from the release. Verify the checksum before using it. Copy the complete text fields into Grok's template preparation tool, including the full profile, both skills, and all four memories. Preserve the exact release commit and source ZIP checksum.

Open **Share > Update template** for the existing authoring Bot. Check its display metadata, complete profile, each skill through its last paragraph, and every shared memory's complete text and saved length against the bundle. Open memory details rather than relying on list previews; inspect any 500-character cutoff. Native shared fields must contain literal text, not file paths, JSON expressions, or summaries. A hash of the downloaded source does not verify what the host saved. Stop before publication if the saved content is incomplete. Exclude credentials, owner preferences, setup status, recordings, and unrelated skills.

### Fit memories into native fields

Grok's observed native memory limit is **500 characters per fact**. Longer strings were accepted by the staging tool but truncated when saved. Split any longer bundle memory at sentence boundaries into consecutive facts of at most 500 characters. Preserve every word and the original separator between parts; do not summarize or clip the text. The compiler's four canonical memories remain unchanged.

For v0.1.8, the release memory becomes parts of 467 and 70 characters, and the setup/privacy memory becomes parts of 489 and 107 characters. Each pair joins with one space. The other memories remain single facts of 397 and 471 characters, giving six native facts in total.

Read back every saved part before publication. Reconstruct each canonical memory with its original separator and compare the complete text and SHA-256 with the bundle. A successful source checksum or staging response is not enough. If the saved parts do not reconstruct the source exactly, stop and correct the draft.

Publish the reviewed native update and confirm that **Copy link** returns the existing template URL. A compiled or uploaded bundle does not update Grok by itself. The public preview cannot prove the full skill bodies were saved. Follow [the native publication checks](../template/INSTALL.md#update-the-existing-public-template).

## Recover from a compiler failure

- If the release is missing or incomplete, finish publishing its package assets and retry.
- If GitHub rejects anonymous requests, wait for its rate limit to reset. Do not put tokens in compiler arguments.
- If a checksum, source file, version, or metadata check fails, correct the release source and publish a new release. Do not bypass validation or substitute local files.
- If the destination exists, inspect it and choose a new output directory. Preserve prior artifacts for comparison.

The bundle format is specific to Article Audio. It is a review artifact, not a documented Grok import API.
