# PF-CINEMA-001 — The Beast Within: $0 Local Cinematic Pilot

**Status:** PLANNED / SOURCE-RECONCILIATION-REQUIRED  
**Campaign:** DJ RezrXtion launch execution  
**Budget:** $0  
**Baseline:** `main` at `6c90c1f0b15b245179da4644fbc8f1135f8ba86e` (observed 2026-10-24)  
**Tracking issue:** https://github.com/justinbusiness461-lab/pulseforge-songforge/issues/1

## Decision

Prioritize the first evidence-backed cinematic music-video production path for **The Beast Within**. Do not add broad new architecture until the existing source can launch reproducibly and a local audiovisual proof exists.

## Current truth and evidence ceiling

The current README describes PulseForge SongForge as a local-first multi-track Score Graph studio, and explicitly says it is not an autonomous AI music-video product or finished 3D film studio. Existing repository tools include OTIO structure validation and SHA-256 content-identity checking.

The current Git tree contains `tools/certify_otio.py` and `tools/certify_integrity.py`, but does not contain the documented `tools/studio_server.py` path, despite README/INSTALL launch instructions referencing it. The current release ZIP has not yet been inspected in this execution, and no clean-install launch was reproduced. This is an unresolved source/package/documentation mismatch, not proof that every release artifact is broken.

No verified **The Beast Within** audio master or authoritative lyric/timing file was located in the current repository/source search. Audio, lyrics, rights, tempo, section boundaries, and lyric alignment remain **UNKNOWN** until supported by actual source evidence.

## Canonical DJ RezrXtion constraints

- World: **The Afterpulse**.
- Primary mark: **Resurrection Crest**. Minimal mark: **Afterpulse Sigil**.
- Performance identity: smooth obsidian mask with no eyes, mouth, or openings; electric-blue pulse lines and Spark Node.
- Palette: black, electric blue, white/silver; restrained gold only when justified by the story.
- Visual grammar: silence/void → pulse → glitch/fracture → spark → storm/return.
- Mask states must remain coherent: Prime, Pulse, Storm, Void, Sparkbearer, Ascension. Sparkbearer/fatherhood symbolism stays rare and emotionally earned.
- Avoid generic AI montage, inconsistent mask/crest geometry, arbitrary neon, and effects unrelated to actual song structure.
- Do not infer the song's story, lyric timestamps, BPM, or emotional turns from the title. Build the treatment from the approved master and lyrics once supplied.

## Execution gates

### G0 — Reconcile executable truth

1. Inspect the exact current source tree and release ZIP contents.
2. Identify the intended executable entrypoint and reconcile README, INSTALL, packaging, and release contents.
3. Reproduce a clean local install/start, recording commands, environment, exit codes, and observed behavior.
4. Do not claim the app launches until reproduced.

**Pass evidence:** pinned source SHA; entrypoint and dependency inventory; clean-install log; actual launch result; docs/package mismatch either resolved or explicitly bounded.

### G1 — Immutable audio ingest and zero-spend execution

1. Obtain the approved original **The Beast Within** master; obtain lyrics or section notes if available.
2. Record provenance, rights status, file metadata, and SHA-256. Preserve the master read-only.
3. Establish offline/no-paid-provider execution; zero external generation calls, credits, and charges.
4. Build a sample-index-authoritative event map with confidence/method labels. Uncertain lyric timing remains uncertain.

**Pass evidence:** audio manifest, source digest, timing report, offline/egress evidence, and honest unsupported-capability outcomes.

### G2 — First real cinematic proof

Render a 10–20 second proof segment from the actual song using a locally executable procedural/3D renderer. A storyboard, still-image montage, waveform visualizer, or planned render is not equivalent.

- Initial target: 24 FPS, 720p; record actual renderer/version, settings, timebase, and performance.
- Produce physical frames and a playable MP4 with the real master audio.
- Verify 100% QA-passed frame coverage across the scheduled proof interval, decodability, duration, timing, and audio continuity/identity method.
- Preserve renderer logs, source/audio hashes, frame coverage JSON, QA findings, and output digests.
- If local execution cannot produce the artifact, report the exact blocker as `BLOCKED_UNSUPPORTED`; do not invent progress.

**Pass evidence:** the actual MP4 and frame set, machine-readable coverage, audio verification, renderer trace, and technical certificate referencing existing files.

### G3 — Song-grounded story and character expansion

Only after G2 passes:
1. Approve a treatment based on the actual song and canon.
2. Compile inspectable scene/shot manifests bound to implemented actions.
3. Prove consistent character identity, camera movement, lighting transitions, and supported animation.
4. Fault-inject a shot defect, detect it, and repair only the affected dependency cone.
5. Track technical certification separately from creative approval.

A short proof does not certify the full-length film. Full-song production remains **INCOMPLETE** until the intended whole-song master has physically rendered and passed QA.

## No-spend and repository constraints

- Budget remains $0. Do not use paid generation APIs, per-video credits, or automatically spending providers.
- GitHub Actions are not required for this campaign.
- Prefer existing qualified mechanisms; do not copy donor code without source, license, commit, and runtime qualification.
- Parallelize independent analysis; serialize canonical WorldState, approved shot replacement, and master publication.
- Keep planning progress, QA-passed asset progress, and certified timeline-frame coverage separate.
- A technical pass and creative approval are distinct decisions.

## Immediate next actions

1. Reconcile the missing documented server entrypoint against the current source tree and release ZIP.
2. Locate/provide the approved **The Beast Within** master and any authoritative lyrics.
3. Execute G0, then G1, then render and independently inspect G2.
4. Expand to character-driven narrative only after the first proof passes.

## Acceptance checklist

- [ ] Clean launch reproduced from a pinned source tree.
- [ ] Master provenance, rights status, immutable source hash, and timing confidence recorded.
- [ ] Zero paid-provider calls/credits; offline policy evidenced.
- [ ] Physical frames exist and scheduled proof coverage is 100%.
- [ ] Real master audio is present; sync/continuity verification method is recorded.
- [ ] MP4 decodes and is playable; metadata and digest recorded.
- [ ] Canon and continuity review completed.
- [ ] Technical result and creative approval are reported separately.
- [ ] Full-length status remains INCOMPLETE until the entire intended film is physically rendered and certified.

**Completion law:** no claim of cinematic completion without actual pixels, the approved song master, measured synchronization, physical QA, provenance, and a certificate tied to real artifacts.
