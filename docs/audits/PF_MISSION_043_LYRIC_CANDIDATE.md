# Mission 043 — LYRIC_TIMELINE_M043_CANDIDATE

Branch: `work-a/m043-lyric-timeline`

## Schema
Integer half-open sample coordinates. Model = evidence only.

## Fixture FX-LYRIC-001
Digest `857e078e33b7caedb7a22ef783370b0de1a9e26214dfa1db041ebfb0ea5f5ba3`
R1 machine: hello **fire** world → R2 user: hello **higher** world

## Proofs
- R1→R2 parent chain; R1 immutable after correction
- Fresh store reopen retains both
- Audio digest unchanged by text correction
- Instrumental: empty words, `no_vocal_detected`
- Invalid ranges / digest mismatch rejected

## Tests
`python3 -m unittest tests.test_lyric_timeline -v` → 4/4 PASS

## Not yet
LYRIC_INTELLIGENCE_PASS, full ASR, ProjectRevision HTTP wire of lyricDigest on main freeze, WAV blob on remote (metadata + local WAV sha matched).
