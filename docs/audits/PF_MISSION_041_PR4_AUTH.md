# Mission 041 — PR #4 independent source authentication

**Role:** Work B / Runnable-style (read-only qualification)
**PR:** https://github.com/justinbusiness461-lab/pulseforge-songforge/pull/4
**PR4_HEAD_SHA:** `fcab64b18f325cd718e0ddb76f3d1ba72645fdd2`
**Branch:** `work-a/m040-sound-truth`
**Base:** main `6c90c1f0b15b245179da4644fbc8f1135f8ba86e`
**State:** open, mergeable (not merged by this lane)

## Conflict resolution

| Statement | Verdict |
|-----------|--------|
| Full studio_server still ZIP/local only | **FALSE for PR #4 head** |
| main still stubs | **TRUE for main** — do not qualify main |
| PR #4 has remote executable source | **TRUE** |

**Do not retest old v2.18 ZIP as the candidate.** Use PR #4 head.

## Required files at PR4 head (REMOTE_PRESENT)

| PATH | BYTE_SIZE | GIT_BLOB_SHA (prefix) | REMOTE_PRESENT |
|------|-----------|----------------------|----------------|
| tools/studio_server.py | 16209 | 4aaa98d7… | **YES** |
| tools/test_harness.py | 5165 | a57db8f8… | **YES** |
| tools/vocal_lab.py | 17510 | 78582d09… | **YES** |
| tools/certify_integrity.py | 2659 | 23094900… | **YES** |
| tools/certify_otio.py | 4467 | 6e715494… | **YES** |
| tools/certify_mix.py | 2048 | b3999968… | **YES** |
| app-core.js | 37016 | 2e9d8ea6… | **YES** (full, not main stub) |
| app-ui.js | 34392 | 87748684… | **YES** |
| app-cinema.js | 8987 | 3ffe39fe… | **YES** |
| service-worker.js | 1368 | 53316812… | **YES** |
| manifest.json | 973 | 46522a6d… | **YES** |
| package_project.py | 2809 | d82fb6b0… | **YES** |
| release.json | 371 | 3e8ce0c7… | **YES** version **2.19.0** |
| tests/test_m040.py | 3040 | a2b769b6… | **YES** |

## Music artifacts on PR (remote)

| Artifact | Size | Notes |
|----------|------|-------|
| evidence/m040/music/initial.wav | 8908244 | 50.5s claim |
| evidence/m040/music/edited.wav | 8908244 | section edit |
| SongSpec.initial/edited.json | ~32k each | symbolic |
| ProductionTimeline.json | 32453 | |
| cold-reopen.json | matches edited sha256 | `796b0432…` matches_prior true |
| render-receipt.json | frames 2227050 @ 44.1kHz dual channel | |

## Capability classification (PR #4)

| Capability | Status |
|------------|--------|
| SECURE_BROKER | COMMITTED + owner evidence (12 unit + 40 HTTP) — **B must re-run independently** |
| IMMUTABLE_EXPORTS | COMMITTED + evidence |
| RELEASE_IDENTITY | COMMITTED 2.19.0 (not mixed 2.5/2.18 labels) |
| SAMPLE_PEAK / dBFS | certify_mix.py present; claims PCM peak + 20*log10 |
| SONGSPEC_GENERATION | COMMITTED + WAVs |
| SECTION_EDIT | COMMITTED evidence |
| PROJECT_REOPEN | cold-reopen matches — **C must physical re-decode** |
| LYRIC_TIMELINE | **NARRATIVE_ONLY / absent** |
| BBD / ONNX / TAURI | HOLD / empty weights |

## Gates (this authentication only)

| Gate | Result |
|------|--------|
| STUDIO_SOURCE_COMPLETE (PR #4 tree) | **PASS** — required executables remote |
| STUDIO_SECURITY_PASS | **PENDING independent retest** (owner claims green) |
| STUDIO_PROVENANCE_PASS | **PENDING independent retest** |
| SOUND_FORGE_PROJECT_AUTHORITY_PASS | **PENDING** (exports proven; unified browser/server authority still ceiling) |
| MUSIC_GENERATION_PASS | **BOUNDED PENDING C/D** |
| Merge | **NOT performed by this lane** |

## WORKFLOW_READY

**YES** for clean-checkout qualification of `fcab64b18f325cd718e0ddb76f3d1ba72645fdd2`.

## Explicit non-claims (from HANDOFF, accepted)

- Not browser/PWA certified
- Dual mono output (correlation 1)
- No lyric intelligence
- No product candidate
- No cinema change

## Next owners

1. **B** re-run security/provenance probes on checkout of PR head (not trust A logs alone).
2. **C** FFmpeg decode of exact `initial.wav` / `edited.wav` + metrics.
3. **D** adversarial origin + listen.
4. Merge only after B green → freeze SHA.
5. Then A lyric timeline against frozen audio.
