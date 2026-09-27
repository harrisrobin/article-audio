# Verification

Local evidence from 2026-09-27. This distinguishes implemented behavior from integrations that still need a real account test.

Current published package: [GitHub v0.2.1](https://github.com/harrisrobin/article-audio/releases/tag/v0.2.1) includes the fixed narration flow and the adversarial-review corrections to runtime repair and installation guidance. Its source archive and complete template bundle are published and independently verified. The native Grok update is blocked by the locked Mac. Native v0.1.8, staged version 16, remains the last verified publication at [the retained template](https://x.ai/bot/zBuR546KeAs5X0iwlXkxt). Earlier unpublished drafts are superseded; stage v0.2.1 when native control resumes.

Earlier sections are historical. The old `u9M4WdBafSgCyS3GNHKla` template remains deprecated and accessible; no supported removal was found. Shared-account fallback storage, R2 provisioning, and public sample delivery were verified below. Native secret delivery, a clean import, and complete X Article narration still need their own proof.

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

## Historical first Grok Bot template, deprecated

The original template `u9M4WdBafSgCyS3GNHKla` was published with the first release and is now deprecated. Grok fetched the public skill, saved it through its skill system, and created the template. Native inspection at that time confirmed its narration/bootstrap skill, exact commit, ZIP checksum, first-use setup rule, X-access guidance, and generated getting-started skill. The current template uses only Article audio and Article Audio onboarding. The old public preview remains accessible but is not the current install path.

The template-authoring Bot did not install the runtime or configure credentials, preserving the user's planned first-use test. Public template publication does not establish searchable Marketplace catalog inclusion. The main branch now links to the template; the pinned v0.1.2 assets remain unchanged.

## Automatic hosting setup in 0.1.4

The local suite passes 78 tests on Python 3.14 and 3.11, including automatic bucket setup against a mocked Cloudflare API, exact bucket-scoped token policy, bootstrap cleanup, preservation of concurrent manual credentials, denied and uncertain requests, recovery without repeated token creation, unsafe state files, private-bucket checks, and all three local credential forms. Both skills validate, Ruff checks pass, and ZIP/wheel/source builds succeed. The two-axis review found three Standards defects and one Spec cleanup defect, all addressed before release.

The code does not claim live Cloudflare provisioning or installed native-card compatibility. The fresh-import test must verify native secret collection or the documented fallback, real bucket and upload-token creation, a sample listening link, setup-token revocation, and a successful repeat publish using the saved bucket credentials. Deleting a Bot does not clear account-shared files or secrets, so a reinstall on the same account may reuse earlier setup.

Version 0.1.4 was published from `cfd83882dc8c0648422be58b729dcd2c3608bc2c`. A clean ZIP installation passed dependency setup, doctor, provisioning help, and offline planning. Anonymous download verification confirmed all 43 archive files match the tagged source exactly. ZIP SHA-256: `22293852d43ecb3fdd771750b2028493c91e672e00a6c8f6aa23876719bfff15`.

The replacement [v0.1.4 native template](https://x.ai/bot/zBuR546KeAs5X0iwlXkxt) was published and its public preview verified. Native review confirmed both skills with their complete release instructions, the full profile, four intended shared memories, exact revision/checksum, first-message readiness rule, and automatic Cloudflare setup guidance with manual fallback. No credentials or account-specific files were included. This is a new public template, not an overwrite of the earlier `u9M4WdBafSgCyS3GNHKla` link. The old template was not deleted.

[GitHub run 36320092567](https://github.com/harrisrobin/article-audio/actions/runs/36320092567) again started no test steps. Its Python 3.11 check reports the account billing lock; Python 3.13 was canceled by the matrix. Local verification is passing; hosted CI remains unavailable.

## Credential rotation and runtime repair in 0.1.5

All 81 tests pass on Python 3.14 and Python 3.11. Ruff lint and formatting checks pass. Two independent adversarial reviewers rechecked the credential-rotation cleanup fix, the pinned runtime repair flow, and the update-in-place instructions, with no remaining actionable findings. This does not establish live Cloudflare permissions or Grok's native credential handoff.

[Version 0.1.5](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.5) was published from `b52e77308939635366dc0ed261514bf624cc9957`. A fresh ZIP installation passed dependency setup, the wrapper outside its checkout, doctor, provisioning help, and offline sample planning. Anonymous downloads verified the ZIP checksum, all 43 files against the tagged source, and the public profile plus both complete skills. ZIP SHA-256: `e2b715e256e47cabe54fa66f4499cb12d16bc2a1a55275412199b49cae2d87f8`.

The existing [native template](https://x.ai/bot/zBuR546KeAs5X0iwlXkxt) was updated in place to v0.1.5 on 2026-09-27. Grok staged version 2 of that template; its review card changed from Unpublished to Published after publication. The shared context contained the exact release commit and ZIP checksum, four intended public memories, and both Article Audio skills. The registered onboarding instructions include version/commit verification and runtime-only repair. Reloading the same public URL showed the v0.1.5 profile, confirming the URL was preserved. This update does not prove setup on an imported Bot or live Cloudflare access.

The earlier u9M4WdBafSgCyS3GNHKla template remains publicly accessible. Its authoring Bot had already been deleted. The current Bot reported no supported tool to delete or unpublish that other template, and the inspected marketplace management view exposed plugins and skills, not orphaned templates. No deletion was performed. Removing this old link remains unresolved and may require product support; it does not block testing the updated zBuR546KeAs5X0iwlXkxt template.

[GitHub run 36321145250](https://github.com/harrisrobin/article-audio/actions/runs/36321145250) started no steps. The Python 3.13 check reports the same account billing lock; Python 3.11 was canceled. Hosted CI remains unavailable despite passing local checks.


## Expert feedback and preferences in 0.1.6

The profile now states its only job, anti-jobs, and source-instruction boundary. Agent onboarding auditions before hosting, confirms and saves narration/delivery preferences once, and resumes partial setup without clearing shared credentials. The CLI continues to use explicit flags; it does not read the agent's readiness record.

All 81 tests pass on Python 3.14 and 3.11, both skill validators pass, and Ruff lint/format checks pass. These tests validate existing CLI behavior, not human acceptance of the new agent instructions. The two-axis review and dispositions are in review.md. Native publication and legacy-skill removal are verified below. Live account-recovery playback/token cleanup remains pending. A clean-import pass still needs an isolated account/computer; the owner chose to preserve and finish the existing Gemini setup.

[GitHub v0.1.6](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.6) was published from `411166cc48c30350fd95eae29c980fad63c4d102`. Anonymous download verification matched all 45 ZIP files to the tag, checked the checksum, and retrieved the exact public profile, both skills, and new preference/test guides. ZIP SHA-256: `732a63c102742380e2c959c22d9c559498a945ab5dd1240bd7e1668d804c9563`. A fresh ZIP installation passed setup, version, doctor, provisioning help, and offline sample planning from outside the checkout.

The Mac app-control connection timed out on native inspection and reconnection attempts. No v0.1.6 native update, legacy-skill removal, store rename, or live setup is claimed. The owner approved finishing existing setup while preserving its Gemini key; credential entry and human playback await the restored connection. CI remains blocked before any steps run: the GitHub check annotation says the account is locked due to a billing issue.


### Native v0.1.6 publication

On 2026-09-27, after the app-control connection recovered, Grok staged version 3 of the existing `zBuR546KeAs5X0iwlXkxt` template. Native review showed four intended public memories with the exact release commit/checksum and exactly `article-audio` plus `article-audio-onboarding`. The registered onboarding body showed v0.1.6, preference confirmation, shared-key recovery, and token-cleanup gates; the narration editor showed the matching release and audition-before-hosting flow. The template's Publish action changed to Copy link, its conversation card showed Published, and the same public URL displayed the complete v0.1.6 profile. No replacement Bot or public URL was created.

The owner explicitly confirmed deletion of the obsolete account-wide `Article audio getting started` skill. The native Delete Skill confirmation completed; the UI reported deletion and the remaining skill list retained the two current Article Audio skills plus the unrelated hospital skills. This is separate from the old orphan public template, which remains deprecated rather than deleted.

Grok reported correcting the editable store display name from New Agent to Article Audio with a name-only metadata edit after the normal profile/UpdateAgent actions did not synchronize it. The visible Bot and template names are Article Audio / Article narrator. The live setup is now using the saved Gemini key, preserving shared state, and preparing an audition before any Cloudflare credential collection.

### Shared-account setup recovery

Grok reported that both complete registered instruction bodies match the tagged v0.1.6 files after frontmatter extraction, the store name reads Article Audio, and the deleted legacy skill was not recreated. It installed `/workspace/article-audio-v0.1.6`, verified the clean source origin and exact release commit, passed CLI version/doctor checks, and saved the runtime path privately. It reused the saved Gemini key and generated an approximately 51-second Algenib audition at 1.1x with the package direction.

The first response claimed a file was attached, but native UI inspection showed no playback/download artifact. Delivery repair was requested using the existing MP3, without regeneration or preference acceptance. Human playback, preference confirmation, R2 credential collection/provisioning, setup-token revocation, and repeat publish remain unverified. This is shared-account recovery, not a clean-import test.

Delivery repair succeeded without new synthesis: Grok reported direct MP3 attachments are blocked by this host, used its supported CopyFromBox tool to deliver the existing file to the owner's Mac, and attached a ZIP containing that MP3 in chat. The native UI displayed the ZIP download. Local ffprobe verified the copied MP3 is 814,227 bytes and 50.814671 seconds, and it was presented for playback. These transport/decoding checks do not establish human listening or preference acceptance.


## Public delivery preferences in 0.1.7

The owner accepted the delivered Algenib audition at 1.1x with the same model and restrained British direction, and explicitly selected public R2 links using `r2.dev` for this test. Grok reported saving those choices privately without resynthesis and keeping sample verification incomplete. Both native Cloudflare cards displayed Saved, but Grok reported that the pair was absent from its subprocess environment. The local fallback then rejected the submitted form with a cross-origin error. This is not successful credential handoff; provisioning, public access, playback/seek, and token cleanup remain unverified. No owner URL or bucket identifier is published here.

The new instructions save public delivery and its verified base URL, pass it on retries and post-cleanup publishing, and keep private delivery as the default for other owners. They require a dedicated bucket before public exposure and distinguish a signed URL from making a bucket private. The existing CLI already implements public publishing; no new permission-changing CLI was added.

All 81 tests pass on Python 3.14 and Python 3.11, Ruff lint/format checks pass, and both skill validators pass. Release artifacts, native template update, and the live public-hosting test are still pending. This remains shared-account recovery, not clean-import proof.


### Browser form diagnosis

A local browser test with dummy Cloudflare values reproduced the same failure: `Origin:null` with `Sec-Fetch-Site:same-origin` under the old `no-referrer` response policy. After changing the policy to `same-origin`, the browser sent the exact loopback origin, the page reported Credentials saved, and the server confirmed success. No real credentials were used in that probe. HTTP regression checks still reject hostile, missing, and null Origin headers. The independent Standards and Spec rechecks found no remaining actionable findings.


[GitHub v0.1.7](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.7) is published from `dfa61e82b9a4f3f6af68f8ae4c47ad8dd4568820`. Its ZIP checksum is `1657dbe5f5852b221beb86297a1a0ede080e2ebe0097ecf9b01a168cd254e4df`. Anonymous download verification matched all 45 files to the tag. Fresh ZIP installation passed version, doctor, provisioning help, and offline planning outside the checkout. The final 81-test suite passes on Python 3.14 and 3.11; Ruff and both skill validators pass.

Grok reported that a separate host-spawned worker also received only the Gemini injected-secret name, with both Cloudflare names absent. This confirms the observed handoff failure extends beyond an ordinary child shell. It does not prove the vault deleted the saved secrets or establish the internal cause. Credential collection is paused while the fixed runtime and native template update are staged. Native Settings also displayed an older v0.1.5 profile; the update must verify that live description as well as the public preview.


### Native v0.1.7 publication and runtime

The first staged version contained only a short summary in its shared Instructions field. It was not published. The corrected version 5 included the full tagged PROFILE, four intended public memories, the exact release SHA/checksum, and the two current skills. Native review confirmed those contents. Publishing changed the control to Copy link; the fresh public page at the same zBuR URL displayed the complete v0.1.7 profile through its final paragraph. Native Bot Settings also displayed the full current profile, correcting the stale v0.1.5 text observed earlier. No duplicate public template was created.

Grok reported installing `/workspace/article-audio-v0.1.7` with the exact clean release HEAD, version/doctor checks passing, and the fixed response header present. It updated runtime_path without changing accepted narration, delivery choice, or the existing audition. The repaired fallback is being reopened once for the owner; this is not yet proof of live credential storage, R2 provisioning, public playback, or setup-token cleanup.

The observed desktop app version is 0.61.0. Its native Cloudflare cards displayed Saved, while both original and fresh host-worker checks reported the Cloudflare environment names absent. The internal host cause remains unknown; no claim is made that stored secrets were deleted.

[GitHub run 36325438656](https://github.com/harrisrobin/article-audio/actions/runs/36325438656) again started no tests. The check annotation reports the account billing lock. Local checks passed; hosted CI remains unavailable.

### Live fallback credential storage

On 2026-09-27, native Settings reported desktop 0.61.0 Stable and the shared cloud computer up to date. Fully quitting and reopening the desktop app did not change the Bot's subsequent presence-only result: Gemini was injected, while both Cloudflare names were absent. The Bot reported no supported refresh/rebind operation or browser-fill path for an existing Bot Secret. This is an unresolved native handoff, not proof that the saved vault values were deleted.

The owner then chose the repaired local fallback. The first attempted handoff was text only; after correction, native inspection verified an actual Computer / Take over card. On completion, Grok reported both the page's Credentials saved result and the CLI's Cloudflare-present status, while Gemini remained present. No values were inspected or printed. This establishes live credential storage through the v0.1.7 fallback on this account; it does not establish native-card delivery or a clean import. R2 provisioning and public playback remain separate checks.

The subsequent provisioning attempt stopped at its first Cloudflare API request with an authentication rejection. Redacted validation identified an unusable saved setup token. No bucket or upload-token creation was attempted, and correction through the local form is pending. Credential presence is therefore verified, but Cloudflare authentication, R2 provisioning, public playback, and setup-token cleanup remain unverified.

### Live public R2 playback

After the owner corrected the setup token, Grok reported successful provisioning of one new dedicated bucket and a bucket-restricted upload key. It verified that the returned bucket matched its reservation and saved R2 configuration, enabled that bucket's managed r2.dev domain through the documented Cloudflare API, and read back enabled=true. It saved the public base URL only in the owner's private preferences. The matching setup-token file copy was removed; this is not provider revocation.

Grok published the previously accepted audition without resynthesis and reported public access, verified=true, and no scheduled expiry. An independent unauthenticated range request from the owner's Mac returned HTTP 206, audio/mpeg, Accept-Ranges: bytes, and Content-Range: bytes 0-1023/814227. The owner confirmed that the public link plays and seeks correctly. No owner URL or bucket identifier is included here. Setup-token revocation, native-secret cleanup, and a repeat publish using the saved upload key remain pending, so overall sample verification must stay false. This remains shared-account recovery, not a clean-import or full X Article test.

The owner subsequently confirmed provider revocation of the temporary setup token while retaining the bucket upload token. Grok repeated the audition publish using saved R2 credentials and the saved public base URL, reported verified public delivery with no expiry, and confirmed the setup token was absent from the private store and process environment. It then marked setup-token cleanup complete and sample verification true. This establishes completion of the shared-account setup via the local fallback; a clean import and full X Article narration still require their own tests.

### Native audio rendering limitation

On desktop 0.61.0, the Bot reported that its supported SendToUser voice-memo mode synthesizes message text with the host's voice and cannot accept an existing audio file or URL. Its attachment path rejects audio files as voice memos. The Gemini MP3 therefore remains a public listening link or an owner-delivered local file; the documented presence of voice memos in chat does not establish support for external MP3 playback. No replacement narration, file-type disguise, or additional UI service was created.

### Final template content verification

The later sharing drafts initially contained shortened instructions or literal `FILE:/tmp/...` markers in place of skill bodies. Native review identified those defects. The corrected draft, reported by the staging tool as version 11, carries the full v0.1.7 PROFILE, both literal skill bodies, and four intended public memories with the exact release commit and ZIP checksum. Native inspection checked both skills through their final sharing paragraphs and confirmed that the obsolete getting-started skill and unrelated skills are absent. Grok reported matching the source hashes for the profile and both skills. Owner setup records, bucket details, preferences, and credentials were excluded.

The version 11 conversation card changed from Unpublished/Publish to Published/Copy link. The retained public URL was independently fetched with `Cache-Control: no-cache`; it returned HTTP 200 and contained the complete tagged PROFILE verbatim, including its final paragraph. An in-app browser reload temporarily retained the short description. The HTTP response advertises `s-maxage=86400` and `stale-while-revalidate=604800`, so a stale preview alone is not a reliable publication check. No numeric revision is exposed by the public page; the native card and staging result establish the revision evidence.

The release code and v0.1.7 assets are unchanged. Subsequent repository commits update verification and publication instructions only. This completes the current shared-account setup and template repair. A clean import and narration of a complete X Article remain separate acceptance tests.

## Published-release template compiler in 0.1.8

[GitHub v0.1.8](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.8) was published from `14e40990bee6ce327a801eb83379f5abc69291e5`. The ZIP SHA-256 is `e84114262eaf6bbb690c5adc21df23eddd2b3edd71132e9b3d78ddf0b903c947`. All 132 tests pass on Python 3.11, Ruff lint and formatting pass, and both skill validators pass. Standards and Spec review outcomes are recorded in review.md.

The actual compiler command succeeded against the published release through anonymous GitHub requests. An independent download matched all 51 ZIP files to the tagged source and checked the full profile, two complete skills, four rendered memories, byte counts, and body hashes. Running the compiler from a fresh extraction with a new Python 3.11 environment produced byte-identical JSON and checksum files.

The release now includes `article-audio-template-v0.1.8.json` and its SHA-256 sidecar. Anonymous downloads of both exactly matched the local verified outputs. Bundle SHA-256: `eb88cab53355d79aa02a745bc60b9913c0f1cb6cf4d7e39ec8f813b7c478ef57`. An initially cached release-metadata response omitted the newly uploaded assets; a fresh metadata request confirmed them before download verification.

[GitHub run 36336342180](https://github.com/harrisrobin/article-audio/actions/runs/36336342180) started no test steps. Its check annotation again reports the account billing lock. Local test results do not establish hosted CI success. This release changes template assembly and release verification; it does not change narration performance or establish a clean Grok import.

### Native v0.1.8 publication and memory defect

After Mac access recovered, Grok verified the bundle checksum and updated the live public profile and both registered skills. Native review showed the complete profile and both skills through their final sharing paragraphs, four intended memories, and the exact v0.1.8 commit and ZIP checksum. Publishing staged version 14 changed its button to Copy link and its conversation card to Published. The retained public URL displayed the complete v0.1.8 profile through the final paragraph. No new template ID was created.

Final inspection of the individual memory detail found the release memory cut off at character 500, compared with 538 in the bundle. The setup/privacy memory has 597 characters in the bundle and was also truncated. Grok's supported read-back reported actual stored truncation, not just a list-preview limit. Correction was requested in place. Installation and bundle-publication guidance requires opening every memory and comparing its saved full text and length before publishing. Source hashes alone cannot establish successful host storage.

### Native v0.1.8 memory repair

On 2026-09-27, staged version 16 split the two over-limit memories at sentence boundaries. Independent comparison used the actual text read from native Context, rather than the staging tool's source hashes. The six saved facts had lengths of 467, 70, 397, 489, 107, and 471 characters. Joining the first pair and the setup/privacy pair with their original single spaces reproduced all four canonical bundle memories exactly, including each SHA-256. No text was summarized or discarded. Version 15, which still contained over-limit strings, was not published.

Native review also inspected the profile through its final paragraph and both complete skills through their final sharing sections. Only `article-audio` and `article-audio-onboarding` were included. Publishing version 16 changed its control to Copy link and its conversation card to Published. Copy link returned the same `zBuR546KeAs5X0iwlXkxt` URL; reloading the public page showed the complete v0.1.8 profile. The public page does not expose the numeric native revision or memory bodies, so those checks rely on the native review.

The v0.1.8 package and compiler bundle are unchanged. This repair changes native memory packing and repository publication guidance only; it does not establish a clean import or full-article narration. Grok reported that owner preferences, runtime, and credentials were left untouched.


## Playable hosted auditions in 0.1.9

The previous flow required voice acceptance before configuring R2 and offered a ZIP when Grok rejected direct MP3 attachments. The owner reported that the ZIP could not be played inside Grok. The revised flow chooses delivery first, configures the selected hosted destination, then sends a verified direct MP3 link before asking for voice acceptance. Local-only explicitly discloses external playback, and ZIP transfer alone never establishes playback or readiness.

Accepted narration settings, existing samples, shared credentials, and automatic setup-token cleanup remain protected. The runtime APIs and synthesis behavior are unchanged. All 132 tests pass on Python 3.11, Ruff lint/format checks pass, and both skill validators pass. The package and bundle publication checks below pass. A fresh import and human playback under the new ordering remain separate acceptance checks.


[GitHub v0.1.9](https://github.com/harrisrobin/article-audio/releases/tag/v0.1.9) was published from `4bb5f6b32227bd17dde6cda244f12926f5160ef6`. ZIP SHA-256: `2dc22954a0916423f4b867a852aa8704ade986588c0464f5ed8075832fb40f24`. An anonymous download matched all 51 archive files to that commit. The compiler run from a fresh extraction produced the same complete profile, two skills, four canonical memories, JSON bundle, and checksum as the release build. Public downloads of the bundle and sidecar matched the verified outputs. Bundle SHA-256: `ce803b4582c43f09c7d51ac11124ba765dbb18930e0b78fd368ac1dd41fe571b`.

[GitHub run 36354196478](https://github.com/harrisrobin/article-audio/actions/runs/36354196478) started no test steps. Its annotation reports the existing account billing lock. Local tests passed; hosted CI did not run.

Grok reported verifying the bundle and updating both complete live skills. Native template staging was in progress when the Mac locked, before the new review card could be inspected or published. This is not a verified v0.1.9 native publication.


## Fixed narration and automatic readiness in 0.2.0

The owner requested one informational preview with no voice controls, voice acceptance, manual playback/seek check, or setup-token-revocation checkpoint. The CLI now exposes only the fixed Gemini 3.8 Flash TTS / Algenib / British / 1.1× preset. Automated media and selected-mode publish verification remain. Schema 2 records `preview_ready` and delivery configuration, replacing the former narration, confirmation, and cleanup flags. Migration preserves credentials and recordings.

The complete local suite passes 140 tests on Python 3.11, including CLI rejection of all removed controls before provider access or job creation. Ruff, formatting, both skill validators, and direct wrapper version/help/plan checks pass. Native and fresh-import behavior for this release remain untested while the Mac is locked. This local result is not a hosted CI result.


Published package commit: `7c17964566d8e2d9f2e3c1f85f7abe78d81bec29`. Source ZIP SHA-256: `e4ba6aa78c1e0bf4e234714ed51a7f94ac5bc76fabe532963bff644d58071584`. Bundle SHA-256: `a944fb7f8aaf5441545e04914ed1555d7d413273cf4426ebf2e892d39453f656`. All six release assets are published. Anonymous downloads matched the verified local bundle and checksum. Every one of the 51 source ZIP files matched the tag commit. Compiling from that fresh downloaded source with Python 3.11 produced byte-identical bundle and checksum files.

The release memory expands to 538 characters and needs two native facts; the other canonical memories are 397, 484, and 471 characters. Native publication must preserve all five resulting facts, both complete skills, the full profile, and the same template URL. Grok control was attempted again after package publication and still reported a locked Mac, so no v0.2.0 native update is claimed.

GitHub Actions run `36355321696` did not execute any test steps. Its annotation says the account is locked due to a billing issue. The 140-test result is local; the clean-import behavior of this simplified flow remains unverified.


## Adversarial follow-up in 0.2.1

The independent follow-up review corrected two instruction issues. Already-ready owners now get runtime-only repair before any setup invitation; schema-1 migration reuses their delivery and keys. README and INSTALL prominently distinguish the older native template from the current package and offer manual skill installation until native publication.

All 140 tests passed again on Python 3.11, with Ruff and formatting checks passing. After the instruction corrections and patch-version change, both packaging tests and both skill validators passed. Independent Standards and Spec rechecks found no remaining actionable issue. The package is published; native publication remains blocked by the locked Mac and is last verified at 0.1.8.


Published release commit: `97f6b7cbec0c072df4318b65a55a9436c13c5a7d`. Source ZIP SHA-256: `4433db00c2b6b2dad084fac47de7a7cbb5ddf30db22909e2f13d5620b9b93b5c`. Bundle SHA-256: `fccecb0095bbb1f3454c0cafffe86e74b7bc4487e80df74782cb65ef03f9a266`. All six release assets are published. Anonymous verification matched all 51 ZIP files to the tag and both public bundle assets to the local outputs. Compiling from a fresh extraction with Python 3.11 produced byte-identical template JSON and checksum.

Native app access was attempted again during this follow-up and reported the Mac locked. No native v0.2.1 publication or clean-import test is claimed. GitHub Actions run `36356824070` again started no steps because the account is locked by a billing issue.
