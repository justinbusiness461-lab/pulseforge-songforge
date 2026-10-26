WORK A ~ READY

# Mission 042 — Durable project authority candidate (2.19.1)

**PROJECT_AUTHORITY_CANDIDATE = PASS — owner qualification, bounded.** PR #4 update; B owns independent qualification, merge and freeze. No product/cinema promotion.

Parent candidate: `fcab64b18f325cd718e0ddb76f3d1ba72645fdd2`. Its full server/source is present; the old endpoint returns HTTP 404 for project commit. `baseline-red.json` reproduces this exact missing boundary using that Git commit. No DSP, instrument, lyric engine, Tauri, video or export-format expansion was made.

## Single authority

`workspace/studio_exports/projects/<projectId>/ProjectManifest.json` is the sole current-project pointer. It holds projectId, currentRevisionId and formatVersion. Immutable `revisions/<revisionId>.json` records bind parent, SongSpec digest, server-derived ProductionTimeline digest, nullable lyric digest (disabled this mission), source object digests, output artifact IDs, input/output bindings and creation time.

SongSpec and timeline bytes use the existing immutable content-addressed object owner. Revision IDs hash their complete core metadata. Reads verify revision identity, project ownership, referenced object hashes and committed ancestry. A prepared/orphan revision cannot masquerade as committed history. R1 remains retrievable after R2 becomes current.

Project commits require **expectedCurrentRevisionId**, compared after acquiring the per-project process lock. Stale proposals return HTTP 409. Two concurrent successors cannot both advance from R1. This is single-host/POSIX authority, not multi-user/cloud authorization.

Before pointer advancement: referenced bytes, file/directory namespace ancestry, immutable revision and its directory are synchronized; references are reread; then the manifest is atomically replaced, directory-synced and reread. Process-death before advancement leaves R1 current; process-death after advancement recovers valid R2. Power-loss was not simulated. Unreferenced pre-commit objects/revisions may remain; no deletion/GC is introduced.

## UI seam

Save project and Open project now call authenticated `/api/projects/commit` and `/api/projects/open`. A visible stable project-ID field allows reopening from a fresh client with no cache. localStorage contains only an address `<projectId, revisionId>`; the old full `sf_project` snapshot is ignored. Open resolves durable current state from the server. A changed project-ID selection requires Open before saving.

WAV export captures SongSpec, source bindings and expected revision before rendering, persists the WAV object, then commits one immutable revision binding that output and those inputs. A stale export may leave an unreferenced immutable WAV; it cannot silently replace current authority. Saving a draft without a render creates a metadata revision with no output binding; exporting afterward creates a new revision, never mutates the earlier one.

## Fresh evidence

- **21/21 unit tests**: the original 12 conservation tests plus project history/output chain, stale CAS, cold process, missing output/disabled lyric rejection, corrupt project fail-closed, three real process-death windows, orphan-history rejection, competing processes, namespace ordering.
- **40/40 prior real HTTP/security/export/restart checks** retained green on the changed source; current run integrity output in `export-integrity.log`. Historical M040 evidence was preserved.
- **15/15 project HTTP/restart checks** using the actual retained 50.5s original/edited WAVs and SongSpecs: R1, R2(parent R1), exact digest binding, process stop/restart, open by projectId, R1 history, stale rejection, R2 unchanged, unauthorized reads rejected. `project-discriminator.json` contains exact project and revision IDs.
- **4/4 UI authority checks** execute the exact UI functions against real HTTP through a Node VM with minimal DOM/storage adapters. Old browser song ignored, stale cached reference opens current R2, stale UI save rejects, durable R2 remains unchanged. This is not browser/PWA certification.
- A fresh headless Web Audio process executes the unchanged offline render function against the retained edited SongSpec and reproduces its exact WAV SHA-256 (`render-confirmation.json`). No new creative audio, PCM change or musical-quality claim.
- JS syntax / Python compilation / whitespace checks pass. Corrected release version is 2.19.1; its retained ZIP sidecar binds the exact source commit, inventory, packager and package SHA. Test sources are included in the runtime package inventory; Git-based baseline/probe commands still run from a checkout.

## Reproduction

From a fresh PR checkout:

```
npm ci --ignore-scripts
python3 -m unittest discover -s tests -v
python3 tools/m042_baseline_probe.py
python3 tools/m040_http_probe.py
python3 tools/m042_project_probe.py
node tools/m042_ui_probe.cjs
node tools/m040_music_probe.cjs --reopen
python3 package_project.py
```

Probes write only disposable runtime projects/exports and their designated evidence results. No browser cache is required for durable reopen.

## Limits / handoff

B must independently qualify and freeze the new head. C/D audio and musical verdicts remain pending. Browser/PWA interaction and literal playback remain unearned; Node adapters do not substitute for those gates. Audio remains the previously declared dual-mono proof. LyricTimeline remains disabled/null. Existing snapshots are not silently promoted into projects: opening/importing a loose SongSpec creates a draft; explicit Save establishes authority.

All changed source, tests, exact receipts and the source-bound package are conserved in the PR tree. Old 2.19.0 release and M040 media stay historical and unchanged. R5 cinema untouched. Human action: NONE.

WORK A ~ READY
