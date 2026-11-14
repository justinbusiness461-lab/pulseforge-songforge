# PF-M044-RUNNABLE-NASA-001 — Differential Clean-Room Qualification

**Program:** PF-COMPLETION-001  
**Mission:** M044 — S.A.R.A. Studio / Sound Forge  
**Lane:** RUNNABLE / Codex clean-room reproducibility  
**Date:** 2026-11-10  
**Classification:** EXECUTION SPECIFICATION — not certification by itself  
**Primary repository:** `justinbusiness461-lab/SARA_studio`  
**Canonical repository ID:** `1427534706` (rename preserved repository identity/history)

## 1. Mission

Prove, from a fresh qualified checkout, whether the next Sound Forge successor candidate actually closes the two current M044 P0 boundaries without weakening existing project/revision authority:

1. **P0-A — pre-pending crash recovery**: a valid late R1 WAV may not become permanently orphaned if the process dies after artifact durability but before historical association.
2. **P0-B — authenticated revision-bound WAV access**: Studio may retrieve audio only after the server proves principal → project → revision → artifact ownership and validates the immutable audio bytes.

Runnable answers one question:

> Can an exact, clean checkout deterministically reproduce the claimed repaired product path from source alone?

Runnable does **not** replace Manus endurance/torture testing, Work B integration authority, Work C physical-audio certification, Chat D product attack, or Music Specialist listening approval.

---

## 2. Verified starting frontier

At dispatch time:

- Current `main`: `14e2fb9cc55c8ce2909803a66d509915a18eb625`.
- PR #10: merged; prior bounded qualification remains historical evidence.
- PR #17: independently records the current pre-pending crash failure.
- PR #16: documentation-only revision-bound WAV access contract; not implementation proof.
- PR #18: QA-only two-principal HTTP/audio + transport-fence harness; harness self-tests are not live product proof.
- PR #19: Runnable exact-source clean-run harness.
- PR #11: still stacked on an older Bobby base; not current-main product integration truth.

The next candidate SHA must be supplied by the rightful Sound Forge mutation owner or successor main. Never infer it from a branch name.

---

## 3. Authority and ownership rules

Preserve rightful owners.

Runnable may:

- clone/fetch/read source;
- create disposable worktrees/checkouts;
- execute tests and probes;
- start local servers;
- create disposable projects and audio fixtures;
- inject process death into test-only executions;
- inspect HTTP responses;
- calculate hashes;
- retain logs/receipts;
- publish evidence-only commits/PR updates.

Runnable may **not**:

- modify Sound Forge product behavior;
- repair Bobby's code;
- create a second ProjectRevision/history/artifact authority;
- invent an authenticated endpoint;
- expose raw CAS or filesystem paths to the browser;
- promote a branch or merge a candidate;
- claim browser/mobile/listening/deployment proof without directly executing it.

If the candidate fails, stop at the first material failure and return exact evidence.

---

## 4. Inputs

Required:

```text
BASELINE_SHA=14e2fb9cc55c8ce2909803a66d509915a18eb625
CANDIDATE_SHA=<exact Bobby/Work-B successor SHA>
RUNNABLE_PR=19
NEGATIVE_EVIDENCE_PR=17
QA_HARNESS_PR=18
```

Optional only when a real owner-approved authenticated WAV surface exists:

```text
NASA004_FIXTURE=<private runtime fixture path>
NASA004_COOKIE_A=<secret environment value>
NASA004_COOKIE_B=<different secret environment value>
```

Secrets never enter Git, logs, receipts, chat, screenshots, or command echo.

---

## 5. Environment preflight — G0

Use a fresh Codex/cloud checkout or equivalent qualified execution environment.

Record:

```text
repository
remote URL
git HEAD
git status --porcelain
Python version
Node version
npm version
OS/kernel
CPU count/quota if visible
memory limit if visible
network availability
start UTC
```

Required:

- repository identity exact;
- worktree clean before execution;
- candidate commit resolves locally;
- baseline commit resolves locally;
- no untracked product files;
- no local product patches;
- no branch-name substitution for SHA identity.

