# S.A.R.A. Sound Forge — Clean Install

## What this is
Local multi-track arrangement workstation (Web Audio + Python broker).
**Not** an autonomous AI music-video generator. **Not** commercial neural singing without your own ONNX weights.

## Requirements
- Python 3.10+ (stdlib only for server; optional: torch/numpy for production vocals)
- Modern browser (Chrome/Safari/Firefox) with Web Audio

## Launch
```bash
cd pulseforge-songforge
python3 tools/studio_server.py
# open http://localhost:8765
```

## Core journey
1. Enter prompt / lyrics → Compile
2. Play (synth + shelves + BBD + limiter)
3. Export OTIO / WAV / Vocal Lab as needed
4. `python3 tools/certify_otio.py`
5. `python3 tools/certify_integrity.py`

## Integrity ceiling
`certify_integrity.py` proves **content identity** (file bytes match ledger digest).
It does **not** prove registry immutability, artistic quality, or NLE compatibility.

## Exclusions
- Finished 3D cinematic music video
- Suno / ElevenLabs cloud generation
- DiffSinger neural SVS without local model files in `models/vocal/`
