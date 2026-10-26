# Clean install — 2.19.1 M042 candidate

Python 3.10+ on POSIX with directory fsync is required for the local broker. A modern browser supplies Web Audio for the UI. No account or hosted inference service is required.

```
python3 tools/studio_server.py
```

Open **http://127.0.0.1:8765** on the same machine. The broker binds loopback only. A phone cannot reach another machine's localhost; LAN or hosted deployment is not qualified by this candidate.

The served HTML supplies a short-lived, per-process capability to same-origin writes. Mutation requires exact scheme/host/port, allowed Host, and that capability. Restart rotates it; reload online after restart. Static-file hosting can offer browser downloads but does not earn broker durability. Friendly export aliases point to immutable objects; the ledger binds those objects. Private workspace files are not static HTTP assets.

Optional local vocal lab requires numpy (`python3 -m pip install -r requirements-vocal.txt`). Torch and ONNX runtime/weights remain optional and unqualified here. The formant path is not trained neural singing.

Reproduce owner checks:

```
python3 -m unittest discover -s tests -v
python3 tools/m040_http_probe.py
npm ci --ignore-scripts
npm run probe:audio
python3 tools/certify_mix.py evidence/m040/music/initial.wav
python3 tools/certify_integrity.py
python3 package_project.py
```

`probe:audio` uses pinned web-audio-engine 0.13.4 to execute the existing offline export function headlessly. This is not browser playback. `--reopen` runs a separate process from the saved project. The audio probe intentionally regenerates only its isolated evidence fixture, not imported masters.

Generated runtime exports belong to workspace/studio_exports; tests/probes use disposable export names. Use a fresh checkout for reproduction. The package requires committed source; generated archives and sidecars are in dist/. Keep the sidecar with the ZIP to bind version, source SHA, inventory, packager, certifiers and package hash. Evidence is retained through this repository, not ChatGPT Library.

## Durable projects (M042)

Save project creates an immutable revision behind a stable project ID. Keep that ID; Open project resolves its durable current revision, even with browser storage cleared. New project explicitly forks a new identity. Browser storage caches only an address. Stale saves fail with HTTP 409; reopen before applying another edit. WAV export captures its input snapshot, persists its output object, and commits one revision binding both. An interrupted pre-commit render may leave an unreferenced object; it never advances project authority.

Project data lives under workspace/studio_exports/projects/<projectId>/ProjectManifest.json, with immutable revision records under revisions/. Referenced SongSpecs, derived timelines and output bytes live in the existing content-addressed object store. Do not edit these files manually. No new authority or model is added for lyrics in this release.

Run `python3 tools/m042_project_probe.py` for the complete actual-media R1/R2/restart discriminator, and `node tools/m042_ui_probe.cjs` for exact UI authority functions against HTTP. The latter uses minimal DOM adapters in Node; it is not browser/PWA certification.