If any identity cannot be proven:

```text
G0 = BLOCKED
```

Stop.

---

## 6. Negative-control qualification — G1

Before testing a claimed repair, prove the test system still detects the known defect.

Checkout or detached-worktree the exact baseline:

```bash
git checkout --detach "$BASELINE_SHA"
```

Run PR #19's clean-run harness with the baseline pinned:

```bash
RUNNABLE_EXPECT=known-bad TARGET_SOURCE_SHA="$BASELINE_SHA" bash tools/runnable_m044_clean_run.sh
```

The baseline is currently expected to reach the independent pre-pending reproducer and report the known failure.

Expected negative-control facts:

```text
artifactHashValid = true
artifactDecodeValid = true
R2StillCurrent = true
historyOccurrences = 0
verdict = FAIL
```

The hardened harness must return success for **negative-control detection**, not for product recovery. In `known-bad` mode it independently requires the expected failure facts above; a false-green baseline is a harness failure.

**PASS condition for G1:** the known-bad baseline is actually detected as bad and `RUNNABLE_M044_NEGATIVE_CONTROL=PASS` is emitted.

### Receipt-verifier self-proof

Before any candidate execution, run:

```bash
python3 -m unittest discover -s tests/runnable -p 'test_*.py' -v
```

The verifier must reject at minimum:

```text
verdict=PASS
historyOccurrences=0
```

Candidate-mode PASS must not trust the top-level verdict. It must independently require the underlying evidence fields.

If the baseline unexpectedly reports repaired recovery:

```text
G1 = BLOCKED
REASON = NEGATIVE CONTROL DID NOT REPRODUCE
```

Do not certify the candidate. Investigate harness/environment drift first.

---

## 7. Candidate identity and delta gate — G2

Create a fresh detached worktree at the exact candidate:

```bash
git worktree add --detach ../m044-runnable-candidate "$CANDIDATE_SHA"
cd ../m044-runnable-candidate
```

Record:

```bash
git rev-parse HEAD
git status --porcelain
git diff --stat "$BASELINE_SHA"..."$CANDIDATE_SHA"
git diff --name-status "$BASELINE_SHA"..."$CANDIDATE_SHA"
```

Inspect the candidate delta.

The repair must remain within rightful owners. Any new competing revision store, artifact store, browser-owned project truth, or raw-workspace media authority is a **FAIL**.

Runnable does not judge stylistic code quality here; only ownership and executable consequences.

---

## 8. Deterministic repository reproduction — G3

Run the repository's own documented and current M044 checks.

Minimum:

```bash
python3 -m unittest discover -s tests -v
node --test tests/scorecore.test.cjs tests/m044-session.test.cjs
node tools/m044_probe.cjs /tmp/m044-runnable-probe
```

Also execute the focused existing recovery/audio tests if still present:

```bash
PYTHONPATH=tools:tests python3 -m unittest -v \
  test_m044_operations.OperationTests.test_malformed_historical_wav_rejected \
  test_m044_operations.OperationTests.test_crash_before_history_bind_recovers_without_replay
```

No skipped or silently deleted tests.

Record exact test counts and exit codes.

A build or unit-suite PASS alone does not prove G4/G5.

---

## 9. Pre-pending crash repair proof — G4

Run the **same independent negative-control reproducer** against the candidate, adapted only as necessary to import the candidate's actual source. Do not weaken the kill point.

Corrected R3 durability law:

```text
1. persist RenderAttempt identity:
   operationId / projectId / sourceRevisionId / expectedRevisionId /
   renderMeaningDigest / renderConfigDigest / deterministic staging identity /
   state=RENDERING
   → fsync

2. render privately to staging
3. fully validate WAV
4. compute final artifactDigest
5. persist RenderAttempt:
   artifactDigest / intended CAS identity / validated audio metadata /
   state=VALIDATED_NOT_PUBLISHED
   → fsync

6. atomically publish staging → CAS
   → fsync CAS directory

7. persist state=ARTIFACT_DURABLE
   → fsync

8. persist subordinate R1 historical association
   → fsync

9. persist state=HISTORICALLY_BOUND
   → fsync

10. attempt expected-revision current-output promotion
```

