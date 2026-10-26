# Work A — Mission 043 lyric authority candidate

Base main: e6e90d79823734dc5a54f789b399f02ce5fa69df (M042 freeze
7c92fe7a39d6b4209be510d02781adb6a1ef4182 plus retained B/C receipts).
Release: 2.20.0. B owns independent qualification, integration and freeze.

## Earned owner scope

Canonical LyricTimeline subordinate to ProjectRevision, integer half-open decoded
sample ranges, immutable full-content objects and parent lineage, exact source WAV
and decoded PCM identities, resolvable evidence, occurrence IDs, named method and
unknown confidence, explicit correction actor/reason/delta, existing project CAS.
Regular song saves preserve the current lyric binding and cannot silently drop its
source. New candidates cannot overwrite existing corrected truth. No lyric cache.

The lyric transaction holds the existing per-project lock; persists source/evidence/
lyric/revision metadata; rereads; fsyncs all referenced artifact files and namespace
ancestry; only then advances and rereads ProjectManifest. Orphan objects are never
current. Reopen walks and verifies the immutable lyric ancestry. History is bounded
at 128 revisions (fails closed rather than truncating). No new authority service.

## Fixture and evidence ceiling

The spoken WAV says **rise higher**, synthetic system Flite cmu_us_kal, no cloned
identity. Candidate input intentionally says **rise fire**, then occurrence w1 is
corrected to higher. This is *supplied-text alignment*, NOT automatic transcription.
The machine produces sample-bound R1 via known-text-energy-islands-v1; recognition
confidence is null. The deliberate wrong word comes from the provided fixture
transcript, not a claimed recognizer error. No ASR, VAD, continuous-speech, sung-word
or language-generalization gate is claimed. This bounded first slice exercises the
revision loop the mission requested without inventing model capability.

Fixture manifest binds WAV, decoded PCM, 8kHz mono, 17,539 frames and independent
construction intervals. Owner alignment errors: rise start 0/end +12 samples;
higher start -68/end +61 samples. These are signal-placement errors (10ms detector
blocks), not perceptually annotated phoneme accuracy. C must independently measure.

The negative fixture is the first 200ms of retained M040 initial.wav, with a
new PCM16 WAV header. With no known transcript, it returns unknown and zero words;
this does NOT establish general instrumental detection if someone supplies text.

Exact sample rates, R1/R2 lyric IDs, immutable object IDs, project revisions,
correction history, fixture identities and errors: lyric-discriminator.json.
It includes complete R1/R2 lyric/authority documents (song/timeline are digest-bound); objects remain reproducible by
running the retained probe, not by depending on the owner's ephemeral workspace.

## Fresh validation

- 35 unit tests, including old project/security/export conservation and new lyric tests.
- 25 HTTP/import/lyric/correction/restart/409/negative/malformed-audio checks.
- 40 original HTTP/security/export/restart checks.
- 6 exact lyric UI-function checks, Node VM/minimal DOM and actual HTTP.
- 4 exact prior project UI-function checks, Node VM/minimal DOM and actual HTTP.
- Real process death at lyric-object durability, project-revision durability,
  before manifest promotion and after manifest promotion; stale concurrent writers
  yield exactly one winner. Evidence/audio tampering fail closed.
- Python compilation, JavaScript syntax, git diff whitespace checks.

Commands:

```
python3 -m unittest discover -s tests -v
python3 tools/m043_probe.py
node tools/m043_ui_probe.cjs
python3 tools/m040_http_probe.py
node tools/m042_ui_probe.cjs
```

Existing probes write their historic evidence paths: current regression copies are
retained here and historic evidence was restored unchanged. No actual browser/PWA,
perceptual listening, physical timing certification, power-loss, or finished lyric
intelligence promotion. Product UI supports supplied-text alignment and word-only
correction; time editing and ASR are intentionally not implemented in this slice.

app-core.js, retained M040 audio, vocal synthesis, DSP and cinema are conserved.
All new source, fixtures, tests, receipts and release package go to this repository.
