# SongForge / S.A.R.A. Sound Forge — Gap Analysis vs North Star

**Release under audit:** 2.19.0 (local workstation surface)  
**Evidence date:** 2026-10-26 (America/New_York)  
**Scope:** music studio PWA + Python tools only. Full PulseForge 3D film / Blender R4 / RN mobile are out of scope.

## Present (with evidence)

| Capability | Evidence | Ceiling |
|---|---|---|
| Integer-tick Score Graph (TPQ=960) | `app-core.js` `TPQ`, `parsePrompt` section ticks; `tools/song_compiler.py` | Tick math is integer; playback uses float seconds conversion at render time |
| Deterministic prompt → SongSpec | `parsePrompt` + mulberry32/hashSeed; Python mirror + `tests/test_deterministic.py` | Rule-based genre/key/form — not LLM arrangement |
| Seed/repro identity | `generation_seed`, `song_id = sf-<hex(seed)>` (no wall-clock in id) | `created_at` ISO remains advisory wall-clock |
| Multi-track Web Audio + offline WAV | `playScore`, `renderMixBuffer`, WAV export | Offline render uses seeded noise for drums (not Math.random) |
| Formant vocals / phoneme timeline | `lyricsToPhonemes`, VOCAL track events, MEG PHONEME | Formant guides — **not** neural SVS / DiffSinger |
| OTIO-inspired Timeline.1 JSON | `exportOTIOPackage` + `certify_otio.py` | JSON OTIO-shaped package, not full OpenTimelineIO C++ fidelity |
| Content-addressed exports (PF-SOUND-002) | `studio_server.persist_export` → `objects/<aa>/<sha256>` + alias pointer | Ledger binds immutable object path; friendly names are aliases only |
| Project authority (M042) | `/api/projects/commit|open`, revision digests | Requires studio_server capability token from same origin |
| Append-only change ledger (arrangement) | `change_ledger[]` via `appendChangeLedger` on lyrics/role/mute/dup | Local in-ScoreGraph; digests are hashSeed (FNV-style), not SHA-256 |
| Integrity certifier | `certify_integrity.py` | Content identity only |
| Cinema MEG + armature preview | `exportMEG`, `app-cinema.js`, `armature_solver.py` | Viewport preview — not certified 3D film frames |
| Local studio launch | `python3 tools/studio_server.py` → `:8765` | Stdlib HTTP; origin+capability gated writes |

## Missing / partial (honest)

| Gap | Status | Notes |
|---|---|---|
| Neural singing (DiffSinger/ONNX) | Missing weights | `vocal_lab.py` falls back to deterministic formant/proxy |
| Hardware tape / BBD parity | Approximation only | Waveshaper + stereo delay — not analog circuit models |
| Immutable registry file (append-only FS) | Partial | Registry is rewritten atomically as a whole list; objects are immutable |
| Sample-identical live Web Audio vs offline | Not claimed | Live graph uses AudioContext scheduling; offline OfflineAudioContext |
| LyricTimeline sample-bound authority | Partial | Phonemes on ticks; no separate LyricTimeline digest gate (M042 rejects lyric digests) |
| Full OTIO XML / NLE round-trip | Not claimed | JSON Timeline.1 inspired package |
| React Native mobile app | Out of scope | ADR mobile doctrine is surface-contract reference only |
| PulseForge 8026-frame film / Blender R4 | Out of scope | NorthStar Control V2 film campaign separate |
| Zero-cloud “Broadcast” button | Proxy only | `dispatch_neural_compilation` writes local deterministic WAV+OTIO, not Suno/ElevenLabs |

## Highest-value closed this pass

1. Synced M040/M042 content-addressed studio server + project authority from upstream main  
2. Schema bump to `pulseforge.songforge.skeleton.v2.19` with deterministic `song_id`  
3. Arrangement `change_ledger` on section edits  
4. Deterministic unit suite: compiler, ticks, phonemes, WAV PCM identity, PF-SOUND-002  
5. Certifiers runnable against generated fixtures  

## Do not claim

- Neural singing quality or commercial SVS  
- Tape/BBD hardware parity  
- Final 3D music-video certification  
- Cloud generative API integration  
