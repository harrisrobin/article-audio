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

## Any-message onboarding review for 0.1.3

Two reviewers examined `47af3d1...696f6e1`. Standards found that a returning local-only user could be mistaken for an interrupted hosted setup. Spec found the same missing state and a possible loop between onboarding and narration skills. The agent now maintains a nonsecret mode/completion record outside the checkout, and the narration skill skips onboarding when already entered from it. Greeting, unrelated question, article URL, explicit setup, returning user, local-only, and deferral scenarios were reviewed. The readiness record is agent-maintained, not a new CLI feature.

## Automatic Cloudflare setup review for 0.1.4

Two independent reviewers examined `d2b6944...c15f5c1` and rechecked the fixes in `b921577`. The user's approved spec was account ID plus one short-lived setup token, exact dashboard/permission instructions, automatic private bucket and bucket-scoped upload credentials, native secret handoff when available, and the existing four-field fallback.

Standards found three valid defects: concurrent manual credentials could be overwritten at commit time; complete-R2 reuse could retain an unnecessary setup token; and the recovery marker's directory entry was not fsynced. Fixes add a compare-before-commit under the credential lock, remove file-backed setup credentials on reuse while preserving runtime credentials, and fsync the containing directory after atomic replacement. Regression tests cover concurrent manual entry, interrupted credential persistence, reuse cleanup, CLI redaction, and permission/privacy failures. The Spec recheck found that the concurrent-manual branch still retained the broad setup token. That branch now removes the file copy too and explicitly directs external revocation; if cleanup fails, its error reports the retained copy.

Both reviewers completed their final rechecks with no remaining actionable findings. Live Cloudflare provisioning remains a user-account validation step. Mocked API tests do not prove the installed Grok secret handoff or actual Cloudflare permissions.

## Final release review for 0.1.5

Two independent agents reviewed from fixed base `d2b6944744e06b1d68d81bf6697085e7afb3456c` (v0.1.3) through `c125622`, then rechecked the fixes in `fcb05d5`.

### Standards

The review found a credential-rotation race: successful provisioning or concurrent manual setup could remove a newer Cloudflare setup pair saved during the request. Cleanup now compares the whole pair under the credential lock and preserves replacements. Tests cover successful provisioning, concurrent manual R2 setup, and environment/file divergence.

The security policy also contradicted the intentional removal of an unused setup token after concurrent manual R2 setup succeeds. SECURITY.md now distinguishes this completed-setup case from incomplete failures that retain credentials for repair. A proposed enum for the token-request marker was not adopted: the boolean deliberately records uncertainty about whether a remote token POST occurred, and explicit user-confirmed retry remains the recovery boundary. The reviewer accepted these dispositions.

### Spec

The review found that an older working runtime could satisfy readiness after a template update. Onboarding now checks both version 0.1.5 and the template's full release commit before executing the runtime. A versioned installation directory and optional private runtime_path support repair without overwriting a dirty checkout or losing credentials, recordings, delivery mode, or prior sample verification. Runtime-only repair does not request keys or synthesize another sample.

The concern about creating the earlier replacement template referred to publication before the user requested updates in place. It remains a publication acceptance gate: update the existing zBuR546KeAs5X0iwlXkxt template and verify its URL. INSTALL.md documents that procedure; imported copies are not assumed to update automatically.

Both reviewers independently rechecked the final changes and reported no remaining actionable findings. Each ran the 81-test suite successfully. Real Cloudflare provisioning and native credential handoff remain the user's fresh-import integration test.


## Expert feedback follow-up for 0.1.6

Fixed review base: `e64b77cabf5b67553f1a2081cd7db4a3280b68ab`. The user's supplied expert feedback is the spec; this repository has no issue tracker. Scope is the profile, onboarding contract, release hygiene, and honest live-validation evidence. No new CLI preference subsystem is introduced.

- Explicit ONLY job and Anti-jobs now cover social distribution, unrelated assistant work, editorial changes, public hosting, and instructions embedded in source material. The narration voice remains an audition candidate.
- The existing private readiness record now carries user-confirmed narration settings and delivery. Audition precedes hosting; the agent passes saved settings explicitly because the CLI does not read this record. Missing records or older records with no preferences resume setup without erasing keys.
- v0.1.5 was already published to the retained template in place. Older verification entries are historical. The earlier public ID is now explicitly deprecated in installation guidance; its deleted authoring Bot still prevents supported removal.
- The template must contain exactly the two current skills. Native inspection subsequently found the legacy account-wide skill, which was deleted after explicit confirmation. Grok reported correcting the stale editable store name to Article Audio. No unrelated Bot skills or opaque IDs should be changed.
- An EU jurisdiction note and an acceptance-test runbook distinguish local tests, account recovery, human playback, and clean-import proof. Live R2, native handoff, and cleanup evidence remain unverified until actually observed.

### Standards

The reviewer flagged two instruction ambiguities. The completed-state example now explicitly represents automatic R2 setup and records cleanup as complete, avoiding the manual-only not-needed example. Offline `plan` validates voice-name syntax, not Gemini voice availability; confirmation now requires a successful matching audition manifest plus human acceptance. No code-smell changes were requested.

### Spec

The independent reviewer found no actionable repository defects. Native publication and legacy-skill retirement are now verified in verification.md; Grok reported the store-name repair. The agreed account-recovery test remains a separate live validation step. Reusing the saved Gemini key cannot establish clean-import isolation.

The Standards reviewer rechecked both fixes and reported no remaining findings. Spec reported zero repository findings. The 81-test suite passes on Python 3.14 and 3.11; Ruff and both skill validators pass.


## Public delivery and browser form repair in 0.1.7

Fixed base: `31afaa603ba12eb53efcb5b839fce703d28ff766`, reviewed through `3483de9`. The spec is the owner's accepted audition with public R2 defaults and `r2.dev` for testing, plus the live credential-handoff failure. Two independent agents reviewed Standards and Spec.

### Standards

The reviewer found that proposed alternate configuration directories lacked a complete migration of the accepted record and Gemini credential. That speculative migration path was removed. If the configured bucket contains private or unrelated files, setup now stops without altering credentials or access; automatic migration is explicitly unsupported. Fresh setup still creates a dedicated bucket. A possible policy-duplication concern was retained as a nonblocking maintenance observation after the instructions were made consistent.

The fallback form failed a real browser submission because `Referrer-Policy: no-referrer` made the POST carry `Origin: null`, despite a same-origin navigation. A dummy-credential browser reproduction confirmed the failure. Switching the response policy to `same-origin` made the browser send the actual loopback origin and save successfully. Exact Host, non-null Origin, path, CSRF, expiry, one-shot saving, and no-logging checks remain. Regression assertions cover the policy and rejection of hostile, null, and missing origins. The reviewer rechecked the fix and found no remaining actionable issue.

### Spec

Both passes found no actionable repository defect. Public delivery saves the verified base URL and uses it on retries and post-cleanup uploads; other owners still default to private. Existing audio is reused. Native-card storage is distinguished from subprocess injection, which remains unverified for the Cloudflare pair. Live provisioning/playback and template publication remain external evidence gates, not implied by local tests.
