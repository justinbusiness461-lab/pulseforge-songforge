# PulseForge™ / S.A.R.A. Sound Forge™ — Chat D Mission 042 Frozen Successor Audit

**Campaign:** PF-COMPLETION-001  
**Mission:** 042  
**Role:** Chat D / adversarial verifier  
**Target freeze:** `7c92fe7a39d6b4209be510d02781adb6a1ef4182`  
**Release:** `2.19.1`  
**Date:** 2026-10-26 America/New_York

## Final verdict

`TECHNICAL_AUDIO_VERDICT = PASS — BOUNDED M042 LOCAL-HOST CANDIDATE`

`MUSICAL_QUALITY_ASSESSMENT = 5.3 / 10 — technically valid, artistically primitive / highly procedural`

The technical PASS is independent of artistic taste. It covers the exact frozen successor, its loopback broker, immutable export/provenance path, durable project authority, retained generated WAVs, and the adversarial vectors executed in this audit.

This does **not** promote:
- `AUDIO_MASTER_PASS`
- `SOUND_FORGE_PRODUCT_CANDIDATE`
- `LYRIC_INTELLIGENCE_PASS`
- browser/PWA certification
- professional stereo/mastering quality

## Freeze authentication

Work B's retained receipt identifies:

- `PR4_QUALIFIED = PASS — bounded integration`
- `STUDIO_SOURCE_COMPLETE = PASS`
- `STUDIO_SECURITY_PASS = PASS — loopback contract tested`
- `STUDIO_PROVENANCE_PASS = PASS — immutable export history`
- `SOUND_FORGE_PROJECT_AUTHORITY_PASS = PASS — bounded POSIX local-host scope`
- `MERGED_SHA = 7c92fe7a39d6b4209be510d02781adb6a1ef4182`
- `SOUND_FORGE_M042_FREEZE_SHA = 7c92fe7a39d6b4209be510d02781adb6a1ef4182`
- `RELEASE_VERSION = 2.19.1`

Chat D independently reconstructed required files directly from that exact frozen SHA in an isolated runtime.

## Independent baseline execution

Fresh frozen execution:

- Python: `3.10.12`
- unit tests: `21/21 PASS`
- `tools/m040_http_probe.py`: `40/40 PASS`
- `tools/m042_project_probe.py`: `15/15 PASS`

An initial partial reconstruction produced one missing-import error and server-start failures. Those were correctly classified as an incomplete isolated test surface; after restoring the exact required frozen files, the full commands passed.

## Security regression — PASS

Independent Chat D adversarial results:

| Vector | Result |
|---|---|
| foreign `evil.example` Origin | `403` |
| deceptive localhost-like hostname | `403` |
| wrong port | `403` |
| malformed Origin | `403` |
| missing Origin | `403` |
| missing capability | `403` |
| traversal in filename | `400` |
| traversal in subdirectory | `400` |

### Mutation replay

The same authorized write was replayed twice.

- first status: `200`
- second status: `200`
- digest identical both times
- immutable object path identical both times

Result: replay is content-idempotent at the object layer. It does not create a second conflicting object identity or corrupt alias history.

`PF-SOUND-001 SUCCESSOR REGRESSION = PASS`

## Provenance regression — PASS

Independent A/B history and tamper behavior:

1. immutable A exported
2. project R1 bound to A
3. immutable B exported through the same logical project flow
4. R2 bound to B
5. historical R1 remained retrievable
6. immutable A object was physically tampered
7. historical project open failed closed with HTTP `400`
8. `tools/certify_integrity.py` exited `1`
9. verifier reported a digest mismatch

`PF-SOUND-002 SUCCESSOR REGRESSION = PASS`

## Project-authority adversary — PASS

Independent attacks produced:

- stale R1 save after R2: `409`
- R1 revision file mtime forced newer than R2: manifest still opened R2
- historical R1 retrieval: `200`, exact R1
- corrupt friendly output alias: current project still reopened R2
- absent friendly output alias: current project still reopened R2
- orphan output artifact exported after R2: excluded from R2 authority
- R2 output binding remained exact
- fresh-process project probe with no browser cache: `15/15 PASS`

This establishes the intended authority law at the tested scope:

`ProjectManifest.currentRevisionId`
→ exact immutable `ProjectRevision`
→ exact SongSpec / ProductionTimeline
→ bound immutable output digests

Friendly aliases and cache are non-authoritative.

`SOUND_FORGE_PROJECT_AUTHORITY_ADVERSARY = PASS`

## Retained generated audio — direct physical measurements

### initial.wav

- SHA-256: `512bdfc02b2aa18476d3b32fac9898724d1a8c4255f01c5599decd8886050858`
- codec: PCM signed 16-bit little-endian
- sample rate: `44,100 Hz`
- channels: `2`
- decoded frames: `2,227,050`
- duration: `50.500000 s`
- sample peak: approximately `-9.56 dBFS`
- LUFS-I: approximately `-28.34`
- LRA: approximately `3.50 LU`
- DC offset: approximately `+0.000113`
- exact L/R correlation: `1.0`
- exact dual mono: `TRUE`
- silence ≥0.5s below -55 dB: final `0.626916 s` tail only
- decode: clean

