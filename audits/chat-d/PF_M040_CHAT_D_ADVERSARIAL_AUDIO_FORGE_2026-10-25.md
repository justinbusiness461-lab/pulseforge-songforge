# PulseForge™ / S.A.R.A. Sound Forge™ — Chat D Adversarial Audio Forge

**Campaign:** PF-COMPLETION-001  
**Mission:** 040 — BREAK THE MUSIC CLAIM  
**Role:** Chat D / adversarial verifier  
**Mode:** Read-only product audit; evidence-only retention  
**Audit date:** 2026-10-25 America/New_York  
**Pre-audit product SHA:** `6c90c1f0b15b245179da4644fbc8f1135f8ba86e`  
**Bundle:** `SoundForge-Studio-Release-v2.18.zip`  
**Bundle SHA-256:** `a0ceb7dcdf3629ba8e86f4c644f68ccb9ac7d8a11becdd7bc3d2e25ac2be56cd`

## Verdict

`TECHNICAL_AUDIO_VERDICT = FAIL`

`MUSICAL_QUALITY_ASSESSMENT = INCONCLUSIVE_FOR_GENERATED_CANDIDATE`

The candidate has real mechanisms—deterministic prompt-to-SongSpec generation, bounded section edits, symbolic edit isolation, serialize/load round-trip, local synth paths, WAV/OTIO tooling, and integrity verification—but cannot promote because two P0 boundaries failed by direct execution.

## P0 — PF-SOUND-001 broker mutation authority: FAIL

Bundled `tools/studio_server.py` emits `Access-Control-Allow-Origin: *` and performs no exact Origin/capability/session authorization before mutation.

Physical POST matrix against `/api/write_production_file`:

| Attack | Observed |
|---|---|
| trusted `http://localhost:8765` | HTTP 200 / write |
| `https://evil.example` | **HTTP 200 / write** |
| `https://localhost.evil.example` | **HTTP 200 / write** |
| `http://localhost:9999` | **HTTP 200 / write** |
| malformed Origin | **HTTP 200 / write** |
| missing Origin | **HTTP 200 / write** |
| traversal strings | HTTP 200, sanitized into in-root path |
| replay | accepted repeatedly |

Oversized-body handling is also not bounded early: the handler reads the declared request body before applying the 50 MiB decoded-data gate. A destructive 50+ MiB probe was intentionally not sent.

**Disposition:** `SOUND_FORGE_SECURITY_PASS = FAIL`.

## P0 — PF-SOUND-002 historical ledger durability: FAIL

Physical sequence:

1. Write `AAA` to `masters/master.wav`.
2. Ledger records SHA-256 `cb1ad211...`.
3. Write `BBB` to the same friendly filename.
4. Ledger records SHA-256 `dcdb7041...` at the same absolute path.
5. Re-run `tools/certify_integrity.py`.

Result: historical A entry reports **DIGEST MISMATCH**; current B passes; verifier exits 1.

No immutable content-addressed object store was observed. Friendly filename and artifact identity are still coupled.

Required model remains:

`ArtifactVersion = immutable content`  
`FriendlyAlias = mutable pointer`  
`LedgerEntry = immutable artifact identity`

**Disposition:** `SOUND_FORGE_PROVENANCE_PASS = FAIL`.

## Source/release authority split

Live GitHub main before this audit receipt was `6c90c1f0...`.

Current main fetches showed:

- `app-core.js` present, ~7,952 chars
- `app-ui.js` present, ~6,823 chars
- `index.html` present, ~6,184 chars
- `service-worker.js` present
- `tools/certify_integrity.py` present
- `app-cinema.js` **absent / 404**
- `tools/studio_server.py` **absent / 404**

The v2.18 ZIP contains:

- `app-core.js` 36,957 bytes
- `app-ui.js` 34,151 bytes
- `index.html` 8,594 bytes
- `app-cinema.js` 8,987 bytes
- `tools/studio_server.py` 11,431 bytes
- `tools/vocal_lab.py` 17,510 bytes

README/INSTALL on main still instruct launching `python3 tools/studio_server.py`, despite that file being absent. Current `service-worker.js` precaches `./app-cinema.js` via `cache.addAll(ASSETS)`, while main lacks that asset.

**Disposition:** `SOUND_FORGE_SOURCE_COMPLETE = FAIL`; live main and release ZIP are not the same product tree.

## Symbolic edit isolation: PASS

Executed bundled `app-core.js` in a Node VM with seed 12345.

Target: verse `sec-7680`; operation: append one lyric token through `applySectionLyrics()`.

Observed:

- target section changed: yes
- every non-target section JSON-identical: yes
- drums unchanged: yes
- bass unchanged: yes
- pad unchanged: yes
- lead unchanged: yes
- pluck unchanged: yes
- vocal track changed: yes / expected
- vocal event count: 48 → 51

`serializeProject()` → JSON → `loadProjectObject()` preserved `projectFingerprint()`.

