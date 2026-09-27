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

## Published-release template compiler in 0.1.8

Fixed base: `b53be74fb0800c4f350626049d52d72d36753894`. The approved spec is a compiler for published stable releases only. The bundle must contain the complete profile, exactly two skills, four public memories, and verified release provenance. Native Grok publication remains a separate reviewed action.

Independent Standards and Spec reviewers inspected the implementation. Standards found a cleanup race that could remove a file replaced by another process. Cleanup now records device/inode ownership and preserves replaced files. A deterministic regression covers that race. Parent review also found uncaught malformed DEFLATE data and ZIP names truncated at NUL bytes; both now fail with safe compiler errors. Releases missing public metadata receive an actionable unsupported-release error and cannot fall back to local files.

The Standards recheck found no remaining actionable issues. Spec found no code-level deviations; its remaining completion gate was publication and verification against the actual release. All 132 tests pass on Python 3.11, and Ruff lint/format checks pass. Release and native-publication evidence is recorded separately in verification.md.


## Playable hosted auditions in 0.1.9

Fixed base: `f742234db5e50b60a46a461ff58e4f32a00d6fd0`. The owner reported that Grok delivers the first audition as a ZIP that cannot be played inside the app. The fix chooses delivery first, configures the selected hosted destination, and returns a verified MP3 link before asking for voice acceptance. Local-only retains external playback with no implicit upload.

Independent Standards and Spec reviewers both found that moving generation into the hosted branch left new local-only owners without a sample-generation step. Both local-only entry points now explicitly generate or reuse a manifest-matching sample before transfer. Parent review also preserved confirmed narration during hosting-only recovery and removed an obsolete accepted-sample requirement from the public URL instructions. No source comments changed.

Both axes retain publication as a completion gate: the new tag, source archive, verified bundle, and native template must exist before the change is called shipped. Instruction scenarios cover private and public first setup, local-only transfer, shared Gemini recovery, accepted voice with incomplete hosting, voice replacement, delivery-only reuse, and interrupted cleanup. These checks do not establish a clean import or human playback under the revised ordering.

Both reviewers rechecked commit `4bb5f6b` and reported no remaining repository findings. Package and native publication are tracked separately in verification.md.


## Fixed narration and automatic readiness in 0.2.0

Fixed base: `c68c210a5b53dc2968d55bacf9a7affef573c1cd`. The owner's new requirement supersedes the earlier preference-confirmation and cleanup gates. The data shape is one immutable narration preset plus a schema-2 delivery record with `preview_ready`. Only chunk size remains configurable in the internal settings snapshot. Existing cache identities still contain the concrete preset values.

The Model the Domain principle led to a new readiness schema without obsolete acceptance and cleanup flags. The Laziness Protocol kept the existing settings snapshot and cache format, while deleting voice CLI controls, model discovery, and the unreachable legacy provider payload. No remote token-revocation mechanism was added. Setup tokens retain their one-day expiry requirement, matching-only local cleanup, and uncertain upload-token recovery.

Work was split into runtime controls and agent instructions, then checked together. Parent review removed a redundant repeat-publish step and restored concrete bootstrap commands, secure-handoff details, local-delivery requirements, and dedicated-bucket safeguards. The Standards review found no actionable issue. The Spec review found that runtime-only repair could bypass schema-1 migration and that local-only invitation wording implied a Bot-only path counted as delivery. Both were corrected: migration runs first, and local-only needs usable file delivery before readiness. The same pass made explicit setup requests proceed without another invitation. The Spec recheck found one stale playback gate in the earlier marketplace design notes; it now uses automated selected-mode delivery. The active runtime and onboarding instructions passed the recheck, and the final stale research note was confirmed corrected. No new source comments require deletion.


## Adversarial follow-up in 0.2.1

Reviewed `c68c210a5b53dc2968d55bacf9a7affef573c1cd...172f1e1620eb9f24bfa418f6bb5da9daa688e5b8` with fresh independent Standards and Spec reviewers.

