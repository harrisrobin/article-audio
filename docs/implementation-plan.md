# Article audio implementation plan

Goal: deliver an installable, credential-aware narration CLI and Grok Bot skill.
Spec: design.md. Execute in this isolated package directory under the user's approved scope.

- [x] Credential lifecycle: test private persistent storage, redacted status, strict imports, and a one-time local form; implement credentials.py and onboarding.py.
- [x] Gemini and audio: test exact text coverage, request separation, WAV/PCM decoding, refusal/truncation and retry behavior; implement gemini.py and audio.py.
- [x] Resumable CLI: test failed-run recovery and caching, implement pipeline.py and cli.py with plan, doctor, generate, publish and auth commands.
- [x] R2: test upload, remote verification, signing and failure behavior through the boto3 boundary; implement storage.py.
- [x] Distribution: write setup.sh, a concise SKILL.md, profile and onboarding instructions, MIT license, CI and release packaging.
- [x] Verify: run pytest and lint, generate real Gemini narration using the supplied key outside the repo, decode/probe audio, re-run to prove caching, and build/inspect the distributable for secrets.

Runtime handoff: test the native Grok template, credential-entry experience, and a real R2 bucket. See verification.md for the precise evidence and remaining checks.
