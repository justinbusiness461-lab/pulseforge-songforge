# SongForge tools

## Armature solver + harness

```bash
cd tools
python3 test_harness.py                  # uses/seeds MusicEventGraph.json
python3 test_harness.py /path/to/meg.json
```

Maps MEG `PHONEME` / section `viseme_map.layout` tokens (A/E/O/U or ah/ee/oo/oh)
to jaw open, mouth scale, and lip pucker with pupil spacing safety checks.

## Tauri desktop shell

```bash
# Terminal 1 — serve the PWA
cd .. && python3 -m http.server 8765

# Terminal 2 — native shell (requires system WebView + tauri deps)
cd src-tauri
cargo tauri dev    # or: cargo build --release
```

Evidence ceiling: shell is an IPC/window host; DSP stays in WebView (`app-core.js`).


## Local studio server (silent disk writes)

```bash
# from package root
python3 tools/studio_server.py
# open http://localhost:8765
# Exports → workspace/studio_exports/<subdir>/
```

Order used by the UI: Tauri IPC → this broker POST → browser download.
