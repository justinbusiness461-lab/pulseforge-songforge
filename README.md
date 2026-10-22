# PulseForge SongForge (S.A.R.A. Sound Forge)

Local-first multi-track Score Graph studio (PWA).

**Repo:** https://github.com/justinbusiness461-lab/pulseforge-songforge  
**Related (keep separate):** private `song_forge` backend capability core

## Status (PF-COMPLETION-004)

Verified local workstation path: prompt → Score Graph → Play → OTIO/WAV export → `certify_otio` + integrity ledger.

**Not** an autonomous AI music-video product. Cinema viewport is armature/viseme preview only.

## Quick start

```bash
python3 tools/studio_server.py
# open http://localhost:8765
```

See `INSTALL.md` for the full journey and integrity ceiling.

## Open on phone

https://cdn.jsdelivr.net/gh/justinbusiness461-lab/pulseforge-songforge@main/index.html

Then **Add to Home Screen**.

## Tools

| Tool | Role |
|------|------|
| `tools/studio_server.py` | Local broker, atomic writes, integrity ledger |
| `tools/vocal_lab.py` | Formant / production-torch / ONNX-slot vocals |
| `tools/certify_otio.py` | Timeline.1 structural check |
| `tools/certify_integrity.py` | Ledger SHA-256 content-identity |
| `package_project.py` | Provenance zip |

## Commercial

Stage 1 candidate offer: see `COMMERCIAL_OFFER_STAGE1.md` (hypotheses only).

## Evidence ceiling

Local Web Audio + Python broker. Not neural SVS parity without your ONNX weights. Not finished 3D film.
