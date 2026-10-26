# Mission 042 — PROJECT_AUTHORITY_CANDIDATE

Parent: PR #4 `fcab64b18f325cd718e0ddb76f3d1ba72645fdd2`
Branch: `work-a/m042-project-authority`

## Model

ProjectManifest { projectId, currentRevisionId, formatVersion }
ProjectRevision { revisionId, parentRevisionId, songSpecDigest, productionTimelineDigest, lyricTimelineDigest, sourceAssetDigests[], outputArtifactIds[], createdAt }

Browser localStorage role: **cache only** — reopen sets `browserCacheRole: ignored`.

## API (existing Origin + capability gate)

- POST /api/project/create
- POST /api/project/commit (CAS expectedCurrentRevisionId)
- POST /api/project/reopen
- POST /api/project/bind_output

## Durability

1. Atomic revision write
2. Re-read tip; refuse if changed (stale_revision_race)
3. Advance currentRevisionId only after revision durable

## Local tests

- test_project_authority: 3/3 PASS (R1→R2 reopen, stale CAS, tip bind)
- test_m040 security/objects: 9/9 PASS against wired server

## B ownership

Independent fresh-process reopen + security/provenance retest → merge/freeze.

## Not claimed

SOUND_FORGE_M042_FREEZE_SHA, product candidate, lyrics, browser/PWA.
