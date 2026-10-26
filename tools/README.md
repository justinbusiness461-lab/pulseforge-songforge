# SongForge tools

## Studio server (preferred launch)
```bash
# from package root
python3 tools/studio_server.py
# http://localhost:8765
# Exports → workspace/studio_exports/objects/<aa>/<sha256>
# Aliases → workspace/studio_exports/aliases/<subdir>/<file>.json
```
Writes require same-origin + `X-Studio-Capability` (injected into `index.html`).

## Deterministic compiler (Python mirror)
```bash
python3 tools/song_compiler.py "dark 102 BPM F# minor guitar"
```

## Certifiers
```bash
python3 tools/certify_otio.py [path...]
python3 tools/certify_integrity.py [ledger.json]
python3 tools/certify_mix.py path/to.wav
```

## Armature harness
```bash
cd tools && python3 test_harness.py [MusicEventGraph.json]
```

## Unit tests
```bash
python3 -m unittest discover -s tests -v
```
