# Mission 040 — Source truth vs claims (Runnable-style)

Repo: `justinbusiness461-lab/pulseforge-songforge`
Branch inspected: `main` + `mission-039-sound-repair`

## Authoritative package

| Field | Value |
|-------|-------|
| Package | `SoundForge-Studio-Release-v2.18.zip` |
| Bytes | 53669 |
| SHA-256 | `a0ceb7dcdf3629ba8e86f4c644f68ccb9ac7d8a11becdd7bc3d2e25ac2be56cd` |
| Semantic version | **2.18.0 only** |

## Capability matrix (committed tree vs ZIP)

| Capability | File | On main | On mission-039 | Full size in ZIP | Claim ceiling |
|------------|------|---------|----------------|------------------|---------------|
| App shell | index.html | yes ~6k | yes | yes | UI shell |
| Engine core | app-core.js | **stub 7954** | stub | **36957** | ZIP is authority until expanded on branch |
| UI | app-ui.js | **stub 6833** | stub | **34151** | same |
| Cinema preview | app-cinema.js | missing/stub paths | — | 8987 | PREVIEW_ONLY |
| studio_server | tools/studio_server.py | **missing on main tree list** | **not landed full repair** | 11k+ repaired ~14k local | PF-SOUND-001/002 local PASS; remote incomplete |
| certify_integrity | tools/certify_integrity.py | older | **repaired (content_path)** | yes | content identity |
| certify_otio | tools/certify_otio.py | yes | yes | yes | structural only ≠ NLE |
| vocal_lab | tools/vocal_lab.py | missing as path on main listing | — | in ZIP | formant; no weights |
| test_harness | tools/test_harness.py | — | — | in ZIP | harness |
| BBD DSP | — | not as standalone committed module | — | historical snippets | HOLD qualify |
| ONNX SVS weights | models/vocal/ | empty .gitkeep | empty | empty | NOT_IMPLEMENTED |
| Tauri | — | no | no | no | HOLD |
| Secure broker | studio_server | main may still be * CORS if present | receipt only | local exact-origin PASS | SOUND_FORGE_SECURITY_PASS local only |
| Immutable export | studio_server | not on remote full | not full | local PASS A+B history | SOUND_FORGE_PROVENANCE_PASS local |

## PF-SOUND-001/002 local retest (Mission 040)

| Case | HTTP |
|------|------|
| Origin https://evil.example | 403 |
| Origin http://localhost.evil.com:8765 | 403 |
| Missing Origin | 403 |
| Origin http://127.0.0.1:8765 | 200 |
| Export A then B same alias; integrity both objects | PASS exit 0 |

## PF-SOUND-003

Formalized: package name **must** match semantic 2.18.0. Reject v2.5/v2.7 filename with 2.18 manifest.

## Non-claims

- Phase 8/9 “deployed/certified” narrative blocks are **not** product truth.
- Full app-core/ui still only complete inside the ZIP on this repo.
- MUSIC_GENERATION_PASS / product candidate **not** earned this turn.