### edited.wav

- SHA-256: `796b0432264aaac2c5d34f64c650a7037d841d86d910cfd74798c55a3d45ccee`
- codec: PCM signed 16-bit little-endian
- sample rate: `44,100 Hz`
- channels: `2`
- decoded frames: `2,227,050`
- duration: `50.500000 s`
- sample peak: approximately `-9.56 dBFS`
- LUFS-I: approximately `-28.39`
- LRA: approximately `3.50 LU`
- DC offset: approximately `+0.000112`
- exact L/R correlation: `1.0`
- exact dual mono: `TRUE`
- silence ≥0.5s below -55 dB: final `0.626916 s` tail only
- decode: clean

The WAVs are healthy technical artifacts. They are **not mastered** and do not provide stereo image.

## Edit preservation — PASS at declared contract

Declared form at 96 BPM, E minor:

1. Opening — 0–5s
2. Statement — 5–15s
3. Refrain — 15–25s
4. Turn — 25–35s
5. Refrain return — 35–45s
6. Closing — 45–50.5s

Actual PCM difference:

- first changed frame: `1,102,506`
- first changed time: `25.000136 s`
- last changed frame: `1,544,556`
- last changed time: `35.023946 s`
- changed sample-value fraction: ~`19.76%`

The edited region therefore starts exactly at the `Turn` boundary and extends only ~24 ms into the following section, remaining inside the declared 100 ms release tail.

Symbolic diff is limited to:

- revision metadata
- eight bass-note pitch changes in the intended section

Unrelated tracks remain symbolically unchanged.

`EDIT_PRESERVATION = PASS`

## Musical-quality assessment

### Important evidence ceiling

This environment allowed direct byte retrieval, decoding, signal measurement, source inspection, and structural comparison, but it did **not** provide a literal audio-listening channel to the model.

Therefore this is a **signal + arrangement + score-graph assessment**, not a claim of human-style audition.

### Scores

| Dimension | Score | Evidence |
|---|---:|---|
| Structure | 7/10 | clear six-section intro/verse/chorus/verse/chorus/outro form |
| Groove | 6/10 | stable 96 BPM event grid; technically coherent but pattern reuse is heavy |
| Tonal coherence | 8/10 | declared E minor; bass/pad/lead note material is internally coherent |
| Transitions | 5/10 | section boundaries are clean, but arrangement contrast is limited |
| Repetition control | 3/10 | body drum pattern repeats exactly; verse/turn and chorus/return reuse the same event signatures |
| Dynamics | 4/10 | section RMS varies by only roughly 0.5 dB; LRA ~3.5 LU |
| Mix / headroom | 6/10 | clean, unclipped, ample headroom; very quiet for release and not mastered |
| Stereo interest | 1/10 | exact dual mono |
| Procedural subtlety | 3/10 | small event vocabulary and repeated patterns make procedural construction obvious |
| Edit integration | 8/10 | one-section bass edit is precisely localized and technically integrated |
| Emotional / musical usefulness | 5/10 | useful as an editable generated instrumental foundation, not yet a compelling finished record |

**Overall bounded musical-quality score: `5.3 / 10`.**

### Musical conclusion

The retained song is **technically valid but artistically primitive**.

It has a coherent form, coherent key center, clean timing, clean section-local editing, and no evidence of broken transitions, clipping, silence faults, or tonal collapse. The main limitations are not correctness defects; they are musical maturity limitations:

- exact dual mono
- very low finished loudness
- narrow dynamic range
- repeated body drum patterns
- repeated verse/chorus arrangement signatures
- limited orchestration evolution
- obvious procedural construction

The one-section edit is believable as a controlled variation because it changes the intended bass material and remains localized to the target section plus a short release tail.

## Layered promotion consequence

Earned from Chat D at the exact M042 freeze:

- `SOUND_FORGE_SECURITY_PASS = PASS`
- `SOUND_FORGE_PROVENANCE_PASS = PASS`
- `SOUND_FORGE_PROJECT_AUTHORITY_PASS = PASS`
- `MUSIC_GENERATION_PASS = PASS — bounded real editable artifact`
- `PROJECT_RECOVERY_PASS = PASS — bounded local-host/process-restart scope`

Still held:

- `AUDIO_MASTER_PASS = HOLD`
- `LYRIC_INTELLIGENCE_PASS = NOT STARTED BY LAW`
- `SOUND_FORGE_PRODUCT_CANDIDATE = HOLD`

## Next lawful consequence

Mission 042's technical Chat-D cone is closed.

The next intelligence boundary is Lyric Intelligence only after the team accepts the C/D physical chain:

`AudioMaster digest`
→ `LyricTimeline R1`
→ correction
→ `LyricTimeline R2(parent=R1)`
→ ProjectRevision advance
→ restart
→ R1 retained
→ R2 authoritative

No DSP detour. No synth detour. No cinema expansion.
