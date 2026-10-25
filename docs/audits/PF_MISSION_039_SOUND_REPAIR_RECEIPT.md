# PF-COMPLETION-001 · Mission 039 — Sound Forge repair receipt

## PF-SOUND-001 — untrusted Origin mutation

**Fix:** `tools/studio_server.py` gates all `POST /api/*` on `Origin`.
- Default allowlist: `http://localhost:8765`, `http://127.0.0.1:8765` (override via `STUDIO_TRUSTED_ORIGINS`)
- Missing Origin → 403 unless `STUDIO_ALLOW_NULL_ORIGIN=1` (local CLI only)
- Untrusted Origin → 403 `origin_not_allowed`
- CORS reflects trusted Origin only (no `*` on mutations)

**Regression observed:**
| Case | HTTP |
|------|------|
| Origin: https://evil.example | 403 |
| No Origin | 403 |
| Origin: http://127.0.0.1:8765 | 200 |

## PF-SOUND-002 — export overwrite vs historical ledger

**Fix:** content-addressed store `workspace/studio_exports/objects/<sha256>/<filename>` + mutable alias under `exports/`.
Ledger binds `content_path` + `content_sha256` + `artifact_id`.

**Regression observed:**
- Export A (19 bytes) → object f909b1ae…
- Export B same alias `master.wav` (22 bytes) → object 3b3af7c4…
- `certify_integrity.py` verifies **both** historical entries PASS (exit 0)

## Non-claims
- Not SOUND_FORGE_PRODUCT_CANDIDATE
- Browser UI journey still unverified in this host
- Formant vocals remain PREVIEW_ONLY