**Disposition:** project-graph section isolation PASS; symbolic serialize/load fingerprint PASS.

This does **not** establish cold browser recovery, repo-backed persistence, or unchanged-region rendered-audio identity.

## Rendered-audio determinism risk

Offline and realtime synthesis paths still use `Math.random()` for noise-based drum/string excitation. Therefore unchanged symbolic state does not imply sample-identical audio, and a one-section edit cannot yet prove unchanged audio regions remain identical/reused unless the contract explicitly permits nondeterministic re-synthesis.

**Disposition:** rendered edit-delta certification remains OPEN / not promotable.

## Lyric engine adversary

No implementation was found for the Mission 040 target fields:

- `LyricTimeline`
- `sourceAudioDigest`
- `revisionId`
- decoded sample start/end coordinates
- confidence
- correction history

Current vocal events contain tick, MIDI note, duration, phoneme, word and role. This is useful lyric-driven vocal generation, not yet evidence-bound imported-audio lyric truth.

Therefore:

- false lyrics in instrumental passage: NOT QUALIFIED
- repeated chorus identity: NOT QUALIFIED
- decoded-sample word timing: NOT IMPLEMENTED
- confidence calibration: NOT IMPLEMENTED
- durable correction revision: NOT IMPLEMENTED

**Disposition:** `LYRIC_INTELLIGENCE_PASS = FAIL / NOT IMPLEMENTED`.

## Existing harnesses

- `python3 tools/test_harness.py` → exit 0; armature/MEG fixture and pupil-spacing safety check pass.
- `python3 tools/certify_otio.py` on clean extracted release → exit 2, because no exported OTIO package existed.
- `python3 tools/certify_integrity.py` on clean extraction → exit 2, no ledger.
- after adversarial A→B overwrite → exit 1, historical digest mismatch.

## Reference media QA — BAD HABIT

This is **reference media only**, not proof of Sound Forge generation.

Supplied master SHA-256: `4de2da2c0b6ea12a0aee0b178e7aac59c67247bcda93d75ee5adbd6fe62e7e6d`.

Measured:

- MP3, 44.1 kHz, stereo
- 267.546122 s
- ~128 kb/s
- integrated loudness: -14.54 LUFS-I
- ffmpeg loudnorm true peak: -0.47 dBTP
- LRA: 6.80 LU
- overall sample peak approx -0.59 dBFS
- overall RMS approx -15.18 dBFS
- DC offset approx -0.000019
- NaNs 0 / Infs 0
- no >=0.5 s silence below -55 dB detected

## Mission 040 promotion matrix

| Gate | Verdict |
|---|---|
| SOUND_FORGE_SOURCE_COMPLETE | **FAIL** |
| SOUND_FORGE_SECURITY_PASS | **FAIL** |
| SOUND_FORGE_PROVENANCE_PASS | **FAIL** |
| SOUND_FORGE_RUNTIME_PASS | **PARTIAL** |
| MUSIC_GENERATION_PASS | **PARTIAL** |
| LYRIC_INTELLIGENCE_PASS | **FAIL / NOT IMPLEMENTED** |
| AUDIO_MASTER_PASS | **INCONCLUSIVE** |
| PROJECT_RECOVERY_PASS | **PARTIAL / symbolic PASS** |
| SOUND_FORGE_PRODUCT_CANDIDATE | **FAIL / NOT PROMOTABLE** |

## Smallest lawful remediation order

1. Fix PF-SOUND-001: exact scheme/host/port policy + mutation authority + consistent OPTIONS + pre-read request-size bound.
2. Fix PF-SOUND-002: immutable content-addressed objects; friendly aliases separate; ledger binds immutable objects.
3. Reconcile GitHub main vs release ZIP into one authoritative source tree.
4. Restore source-complete service-worker precache.
5. Define audio edit-isolation contract; seed random synthesis if sample determinism is required.
6. Implement authoritative, revisioned, sample-bound LyricTimeline.
7. Retain one generated WAV candidate in repo-owned evidence storage and run physical media QA.
8. Rerun this exact Chat D adversarial matrix.

## Final receipt

`TECHNICAL_AUDIO_VERDICT = FAIL`  
`MUSICAL_QUALITY_ASSESSMENT = INCONCLUSIVE_FOR_GENERATED_CANDIDATE`  
`PF-SOUND-001 = FAIL — PHYSICALLY REPRODUCED`  
`PF-SOUND-002 = FAIL — PHYSICALLY REPRODUCED`  
`PROJECT_GRAPH_SECTION_ISOLATION = PASS`  
`PROJECT_SERIALIZE_LOAD_FINGERPRINT = PASS`  
`LYRIC_INTELLIGENCE_PASS = FAIL / NOT IMPLEMENTED`  
`LIVE_MAIN_EQUALS_RELEASE_ZIP = FALSE`  
`SOUND_FORGE_PRODUCT_CANDIDATE = NOT PROMOTABLE`

Chat D made no product/source repair. This commit retains audit evidence only.
