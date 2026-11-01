# Work C — Mission 044 physical measurement harness contract

Status: DESIGN PREPARED; NOT EXECUTED against a generated song. No M043 rerun or source mutation.
M043 certification freeze remains 076aed8d438a938119a7c2d5b34bb5eeb3ba4409.
M043 scope: GUIDED SUPPLIED-TEXT ALIGNMENT; SYNTHETIC SPEECH; NOT ASR; NOT SINGING CERTIFICATION.

## Evidence handoff to B
PR #7 open/mergeable at 1f59490cae892b56eb5d90e1c34863acb778dc1d; four evidence files remotely reachable at that exact commit.
Git blobs:
measure.py 4e6c72cf9050e5d2b4229c3785fada30215ca251
measurement.json 4c05a2c0f211b28dc37a56ce0d1916c083eb1597
recovery.json 04e7f1a3af5df936663fa89c9a0a9c603c1883a7
RECEIPT.md a6afc26631540a7be81fc11cf2622825df18d923
These are Git blob identities, not SHA-256 media digests. Evidence commit does not replace certification freeze.
Retained C result: 25 workflow checks; max construction-boundary error 8.5 ms. No tests rerun this turn.

## Inputs and authority
Exact source freeze, renderer/tool versions, command, environment identity, immutable before/after AudioMaster artifact and decoded PCM digests, declared PCM encoding/channel order/rate/frame count, SongSpec and ProductionTimeline revisions, integer half-open section intervals, intended edit interval and explicitly declared DSP/release tails.
Read section boundaries from the existing authoritative timeline; do not create a new section graph. Record clock conversion/rounding rule. Reject mismatched rate/length unless an explicit resampling/alignment operation is declared. No automatic time shift, gain normalization, or resampling before locality comparison.
Required output: per metric value/unit/method/version/scope/status/limitations plus raw logs and source identities. Unsupported metrics = UNVERIFIED, never inferred PASS. Report null for undefined ratios.

## Measurement plan
| Metric | Method | Interpretation |
|---|---|---|
| Sample peak | max absolute decoded amplitude; 20 log10(amplitude/full scale), silence = negative infinity | Sample peak only |
| True peak | qualified FFmpeg ebur128 peak=true or validated oversampled estimator; retain implementation/version | Label measured estimate and method; never substitute sample peak |
| LUFS-I | qualified BS.1770/EBU R128 implementation, explicit channel layout and gating | Full-song plus optional section loudness; short/silent sections may be undefined |
| Stereo | Pearson L/R correlation, mid/side energy and side-to-mid dB by song and section; mono downmix loss | Dual mono, phase risk and intended width reported separately; undefined for zero variance |
| Section RMS | per-channel and aggregate RMS over exact sample boundaries, dBFS and section duration | Include silence; no hidden gain matching |
| Macro dynamics | per-section RMS contrasts, crest factor, windowed RMS distribution and transitions | Do not equate compression with quality; do not mislabel as standardized LRA |
| Spectral balance | sample-rate-aware band energy: 20–120, 120–500, 500–2000, 2000–6000, 6000–Nyquist Hz | State window/FFT/hop/channel combination; truncate at Nyquist; report absolute and fractional energy |
| Silence/dropout | contiguous sample intervals from defined windowed RMS and peak thresholds | Proposal: below -60 dBFS for >=250 ms; expected intro/outro silence annotated; cannot alone diagnose dropout |
| Section differentiation | compare duration-normalized RMS, band-energy and stereo summaries; symbolic event/arrangement comparison where available | Similarity is diagnostic, not proof of fake variation; repeated motifs may be intentional |
| Edit locality | exact PCM equality outside union of edit interval and declared tails; report all differing runs, first/last sample, outside peak/RMS delta | Symbolic locality, render-input locality and PCM locality returned separately; stochastic renders require a declared tolerance contract |

## Validation vectors before candidate admission
Neutral generated fixtures only: silence, mono sine, dual mono, independent stereo tones, anti-phase stereo, impulse near full scale, section gain step, inserted silent gap, identical A/B, edit inside permitted interval, unauthorized one-sample change outside it.
Expected checks: undefined silent correlation is null; dual mono side energy zero; anti-phase downmix loss flagged; gain step reflected in RMS; silent gap bounds reported at analysis-window resolution; exact equality yields no differences; outside sample change fails locality. True-peak/loudness need independently trusted reference vectors before qualification.
The harness must not certify its own numeric implementation solely using expectations calculated by that implementation.

## Candidate admission and outcomes
Require B-qualified M044 freeze plus exact before/after artifacts and edit contract.
First run reports measurements rather than inventing universal width/loudness/dynamics targets. Predeclare numeric thresholds with owners before acceptance; D owns creative rubric (proposed >=7/10, category floors), not this harness.
TECHNICAL_MEDIA, EDIT_LOCALITY, and MUSICAL_QUALITY remain separate verdicts.
No loudness normalization or mastering change is authorized by measurement.

## Cinema preservation
Current R5 production packet blob dfc8268172472dc61782d465cc15c415229492a7 remains reachable and matches previous identity; release digest e5e26578dbc9b7a81c8c6c4edf7f4e6881160806d6c2020654cae867f34451ae.
No render, cinema mutation, or invalidation established. Historical physical R5 evidence is not reset.
shot0029 readiness and media-byte reachability not freshly authenticated; preserve existing state, do not claim ready.

## Refresh limits
GitHub PR #7, exact evidence blobs and current R5 packet refreshed. Accessible supplied instructions applied. Floot, separate governance runtime and shot0029 package not refreshed: UNVERIFIED.

## JUSTIN 101
WHAT CHANGED: Exact C evidence identities handed to B; M044 measurement contract prepared.
WHAT FAILED/BLOCKED: No M044 frozen audio candidate supplied; execution not attempted.
WHAT IS PROVEN: PR #7 evidence reachability and unchanged R5 packet identity.
WHAT IS NOT PROVEN: M044 metrics, harness implementation/qualification, new music quality or full cinema readiness.
WHAT JUSTIN MUST DO: Nothing; B consolidates M043, M044 owners supply frozen candidate later.
