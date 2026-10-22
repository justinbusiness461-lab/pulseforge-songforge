# Sound Forge — Capability Matrix (PF-LRC-006/007/008)

Status: IMPLEMENTED_AND_CERTIFIED | IMPLEMENTED_NOT_CERTIFIED | PARTIAL | MISSING | BLOCKED_BY_DEPENDENCY | NOT_APPLICABLE

| Capability | Status | Owner | Notes |
|---|---|---|---|
| NL prompt to structure | IMPLEMENTED_AND_CERTIFIED | parsePrompt | BPM/key/genre/sections |
| Procedural multitrack | IMPLEMENTED_AND_CERTIFIED | playScore | Local Web Audio |
| Offline WAV + RMS gate | IMPLEMENTED_AND_CERTIFIED | renderMixBuffer | nonzero PCM |
| Section lyrics/mute/dup | IMPLEMENTED_AND_CERTIFIED | applySection* | isolation tested |
| Project round-trip | IMPLEMENTED_AND_CERTIFIED | loadProjectObject | fingerprint |
| OTIO / integrity | IMPLEMENTED_AND_CERTIFIED | tools/certify_* | |
| Neural SVS | BLOCKED_BY_DEPENDENCY | vocal_lab | no ONNX weights |
| Public mobile host | NOT_APPLICABLE | — | NOT RUN |
| Stem separation | MISSING | — | |
| BPM from audio | MISSING | — | prompt-derived only |
