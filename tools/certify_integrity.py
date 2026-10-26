#!/usr/bin/env python3
"""Verify manifest_registry.json entries against on-disk bytes.

Proves: content identity for each registered path (file exists + sha256 match).
Prefer content_path / absolute_path pointing at immutable objects/<sha>/ stores.
Does NOT prove: immutability of the registry file itself, artistic quality, or schema validity.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = ROOT / "workspace" / "studio_exports" / "manifest_registry.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_entry_path(entry: dict) -> Path:
    for key in ("content_path", "absolute_path", "object_path"):
        val = entry.get(key)
        if val:
            return Path(str(val))
    return Path("")


def main() -> int:
    ledger_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LEDGER
    print("=" * 72)
    print(" INTEGRITY LEDGER VERIFIER")
    print("=" * 72)
    print(f"Ledger: {ledger_path}")
    if not ledger_path.is_file():
        print("FAIL: ledger missing (exit 2)")
        return 2
    try:
        entries = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: ledger not JSON — {e}")
        return 2
    if not isinstance(entries, list):
        print("FAIL: ledger root must be a list")
        return 2
    if not entries:
        print("WARN: empty ledger")
        return 0

    fails = 0
    for i, e in enumerate(entries):
        path = resolve_entry_path(e)
        expected = str(e.get("sha256_checksum") or e.get("content_sha256") or "").replace("sha256:", "")
        name = e.get("filename") or e.get("artifact_id") or f"entry-{i}"
        print(f"\n[{i}] {name}")
        if not path.is_file():
            print(f"  ❌ MISSING FILE: {path}")
            fails += 1
            continue
        actual = sha256_file(path)
        if actual != expected:
            print(f"  ❌ DIGEST MISMATCH")
            print(f"     expected {expected}")
            print(f"     actual   {actual}")
            fails += 1
        else:
            size = path.stat().st_size
            print(f"  ✓ identity match sha256:{actual[:16]}… ({size} bytes)")
            recorded = e.get("bytes_written")
            if recorded is not None and int(recorded) != size:
                print(f"  · size note: ledger bytes_written={recorded} disk={size}")
    print("\n" + "=" * 72)
    if fails:
        print(f" ❌ INTEGRITY FAIL ({fails} entries)")
        print("=" * 72)
        return 1
    print(" ✅ INTEGRITY PASS (all registered files match digests)")
    print("=" * 72)
    print("Ceiling: content identity only — not registry immutability or media quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
