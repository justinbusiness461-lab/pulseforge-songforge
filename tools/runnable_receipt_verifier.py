#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

class ReceiptError(ValueError):
    pass

def _required(receipt, key):
    if key not in receipt:
        raise ReceiptError(f'missing required fact: {key}')
    return receipt[key]

def verify_candidate_receipt(receipt):
    checks = [
        ('verdict', _required(receipt, 'verdict') == 'PASS', "must equal PASS"),
        ('historyOccurrences', _required(receipt, 'historyOccurrences') == 1, "must equal 1"),
        ('artifactHashValid', _required(receipt, 'artifactHashValid') is True, "must be true"),
        ('artifactDecodeValid', _required(receipt, 'artifactDecodeValid') is True, "must be true"),
        ('R2StillCurrent', _required(receipt, 'R2StillCurrent') is True, "must be true"),
        ('pendingRecords', _required(receipt, 'pendingRecords') in {0}, "must be an allowed terminal value (0)"),
        ('duplicateR1Binding', _required(receipt, 'duplicateR1Binding') is False, "must be false"),
        ('phantomProjectRevision', _required(receipt, 'phantomProjectRevision') is False, "must be false"),
        ('R2OutputMutated', _required(receipt, 'R2OutputMutated') is False, "must be false"),
    ]
    failures = [f'{k} {reason}; observed={receipt.get(k)!r}' for k, ok, reason in checks if not ok]
    if failures:
        raise ReceiptError('; '.join(failures))
    return True

def verify_known_bad_receipt(receipt):
    required = {
        'verdict': 'FAIL',
        'historyOccurrences': 0,
        'artifactHashValid': True,
        'artifactDecodeValid': True,
        'R2StillCurrent': True,
        'pendingRecords': 0,
    }
    failures = []
    for key, expected in required.items():
        observed = _required(receipt, key)
        if observed != expected:
            failures.append(f'{key} expected {expected!r}; observed={observed!r}')
    if failures:
        raise ReceiptError('negative control mismatch: ' + '; '.join(failures))
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument('receipt')
    p.add_argument('--mode', choices=('candidate', 'known-bad'), required=True)
    args = p.parse_args()
    receipt = json.loads(Path(args.receipt).read_text(encoding='utf-8'))
    try:
        if args.mode == 'candidate':
            verify_candidate_receipt(receipt)
        else:
            verify_known_bad_receipt(receipt)
    except ReceiptError as exc:
        print(f'RUNNABLE_RECEIPT_VERIFIER=FAIL: {exc}')
        raise SystemExit(20)
    print(f'RUNNABLE_RECEIPT_VERIFIER=PASS mode={args.mode}')

if __name__ == '__main__':
    main()
