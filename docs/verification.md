# Verification

Local evidence from 2026-09-27. This distinguishes implemented behavior from integrations that still need a real account test.

GitHub v0.1.7 is published; its native template update is being staged. Current published baseline: v0.1.6 at [the retained template](https://x.ai/bot/zBuR546KeAs5X0iwlXkxt), verified updated in place below. Older sections are historical evidence. The earlier `u9M4WdBafSgCyS3GNHKla` template is deprecated and still accessible; it is not a recommended installation path. GitHub v0.1.6 and native template version 3 are published and verified below; live account-recovery testing remains separate.

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