**Invariant:** exact artifact identity and intended CAS identity are durable **before** CAS publication. CAS existence is never authorization and never ownerless.

Runnable must exercise two distinct deterministic crash cases:

```text
CRASH A:
attempt knows exact artifactDigest + intended CAS identity
CAS is not yet published

Expected:
- restart finds exactly one known incomplete attempt;
- no invented historical output;
- no CAS scanning/filename inference;
- R2 current/output unchanged;
- zero new ProjectRevision.

CRASH B:
attempt knows exact artifactDigest + intended CAS identity
CAS is published
historical association is not yet durable

Expected:
- restart validates that exact known CAS object;
- binds it to R1 exactly once;
- R2 current/output unchanged;
- zero new ProjectRevision;
- no caller/browser replay.
```

Required candidate outcome after fresh reopen:

```text
artifact digest valid = true
WAV decode valid = true
R1 historical binding count = exactly 1
R2 remains current = true
R2 current output unchanged = true
pending orphan count = 0 after successful reconciliation
new ProjectRevision created by recovery = 0
caller replay required = false
browser/cache required = false
arbitrary CAS ownership inference = false
```

Execute a second cold reopen and prove the R1 association remains exactly one.

No duplicate historical binding is allowed.

### Coupled orphan-access discriminator

If authenticated WAV access exists in the candidate, also prove:

1. create the old vulnerable state or equivalent test fixture where valid bytes exist but lawful revision association is not yet established;
2. request that artifact through the new audio accessor **before** reconciliation;
3. access must be denied/unavailable;
4. complete lawful recovery;
5. retry the same revision-bound request;
6. exact bytes must now be returned.

This proves:

> CAS existence is not authorization.

---

## 10. Authenticated revision-bound WAV qualification — G5

Run only if a real owner-approved endpoint exists in the candidate.

Required backend authorization order:

```text
principal/session
→ project authorization
→ requested revision is lawful project history
→ requested artifact is lawfully associated with that revision
→ immutable artifact bytes authenticate
→ admitted WAV validates/decodes
→ stream
```

Forbidden authority shortcuts:

- digest alone;
- filename alone;
- filesystem path;
- browser-provided "current";
- raw CAS existence;
- same-project-but-wrong-revision association.

### Minimum deterministic HTTP matrix

| Case | Expected |
|---|---|
| A reads A current R2 | PASS |
| A reads A historical R1 | PASS |
| A requests R1 artifact as R2 | DENY |
| A requests R2 artifact as R1 | DENY |
| B reads A project | DENY |
| B reads A audio knowing exact digest | DENY |
| anonymous reads A audio | DENY |
| unknown revision | DENY |
| artifact absent from requested revision | DENY |
| corrupt digest/bytes | DENY |
| malformed WAV | DENY |
| unbound/orphan CAS artifact | DENY |

Prefer the PR #18 `live_nasa004.py` harness when its expected contract matches the implemented owner-approved API. Adapt tests, not product authority, if headers/naming differ.

If two genuinely distinct authenticated principals are unavailable:

```text
G5_TENANCY = UNVERIFIED
```

Do not simulate two users with the same credential.

---

## 11. Real R1 → R2 product path — G6

When G4 and G5 pass, execute the bounded canonical journey through the actual server interfaces:

```text
create/open project
→ Generate or canonical M044 R1 fixture
→ resolve R1 ProjectRevision
→ retrieve authorized R1 WAV
→ decode/hash
→ scoped Verse 2 Bass -12 semitone edit
→ commit R2
→ retrieve authorized R2 WAV
→ decode/hash
→ verify R2 remains current
→ retrieve historical R1 again
→ close server/process
→ fresh restart
→ reopen project
→ R2 remains current
→ R1 remains historical/playable
```

Record exact:

