# Mission 042 — Work C physical audio + recovery

**Freeze:** `7c92fe7a39d6b4209be510d02781adb6a1ef4182` only

## TECHNICAL_AUDIO_CANDIDATE = PASS

| Metric | initial.wav | edited.wav |
|--------|-------------|------------|
| SHA-256 | `512bdfc02b2aa18476d3b32fac9898724d1a8c4255f01c5599decd8886050858` | `796b0432264aaac2c5d34f64c650a7037d841d86d910cfd74798c55a3d45ccee` |
| Container | WAV/RIFF PCM | same |
| Sample rate | 44100 | 44100 |
| Channels | 2 | 2 |
| Decoded frames | 2227050 | 2227050 |
| Duration | **50.5 s** | **50.5 s** |
| Sample peak (norm) | 0.33277 | 0.33277 |
| dBFS peak (`20*log10`) | **-9.557** | **-9.557** |
| DC offset L/R | ~3.69 / ~3.66 (int16 mean) | mild, not zero |
| Silence ≥0.5s runs | 1 (edge region) | 1 |
| L/R correlation | **1.0** | **1.0** |
| Dual-mono | **YES** (declared contract) | **YES** |
| True peak / LUFS-I | NOT_MEASURED | NOT_MEASURED |

Receipt SHA matches render-receipt.json (initial + edited). Cold-reopen JSON matches edited SHA.

### Edit preservation

| Level | Result |
|-------|--------|
| SYMBOLIC | SongSpec digests differ (edit applied); receipt `unchanged_symbolic_regions: true`; sample deltas outside edit+100ms tail: **0** |
| RENDER-INPUT | Bound in revision outputBindings to exact digests |
| PCM identity | Not required for full file; edited ≠ initial SHA as expected |

No clipping at sample peak (~−9.6 dBFS). Dual-mono is classification, not failure under declared contract.

## PROJECT_RECOVERY_PHYSICAL = PASS

On freeze SHA:

- `python3 -m unittest tests.test_project_authority -v` → all PASS including `test_cold_process_no_cache`, `test_stale_rejected`, `test_crash_before_and_after_promotion`
- `evidence/m042/project-discriminator.json`: all checks pass; `browser_cache_used: false`; `new_server_process: true`; R2 current; R1 retained; outputs bound to WAV SHAs above

## Non-claims

- Not AUDIO_MASTER_PASS (mastering / true peak / LUFS not measured)
- Not musical quality (D owns listen)
- Not browser/PWA product journey
- Not Mission 043

## Verdict

```
TECHNICAL_AUDIO_CANDIDATE = PASS
PROJECT_RECOVERY_PHYSICAL = PASS
```
