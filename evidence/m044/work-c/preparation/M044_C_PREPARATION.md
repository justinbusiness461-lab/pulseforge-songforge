# M044 Work C preparation

Repository persistence correction, 2026-11-06. Previous scratch downloads were lost during workspace maintenance. This reconstructed preparation replaces those downloads; it does not claim new product certification.

## Execution contract

Reuse tools/certify_mix.py (blob b3999968cbc4befb908e1cc0116292261dfb90c9). Run this directory's m044_physical.py with --repo EXACT_CHECKOUT and retained WAV paths. It checks strict RIFF length, chunk bounds, PCM16 metadata and full frames before calling the existing metrics owner. Metrics include SHA-256, rate, channels, frames, duration, sample peak, DC, exact-zero runs and L/R correlation. PCM16 has no nonfinite representation. Silence may be intentional; no perceptual dropout, true-peak, LUFS or artistic claim.

Retain original R1, distinct late R1 A, R2 B, exact revision IDs, artifact records, input digests, pre-kill/cold-reopen snapshots and exact merged-main/source hashes.

Negative fixtures: random bytes named WAV, truncation, bad RIFF length, inconsistent byte rate/block alignment, wrong channel metadata, digest mismatch, wrong source revision and missing historical artifact. File rejection alone does not prove application rejection: verify no playable binding or authority change through the real application.

A must decode; differ in digest from original R1 and B; belong to captured R1 exactly once; remain absent from R2 history; and reopen without replay. R2 and B remain current. Authenticate operation/project/source/render-input identities from durable records; never infer ownership from arbitrary CAS objects.

Compare decoded R1/R2 PCM frame-by-frame with identical formats and lengths. Derive selected section and declared release allowance from authoritative inputs. Require zero changed frames outside that interval; separately record inside changes. Verify minus 12 semitones and unchanged timing in authoritative events. Locality does not prove pitch.

Execute product qualification only after B supplies merged M044_MAIN_SHA. Preparation is not merged-main physical PASS. Do not change backend, DSP or revision authority.

## Persistence and validation receipt

Two preparation files are committed on an owner-disjoint branch for review, not directly to main. The script is reconstructed from the previous response and self-checked locally with one valid PCM16 fixture and three malformed fixtures (random bytes, truncated WAV, wrong RIFF length). These synthetic checks are not application admission or recovery proof.

Refresh: main README and tools/certify_mix.py read through GitHub; AGENTS.md returned 404; repository search corroborates the earlier absence of named governance files. Separate governance/Floot runtime not refreshed. No whole-project refresh claimed.

JUSTIN 101

- WHAT CHANGED: repository-owned physical preflight and fixture contract prepared.
- WHAT FAILED/BLOCKED: previous local download retention failed; product execution awaits authoritative merged-main gate.
- WHAT IS PROVEN: synthetic file preflight only, plus remote persistence after readback.
- WHAT IS NOT PROVEN: physical product audio, application admission/recovery, edit locality, listening or finished UI.
- WHAT JUSTIN MUST DO: nothing for repository persistence.
