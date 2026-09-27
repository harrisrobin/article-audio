# Template bundles from published releases

## Problem

The public template has previously contained shortened instructions and literal file-path placeholders instead of complete skills. The package release and native Grok template are separate artifacts. Copying their contents by hand leaves several places where they can disagree.

The compiler creates one reviewable template bundle from a published package release. Grok still owns staging, native review, and publication.

## Chosen module

`scripts/compile_template.py` owns verification, composition, and output behind one `compile_published_release(tag, output_dir, client)` operation. Its CLI accepts only a tag and destination. A frozen `VerifiedRelease` record groups the resolved identity and verified archive bytes; composition never accepts arbitrary workspace paths. HTTPX supplies the existing transport and its test seam.

The standalone maintainer command keeps GitHub release operations out of the narration CLI. A separate saved-attestation stage would expose stale-manifest pairing to callers. A generic GitHub adapter and a second module add no useful caller capability here.

## Contract

- Accept one explicit stable release tag. Do not accept branches, drafts, prereleases, or local content previews.
- Fetch the public GitHub release anonymously. Resolve lightweight and annotated tags to a full commit rather than trusting `target_commitish`.
- Verify the source ZIP against its checksum file and the resolved commit's Git tree. Reject unsafe or duplicate paths, symlinks, oversized downloads or archives, missing files, and inconsistent versions.
- Read the full profile, exactly two skills, and public metadata from that verified ZIP. Never fill missing content from the checkout or an owner's Bot.
- Keep the exact four shared memories in `template/public.json`. Expand only the release memory's declared provenance fields after verification.
- Emit the full literal text, source paths, byte counts, content hashes, display metadata, and release provenance in deterministic JSON. Never truncate or summarize bodies.
- Exclude owner credentials, setup status, preferences, recordings, bucket details, and unrelated skills. A public allowlist prevents accidental collection of local state; maintainers must still review the public source files they publish.
- Write complete output without replacing unrelated files. Identical inputs produce identical bundle bytes.
- Keep compilation separate from native publication. A successful build does not prove that Grok saved the complete shared configuration.

## Release sequence

Publish the package ZIP and checksum first. Then compile the template bundle from those public assets and attach the bundle to the same GitHub release. The source ZIP cannot include its own final checksum without making that checksum circular.

The first compatible release includes `template/public.json`. Earlier releases without this file fail clearly instead of using today's memories with yesterday's package.

## Verification

Exercise the command with real ZIP bytes and controlled HTTP responses. Cover complete output, tag resolution, source-to-commit mismatches, malformed metadata, stale pins, unsafe archives, failed downloads, deterministic bytes, and existing-output protection. The tests must establish that neither local files nor configured credentials supply template content.

After publication, run the actual command anonymously against the new release. Compare every emitted body with the published source ZIP, rerun to check determinism, and verify the uploaded bundle and checksum by downloading them again. Native template verification remains a separate check.
