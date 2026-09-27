# Adversarial review

Review baseline: every file in initial commit `437d304822e89c49563c82da44c46a24ff32ffdc`, compared with the repository's pre-creation empty tree. Two independent agents reviewed Standards and Spec using the code-review skill. Local design and security documents supplied the contracts; no issue tracker is configured.

The reports below retain separate axes. Findings are in review order; the repair notes record which claims survived reproduction.

## Standards

**S1. Status reveals a storage path despite a narrower documented contract.** The reviewer cited `SECURITY.md`: “Status commands report names and presence only.” `CredentialStore.status()` also returned `storage_path`.

Disposition: confirmed documentation mismatch. The path is useful for diagnosis and contains no credential value, so it remains; SECURITY.md now accurately lists names, presence, and storage location. Values remain redacted. No credential leak was reproduced.

**S2. Credential recovery advice loops back into the same failure.** `_read()` told users to rerun setup for corrupt storage, but `save()` reads the existing file before merging, so setup could never replace it.

Disposition: fixed. Damaged JSON, invalid saved fields, or files over 65,536 bytes now produce instructions to move the file to a private backup before collecting both providers again. The size case was caught on the second review pass and corrected. Owner, nonregular-path, and mode errors identify the failed property. Named pipes are opened nonblocking and rejected rather than hanging. Documentation distinguishes ordinary rotation, permission repair, and damaged-file recovery. Tests prove the backup is preserved, clean collection works, and permission repair does not lose another provider's values. No automatic destructive reset or relaxation of permission checks was added.

No consequential code-smell finding survived. Local malformed-form, timeout, and file-permission probes found no secret-value disclosure.

## Spec

**Spec 1. A valid but grossly truncated waveform could be marked complete.** The reviewer cited “Output is not marked complete after truncation” and reproduced a short WAV accepted for a long transcript.

Disposition: fixed with a conservative duration guard. For at least 200 alphanumeric characters, raw audio must last at least character_count/100 seconds. Both fresh and resumed WAVs are checked; final and cached MP3 duration is multiplied by playback speed before comparison. Invalid cached audio is discarded and regenerated, and rejected aggregate output is not retained as a completed file. Tests cover fresh output, many small segments, and old valid-hash WAV/MP3 caches. The guard does not establish word-for-word fidelity or detect ordinary omissions, pronunciation errors, or silence. The design now states that boundary explicitly.

**Spec 2. Cached generation discarded corrected source metadata.** The skill requires retaining title, author, and source link. The cache returned before updating `source.json`.

Disposition: fixed. Supplied metadata merges before the cache return. Omitted CLI fields remain unset and preserve earlier values; an explicit empty string can clear a field. A regression test corrects the title while retaining the author and source URL, with no new narration request.

**Spec 3. Native Grok and live R2 validation remain outstanding.** The reviewer cited the template's runtime validation requirement and the verification document's unchecked integrations.

Disposition: expected external validation, not a missing local-code repair. The user explicitly plans to install and test the template in Grok. The package supplies scripts, a skill, a profile, and a guided installation prompt, not a fabricated native template link. Real R2 permissions and Grok's native secret handoff remain unverified here; the fallback form is tested locally. The checklist stays visible in verification.md.

**Spec 4. Recursive packaging could include accidentally saved private text.** The reviewer cited the no-private-content distribution requirement and reproduced `docs/private.txt` being included. Root reproduction also found that a private file under the Python package could enter the wheel.

Disposition: fixed across all three formats. One explicit list of approved files in `pyproject.toml` drives Hatch and the ZIP builder. A regression test inserts random private markers under docs, examples, and src, builds the ZIP, source distribution, and wheel, and verifies that no marker is included. The README also states the remaining boundary: maintainers must review the content of approved files before publishing them.

## Cloudflare setup follow-through

The guided hosted setup now collects Gemini and all four R2 values before uploading the sample, with one form at a time. An HTTP-level test verifies that the R2 form persists all fields without overwriting Gemini's saved key. The optional plugin's authenticated bucket tools and the CLI's separate S3 credential requirements are documented from current primary sources.

Root review also found a hardcoded default-jurisdiction R2 endpoint. `publish --jurisdiction` and `R2_JURISDICTION` now support default, EU, US, and FedRAMP hostnames. Tests cover all four plus rejection of arbitrary endpoint input, so credentials cannot be redirected through that option.

## Verification

The 50-test regression suite passed on Python 3.14 and 3.11. Lint, source/wheel builds, clean ZIP installation, repeated setup with dummy credentials, and standalone wheel execution passed for version 0.1.1. Both reviewers rechecked the fixes and reported zero remaining findings. See verification.md for the separate live-integration checklist.

Standards: 2 findings addressed; the worst practical issue was unusable recovery advice. Spec: 4 findings, 3 fixed and 1 external validation item retained; the worst publication risk was unintended private-file inclusion, now fixed.

## GitHub bootstrap review for 0.1.2

Two independent agents reviewed `b767d68...561fd5b` before first publication. Standards found no hard violations and one maintenance concern: release versions repeated across the profile, bootstrap instructions, and package metadata could drift. A release consistency check now compares all installation tags and archive names against pyproject, the lockfile, and the runtime version. Spec found no actionable issues. Native secret handoff and live R2 testing remain assigned to the user's imported-Bot test.