Standards found one valid documentation issue. The primary install link led to the older native template while nearby text described the newer fixed-preview behavior. README and INSTALL now label the native snapshot as 0.1.8 with its update pending and offer current skill installation as the available route.

Spec found one valid recovery issue. The onboarding instructions said a ready record qualified for runtime-only repair without dispatching that repair before the generic setup invitation. They now require repair and recheck first, preserving readiness and avoiding new acceptance, credentials, or synthesis solely for runtime repair. Valid schema-1 migration with a customized preview also reuses the saved delivery and keys without a new invitation. The runtime acceptance checklist names these cases.

Two other proposed Spec findings were dismissed. The unchanged short-audio error recommends listening as diagnosis but imposes no playback confirmation or readiness gate. Choosing an unspecified destination is a retained privacy and delivery preference, distinct from the removed voice/playback approvals or a second request to begin setup. INSTALL now makes that distinction explicit.

The Spec reviewer rechecked fresh setup, ready-owner repair, matching/customized schema-1 migration, and missing credentials with no remaining actionable finding. The Standards reviewer also found no unresolved issue after the corrections. All 140 tests, Ruff lint, and formatting passed before these instruction-only corrections. Publication and native runtime evidence remain separate in verification.md.


## Whole-codebase review in 0.2.2

Scope: all 51 tracked files at `20da06789f2e5d962b15ccf518c8bc88a36186b9`, not a release diff. Fresh independent Standards and Spec reviewers used the current security, design, delivery, and template contracts. Parent review also covered the complete compiler, packaging/bootstrap scripts, media pipeline, and external response boundaries. Historical issues were eligible findings.

### Standards

Three hard findings were reproduced and fixed:

1. Multi-key credential reads could combine an old account ID with a newly rotated key, secret, and bucket. Each group now uses one file/environment snapshot. Reusing configured R2 also checks the captured destination under the credential lock before removing setup credentials, preserving them if another process changes the destination.
2. Ranged delivery accepted a correct prefix without validating the range bounds or total object length. S3 and playback reads now require the exact Content-Range and returned byte count/content, including a bounded check for excess response bytes. This remains a ranged-delivery check, not a full remote-file hash or semantic speech check.
3. Public bucket URLs accepted object paths and malformed ports. Validation now rejects these before upload. The independent recheck also caught empty query/fragment delimiters; those are rejected too.

The suggested R2 credential value-object refactor remains a judgment call, not a hard violation. The snapshot boundary fixes the concrete race without adding an unnecessary configuration subsystem. The final Standards recheck accepted all three repairs with no remaining hard finding.

### Spec

Three findings were accepted and fixed. Two overlap the Standards report: incorrect public bucket bases and incomplete ranged-delivery validation. The recheck also found that missing S3 ContentLength or Body fields could escape as internal exceptions; they now produce safe upload_verification_failed errors.

Two candidates were rejected after checking the existing contracts. Complete R2 credential reuse intentionally preserves the configured bucket; the Bot must verify its privacy, and SECURITY.md explicitly warns that signed links do not make public objects private. A stale manifest status alone does not invalidate a matching MP3 hash with a successful media probe and duration check, so cache reuse remains correct.

The final Spec recheck reported all three accepted findings resolved, with no remaining actionable finding or scope creep.

### Parent boundary checks and verification

Malformed Gemini candidates, MIME types, and non-ASCII base64 previously escaped as AttributeError or ValueError; a zero-rate WAV caused ZeroDivisionError during duration calculation. These now become safe provider/audio errors. Regression tests prove malformed provider replies leave failed, resumable manifests without exposing response content.

All 165 tests pass on Python 3.11.14, including credential-rotation races, malformed responses, URL rejection before upload, short-file ranges, incorrect totals, and excess response bytes. Ruff lint and formatting pass. No real credentials, provider calls, bucket changes, or native UI were needed for this review. Release and native-template evidence remain separate in verification.md.

Standards: 3 accepted and fixed, worst issue mixed credentials during rotation. Spec: 3 accepted and fixed, worst issue falsely verified ranged delivery. Two findings overlap; neither axis has an unresolved actionable finding.
