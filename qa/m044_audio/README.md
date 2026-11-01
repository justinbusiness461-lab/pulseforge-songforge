# M044 physical audio harness

Tooling only, outside product source. Reuses tools/certify_mix.py for existing PCM16 sample metrics; NumPy 2.3.5 used for channel/spectral/window analysis. Python 3.12; FFmpeg 6.1.1-3ubuntu5 observed locally. No new product dependencies or authority owners.

Run neutral suite: `cd qa/m044_audio && python3 -m unittest -v`
Run candidate: `python3 qa/m044_audio/measure.py before.wav --manifest sections.json --after after.wav --out report.json`

Manifest: `{"sampleRate":48000,"sections":[{"id":"verse","startSample":0,"endSample":48000}],"allowedEditAndTailIntervals":[[12000,24000]]}`

Candidate admission remains B's exact M044 freeze plus immutable before/after audio, authoritative timeline-derived section bounds and declared edit/tail intervals. This CLI consumes those inputs; it does not independently authenticate project/revision bindings. Bind command, source SHA, manifest digest and output in C's eventual candidate receipt.

Outputs: sample metrics, container and decoded PCM identities, whole/section stereo/RMS/DC/spectral/silence metrics, whole/section FFmpeg loudness/oversampled peak logs, adjacent-section RMS contrast, section RMS range, and exact before/after differing intervals/outside delta. PCM16 WAV only; fail closed on other formats, mismatched sample clocks/shapes or invalid section bounds. No implicit resampling, normalization or alignment.

Qualification: 15/15 neutral tests pass. Initial TDD run failed because implementation did not exist. Analytic sine sample peak/RMS, known gain ratios, independent tones, dual mono/anti-phase, inserted gaps, spectral band placement and exact locality vectors pass. FFmpeg 1kHz -6.0206dBFS-amplitude mono reference produces -6.0dBTP / -9.0LUFS-I within declared tolerances .15dB/.2LU. This reference is not an intersample-overshoot stress vector or full BS.1770 conformance suite. FFmpeg outputs remain OBSERVED_NOT_REFERENCE_QUALIFIED for general metering. Do not promote these to mastering certification. Sample peak remains separate from true-peak estimate.

Undefined silence/zero-energy dB and correlation are null, not fabricated zero. Null dB means undefined/negative infinity where amplitude is zero. Anti-phase zero downmix is represented by midRms=0 and null log ratio. Silence is a 10ms RMS window diagnostic, not proof of unintended dropout. Spectral fractions include all FFT-bin power in denominator; energy under 20Hz can remain unassigned. Section differentiation is diagnostic RMS contrast, not creative scoring. Macro range is section RMS range, not standardized LRA. No song, M043 fixture or cinema render was executed. No perceptual quality verdict.

Remaining validation: independent intersample-overshoot/EBU conformance corpus, stronger section spectral/stereo comparison rubric, actual B-frozen M044 integration. D owns listening quality. Product source and cinema unchanged.

JUSTIN 101
WHAT CHANGED: executable physical measurement CLI and 15 neutral tests.
WHAT FAILED/BLOCKED: full loudness/true-peak meter conformance unqualified; no M044 candidate admission.
WHAT IS PROVEN: stated neutral vectors and bounded FFmpeg reference observation.
WHAT IS NOT PROVEN: song quality, mastering, project/revision bindings, any M044 audio PASS.
WHAT JUSTIN MUST DO: nothing; B reviews tooling; C waits for qualified audio candidate.
