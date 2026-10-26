WORK A ~ READY

# Mission 040 — Sound Forge 2.19.0 owner candidate

## Outcome and authority

**SOUND_FORGE_M040_CANDIDATE = PASS — bounded owner/source/security/provenance/headless-audio scope.** Independent B/C/D qualification and browser product qualification remain open. No global Sound Forge/product, lyric, music-quality, mastering or cinema certificate is issued.

Live baseline authenticated: `justinbusiness461-lab/pulseforge-songforge` main `6c90c1f0b15b245179da4644fbc8f1135f8ba86e`. Open PR #2 was a separate draft cinema brief; it was not touched. No AGENTS.md existed in the retrieved source tree. No `dj_rezrxtion` production inputs were changed.

The loose baseline could not start its documented server: `tools/studio_server.py`, `tools/vocal_lab.py`, `app-cinema.js` and other full application files were absent. Its **committed** `SoundForge-Studio-Release-v2.18.zip` contained them. `reconciliation.json` records loose/archive hashes and presence for every restored file. This candidate conserves that committed implementation as loose source rather than applying proposed Phase 8/9 overwrite snippets. Archive restoration accounts for most of the source diff.

## Repairs and physical evidence

- **PF-SOUND-001:** loopback-only bind; exact parsed scheme/host/port and Host admission; fresh per-process capability for every mutation; consistent exact-origin OPTIONS/CORS; private export namespace excluded from static serving; bounded request allocation and strict filename/subdirectory validation. Missing/foreign/deceptive origins and stale tokens reject before mutation. Local filesystem compromise is outside this HTTP boundary; LAN deployment is not admitted.
- **PF-SOUND-002:** immutable SHA-256 objects; ledger binds objects rather than aliases; friendly aliases are durable JSON pointers. Unique temporary writes, file/directory fsync and process-wide advisory export locking preserve concurrent histories. Corrupt existing ledger/object fails closed. This is a local single-host persistence contract, not distributed or multi-user authority.
- **PF-SOUND-003:** release.json + package.json agree on **2.19.0**. Exact committed-source packager binds Git source SHA, file inventory, packager/certifier hashes, runtime contract, canonical package filename and ZIP digest sidecar. Source and package digests are separate to avoid self-reference. Historical v2.16/v2.18 ZIPs remain historical inputs, not the current release.
- **PF-SOUND-004/005:** `certify_mix.py` explicitly measures PCM16 sample peaks; dBFS uses `20*log10(amplitude)`. No inter-sample/true-peak or LUFS claim. Half-scale, full-scale and silence tests pass.
- **Editable generation:** existing symbolic compiler and offline WAV renderer produce a six-section, 50-second original instrumental study with 0.5s export tail. Original and edited WAVs each have 2,227,050 stereo sample frames at 44.1kHz. One Turn-section bass transposition leaves all other symbolic regions identical. Actual sample differences remain within the edit and declared 100ms release tail. A separate process reopens the saved edited project and reproduces its WAV SHA-256 exactly.
- `ProductionTimeline.json` derives from exact saved SongSpec revision. Render receipt binds symbolic state, timeline, decoded PCM and renderer source hashes. Actual projects and WAVs were also committed through the secured HTTP writer, rehashed, and projects reopened after server restart.

## Fresh verification

- **12/12** unit tests: exact/malformed origins, traversal, A/B history, tampered object, corrupt ledger, four concurrent writers, and independent dBFS reference values.
- **40/40** real HTTP/restart checks: trusted/unauthorized mutation, missing/wrong/stale capability, Host rebinding, foreign/missing/deceptive origin, wrong port, OPTIONS consistency, private/public GET, oversized declared request, historical A/B verification, actual project/WAV exports and project reopening.
- Exact committed-archive baseline reproducer: foreign unauthorized write HTTP 200; changed same-alias export makes old integrity verifier exit 1. Corrected contract is green. The earlier helper-unit red log records missing new seams; `baseline-red.json` is the actual old-behavior reproduction.
- JS syntax and Python compilation pass. Both actual generated WAVs decode through FFmpeg with exit 0. Logs, source states, WAV bytes and receipts are retained in this repository.

## Explicit ceilings / first remaining product blocker

**Browser/PWA journey is unverified.** Chromium was absent; attempted acquisition failed on an invalid downloaded archive. Headless web-audio-engine@0.13.4 is pinned as a dev execution dependency, not represented as Chrome/Web Audio playback. No perceptual listening or user interaction was claimed.

The existing offline renderer differs from the live DSP path. Its output has two identical channels (correlation 1), so spatial stereo, BBD, mix-bus parity and live/offline sonic equivalence remain unearned. No new synth/effect was introduced to hide this gap. The candidate is a modest instrumental proof, not Suno-quality music or an artist-approved song.

Formant vocals remain guide synthesis; numpy is declared separately, torch/ONNX/weights are optional and unqualified. The broadcast route remains an honestly labeled eight-second development proxy, now routed through the immutable export owner. OTIO remains structural/preview interchange; no NLE compatibility promotion. Lyric extraction/alignment/correction revision intelligence is **not implemented or certified by this repair**; existing symbolic phoneme mapping is not transcription.

Browser localStorage is still a draft/cache path; this turn proves explicit exported snapshots and immutable project reopen, not a unified browser/server autosave or durable background render job. Existing legacy mutable export ledgers are not silently migrated or newly certified. POSIX fsync and flock are the declared platform contract; power-loss and Windows execution were not tested.

## Forge and next owners

**ADAPT** committed v2.18 baseline; **ADOPT** exact broker admission and immutable export identity; **HOLD** browser/product/music-quality/lyric/master gates; **REJECT** giant unqualified snippets and competing runtime authority.

B: independently qualify this branch, verify packaged source identity and readback; merge only through rightful ownership. C: independently decode/measure/reopen the exact retained candidate. D: attack security/provenance and listen, reporting technical and musical verdicts separately. A does not merge its own PR.

Repository-first retention is exercised: source, tests, actual audio, symbolic states, receipts and reproducible commands are in this branch. Generated release packages are reproducible with `python3 package_project.py`; its retained receipt binds the package's source commit. No Library upload is used. Cinema stays background and frozen.

Human action: NONE.

WORK A ~ READY
