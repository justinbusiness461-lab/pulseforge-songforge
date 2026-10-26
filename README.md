# PulseForge SongForge / S.A.R.A. Sound Forge

**Mobile-first · offline · zero-dependency** generative music studio (local Web Audio + Python broker).

**Current release:** 2.19.0 · schema `pulseforge.songforge.skeleton.v2.19`

## Quick start
```bash
cd pulseforge-songforge
python3 tools/studio_server.py
# open http://localhost:8765
```
Phone (same Wi‑Fi): `http://<your-ip>:8765` · or Add to Home Screen (PWA).

CDN (may lag):  
https://cdn.jsdelivr.net/gh/justinbusiness461-lab/pulseforge-songforge@main/index.html

## Core journey
1. Prompt → **Compile** (integer-tick SongSpec, TPQ=960)  
2. **Play** (drums / bass / FM / Karplus / formant vocals + shelves + BBD + limiter)  
3. **Save project** (durable M042 revision via studio server)  
4. Export **WAV** / **Cinema Graph** / **OTIO**  
5. Certify: `python3 tools/certify_otio.py` · `python3 tools/certify_integrity.py`

## What ships
| Phase | Capability |
|-------|------------|
| 1 | NL prompt → integer-tick SongSpec, 16-step matrix, mixer |
| 2 | Detuned dual-saw bass, dual-op FM pads/leads, Karplus-Strong plucks |
| 3 | Lyric → phoneme timeline, formant vocals (male/female), MEG visemes |
| 4 | Asymmetric tape saturation + stereo BBD spatial delay |
| 5 | Content-addressed exports + project revision authority (M040/M042) |
| 6 | Arrangement change_ledger + deterministic seed/repro (`sf-<hex>`) |

## Tests
```bash
python3 -m unittest discover -s tests -v
python3 tools/test_harness.py   # MEG → armature (seeds mock if needed)
```

## Evidence ceiling
Deterministic local Web Audio + rule compiler only.  
**Not** neural singing, **not** Suno/Udio/ElevenLabs, **not** hardware tape/BBD parity, **not** certified 3D film.

See `GAP.md` for present vs missing with honesty ceilings.
