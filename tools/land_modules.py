#!/usr/bin/env python3
"""Reconstruct exact engine modules from base64 parts; verify SHA-256."""
from __future__ import annotations
import base64, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = Path(__file__).resolve().parent / "_payloads"
MANIFEST = PAYLOAD / "MANIFEST.json"

def main() -> int:
    man = json.loads(MANIFEST.read_text())
    fail = 0
    for rel, meta in man.items():
        parts = []
        for p in meta["parts"]:
            parts.append((PAYLOAD / p).read_text())
        raw = base64.b64decode("".join(parts))
        digest = hashlib.sha256(raw).hexdigest()
        if digest != meta["sha256"]:
            print(f"FAIL {rel}: expected {meta['sha256']}, got {digest}")
            fail += 1
            continue
        if len(raw) != meta["bytes"]:
            print(f"FAIL {rel}: size {len(raw)} != {meta['bytes']}")
            fail += 1
            continue
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print(f"PASS {rel}: {len(raw)} bytes sha256:{digest[:16]}…")
    return 1 if fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