```text
projectId
R1 revisionId
R1 artifactId/SHA256
R1 decoded PCM SHA256
R2 revisionId
R2 artifactId/SHA256
R2 decoded PCM SHA256
currentRevisionId after edit
currentRevisionId after cold reopen
historical R1 binding identity
```

No raw audio bytes in logs unless repository policy explicitly allows the synthetic fixture.

---

## 12. Playback truth / publication fence — G7

Runnable does not need a graphical browser to qualify the presentation-state reference, but must execute the existing PR #18 fence tests or the integrated equivalent.

Required deterministic cases:

- late R1 completion after R2 selection cannot publish as current;
- explicit historical R1 may play without changing server current authority;
- missing R2 audio does not silently fall back to R1;
- wrong digest does not become playable;
- unverified revision binding does not become playable;
- request cancellation blocks late publication;
- server authority change invalidates stale current request;
- 60 sequential rapid A/B selections admit only the latest intended request in the reference model.

For the M044 fixture with unchanged musical topology, A/B must also preserve the same intended musical position.

Correct files at different musical positions = **HOLD**, not A/B PASS.

---

## 13. Restart / interruption matrix — G8

Execute deterministic, not randomized, interruption points. Manus owns large randomized endurance.

Required Runnable interruption points where supported:

```text
A. after RENDERING attempt fsync, before validated digest identity
B. after VALIDATED_NOT_PUBLISHED fsync, before CAS publication (Crash A)
C. after CAS publication / before ARTIFACT_DURABLE state
D. after ARTIFACT_DURABLE / before historical association (Crash B)
E. after historical association / before HISTORICALLY_BOUND
F. before optional current-output promotion
G. during authorized WAV response setup
H. client abort during WAV stream
I. backend restart after R2 commit
J. client/process reopen after R2
```

For every case record:

```text
source revision
artifact identity
current revision before
current revision after
history count
pending count
duplicate revision count
response status
recovery path
```

No ambiguous consequential retry. Read back disk/project authority before repeating a failed mutation.

---

## 14. Performance and resource observations — G9

This is bounded engineering telemetry, not performance certification.

Capture when possible:

```text
wall time — full deterministic suite
wall time — M044 probe
wall time — R1 authorized fetch
wall time — R2 authorized fetch
peak RSS
open file descriptor count before/after
workspace artifact count before/after
pending-record count before/after
orphan artifact count if measurable
```

Do not publish speed comparisons against Manus or production until environments are normalized.

---

## 15. Evidence retention

Create an evidence directory outside mutable runtime state:

```text
evidence/runnable-nasa001/<candidate-short-sha>/
```

Minimum files:

```text
source_identity.json
environment.txt
git_delta.txt
python_tests.log
node_tests.log
m044_probe.log
negative_control_baseline.json
candidate_early_crash.json
candidate_second_reopen.json
http_audio_matrix.json
r1_r2_identity.json
transport_fence.log
restart_matrix.json
resource_observations.json
receipt.json
```

Hash every evidence file with SHA-256.

The final receipt must distinguish:

```text
SOURCE
BUILD
UNIT
INTEGRATION
PROCESS_RECOVERY
HTTP_AUTHORIZATION
AUDIO_BYTES
PLAYBACK_IDENTITY
COLD_REOPEN
BROWSER
MOBILE
LISTENING
DEPLOYMENT
```

Anything not directly executed is `UNVERIFIED`.

---

## 16. Stop conditions

Stop immediately and return the first material failure when:

- exact candidate SHA cannot be established;
- product source is dirty or unexpectedly patched;
- baseline negative control does not reproduce;
- existing core suite regresses;
- early-crash repair still loses R1 ownership;
- recovery duplicates R1 history;
- recovery promotes R1 over R2;
- unbound CAS bytes are retrievable;
- cross-project/user audio leaks;
- wrong-revision audio is returned;
- malformed/corrupt WAV is represented as playable;
- R2 absence silently falls back to R1;
- stale R1 response can become current.

