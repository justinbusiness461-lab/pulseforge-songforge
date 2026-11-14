#!/usr/bin/env bash
set -euo pipefail

TARGET_SOURCE_SHA="${TARGET_SOURCE_SHA:-14e2fb9cc55c8ce2909803a66d509915a18eb625}"
REPRO_COMMIT="${REPRO_COMMIT:-c107da1308dcd972676d237d33b8c318f7d34f33}"
REPRO_PATH="evidence/work-b-m044-r2-crash/independent_pre_pending.py"
RUNNABLE_EXPECT="${RUNNABLE_EXPECT:-candidate}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

case "$RUNNABLE_EXPECT" in
  candidate|known-bad) ;;
  *) printf 'BLOCKED: RUNNABLE_EXPECT must be candidate or known-bad\n' >&2; exit 2 ;;
esac

ACTUAL_HEAD="$(git rev-parse HEAD)"
printf 'RUNNABLE_TARGET_SOURCE_SHA=%s\n' "$TARGET_SOURCE_SHA"
printf 'RUNNABLE_ACTUAL_HEAD=%s\n' "$ACTUAL_HEAD"
printf 'RUNNABLE_EXPECT=%s\n' "$RUNNABLE_EXPECT"

if ! git cat-file -e "$TARGET_SOURCE_SHA^{commit}" 2>/dev/null; then
  printf 'BLOCKED: target source SHA is not present in this checkout\n' >&2
  exit 2
fi

if ! git merge-base --is-ancestor "$TARGET_SOURCE_SHA" HEAD; then
  printf 'BLOCKED: target source SHA is not an ancestor of current HEAD\n' >&2
  exit 3
fi

ALLOWED_DIFF_RE='^(tools/runnable_m044_clean_run\.sh|tools/runnable_receipt_verifier\.py|tests/runnable/.*|docs/audits/RUNNABLE_M044_.*|docs/handoffs/PF_M044_RUNNABLE_.*)$'
UNEXPECTED_DIFF="$(git diff --name-only "$TARGET_SOURCE_SHA"...HEAD | grep -Ev "$ALLOWED_DIFF_RE" || true)"
if [[ -n "$UNEXPECTED_DIFF" ]]; then
  printf 'BLOCKED: product/evidence source differs from pinned target beyond Runnable-only files:\n%s\n' "$UNEXPECTED_DIFF" >&2
  exit 4
fi

if [[ -n "$(git status --porcelain)" ]]; then
  printf 'BLOCKED: working tree is not clean\n' >&2
  git status --short >&2
  exit 5
fi

python3 --version
node --version
npm --version

python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests/runnable -p 'test_*.py' -v
node --test tests/scorecore.test.cjs tests/m044-session.test.cjs

EVIDENCE_DIR="$(mktemp -d)"
trap 'rm -rf "$EVIDENCE_DIR" .runnable_independent_pre_pending.py independent_pre_pending_result.json' EXIT
node tools/m044_probe.cjs "$EVIDENCE_DIR/m044-probe"

PYTHONPATH=tools:tests python3 -m unittest -v \
  test_m044_operations.OperationTests.test_malformed_historical_wav_rejected \
  test_m044_operations.OperationTests.test_crash_before_history_bind_recovers_without_replay

git show "${REPRO_COMMIT}:${REPRO_PATH}" > .runnable_independent_pre_pending.py
PYTHONPATH=tools:tests python3 .runnable_independent_pre_pending.py | tee "$EVIDENCE_DIR/early-crash.log"
cp independent_pre_pending_result.json "$EVIDENCE_DIR/independent_pre_pending_result.json"

python3 - <<'PY' "$EVIDENCE_DIR/independent_pre_pending_result.json"
import json, sys
p = sys.argv[1]
r = json.load(open(p, 'r', encoding='utf-8'))
for key in ('verdict','historyOccurrences','R2StillCurrent','artifactHashValid','artifactDecodeValid','pendingRecords'):
    print(f'{key}={r.get(key)!r}')
PY

python3 tools/runnable_receipt_verifier.py \
  "$EVIDENCE_DIR/independent_pre_pending_result.json" \
  --mode "$RUNNABLE_EXPECT"

if [[ "$RUNNABLE_EXPECT" == "known-bad" ]]; then
  printf 'RUNNABLE_M044_NEGATIVE_CONTROL=PASS\n'
else
  printf 'RUNNABLE_M044_CLEAN_RUN=PASS\n'
fi
printf 'EVIDENCE_DIR=%s\n' "$EVIDENCE_DIR"
