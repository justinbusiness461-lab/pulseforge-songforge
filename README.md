# PulseForge SongForge / S.A.R.A. Sound Forge

**Mobile-first · offline · zero-dependency** chat-led generative music studio (local Web Audio + Python broker).

**Current release:** 2.20.0 · schema `pulseforge.songforge.skeleton.v2.20`

## Quick start
```bash
cd pulseforge-songforge
python3 tools/studio_server.py
# open http://localhost:8765
```
Phone (same Wi‑Fi): `http://<your-ip>:8765` · or Add to Home Screen (PWA).

CDN (may lag):  
https://cdn.jsdelivr.net/gh/justinbusiness461-lab/pulseforge-songforge@main/index.html

## Core journey (chat-led)
1. **Prompt** in the Session composer (optional lyrics)  
2. **Generate** → integer-tick SongSpec (TPQ=960), studio reply with BPM/key/genre/seed/song_id/schema  
3. **Vary** (new seed) · **Extend** (append section) · **Remix** (keep lyrics, new arrangement)  
4. One-tap **Play** · edit mixer / matrix / section lyrics  
5. **Save project** (durable M042 revision via studio server)  
6. Export **WAV** / **Cinema Graph** / **OTIO** · certify  
7. Session restores from `localStorage` (`sf_chat_session_v220`) including transcript + last Score Graph

## What ships
| Phase | Capability |
|-------|------------|
| 1 | NL prompt → integer-tick SongSpec, 16-step matrix, mixer |
| 2 | Detuned dual-saw bass, dual-op FM pads/leads, Karplus-Strong plucks |
| 3 | Lyric → phoneme timeline, formant vocals (male/female), MEG visemes |
| 4 | Asymmetric tape saturation + stereo BBD spatial delay |
| 5 | Content-addressed exports + project revision authority (M040/M042) |
| 6 | Arrangement change_ledger + deterministic seed/repro (`sf-<hex>`) |
| 7 | Chat-led create loop, trust chips, session continuity, undo checkpoints |

## Tests
```bash
python3 -m unittest discover -s tests -v
python3 tools/test_harness.py   # MEG → armature (seeds mock if needed)
```

## Evidence ceiling
Deterministic local Web Audio + rule compiler only.  
**Not** neural singing, **Not** Suno/Udio/ElevenLabs, **Not** hardware tape/BBD parity, **Not** certified 3D film.

See `GAP.md` for present vs missing with honesty ceilings.