Do not continue to later gates to manufacture a favorable aggregate result.

---

## 17. Pass classification

### COMPLETE / PASS — bounded

Allowed only when all candidate-applicable gates through G8 pass, with direct evidence, and no P0/P1 contradiction remains inside Runnable scope.

### HARDENING_ADVANCE

Use when material deterministic proof is produced but one downstream gate remains legitimately unavailable, such as hosted two-user sessions or browser/mobile execution.

### BLOCKED

Use when a prerequisite does not exist, such as no candidate SHA or no real authenticated endpoint.

### FAIL

Use when executable behavior contradicts the required contract.

---

## 18. Required machine-readable return

Return exactly one summary block:

```text
RUNNABLE_NASA001 = PASS|FAIL|BLOCKED|HARDENING_ADVANCE

BASELINE_SHA = 14e2fb9cc55c8ce2909803a66d509915a18eb625
CANDIDATE_SHA = <exact>
EVIDENCE_SHA = <receipt sha256>

G0_ENVIRONMENT = PASS|FAIL|BLOCKED
G1_NEGATIVE_CONTROL = PASS|FAIL|BLOCKED
G2_CANDIDATE_IDENTITY = PASS|FAIL|BLOCKED
G3_REPO_REPRODUCTION = PASS|FAIL|BLOCKED
G4_EARLY_CRASH_RECOVERY = PASS|FAIL|BLOCKED
G4_CRASH_A = PASS|FAIL|BLOCKED
G4_CRASH_B = PASS|FAIL|BLOCKED
G5_AUTH_WAV = PASS|FAIL|BLOCKED|UNVERIFIED
G6_R1_R2_REOPEN = PASS|FAIL|BLOCKED|UNVERIFIED
G7_PLAYBACK_FENCE = PASS|FAIL|BLOCKED|UNVERIFIED
G8_INTERRUPT_MATRIX = PASS|FAIL|BLOCKED
G9_RESOURCE_OBSERVATION = PASS|BLOCKED

PYTHON = <passed/total>
NODE = <passed/total>
INTEGRATION = <passed/total>
HTTP_AUDIO = <passed/total or UNVERIFIED>
CRASH_CASES = <passed/total>
RECEIPT_VERIFIER = PASS|FAIL
CONTRADICTORY_PASS_REJECTED = true|false
R1_HISTORY_OCCURRENCES = <integer>
R2_STILL_CURRENT = true|false|UNVERIFIED
CROSS_PROJECT_DENIAL = PASS|FAIL|UNVERIFIED
ORPHAN_PRE_RECONCILIATION_ACCESS = DENIED|EXPOSED|UNVERIFIED
COLD_REOPEN = PASS|FAIL|UNVERIFIED

SOURCE_MUTATION_BY_RUNNABLE = NONE
PRODUCT_AUTHORITY_CREATED = NONE
RELEASE_CERTIFIED = false
```

Then provide a short JUSTIN 101:

```text
WHAT CHANGED
WHAT FAILED/BLOCKED
WHAT IS PROVEN
WHAT IS NOT PROVEN
WHAT JUSTIN MUST DO, IF ANYTHING
```

---

## 19. Wake condition

Run immediately when either condition occurs:

1. Bobby/Work B publishes an exact successor SHA addressing P0-A and/or P0-B; or
2. `main` advances to a successor commit with those changes.

If only one P0 is repaired, execute the applicable gates and return the other as BLOCKED/UNVERIFIED. Do not wait for unrelated Studio work.

---

## 20. NASA-grade success criterion

Runnable succeeds when a clean environment can prove, from exact source identity and reproducible commands, that:

> the repaired engine cannot lose lawful R1 ownership in the known crash window; unowned bytes cannot be served merely because they exist; the correct user can retrieve the exact current and historical revision-bound WAVs; R2 remains authoritative across restart; R1 remains truthful history; and stale playback state cannot turn old audio into current truth.

That is the reproducibility bridge from repaired source to a product Work B, Manus, Work C, Chat D, and the musician can trust.
