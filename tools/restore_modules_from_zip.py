#!/usr/bin/env python3
"""Extract the five engine modules from SoundForge-Studio-Release-v2.18.zip and verify SHA-256."""
from __future__ import annotations
import hashlib, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_NAME = "SoundForge-Studio-Release-v2.18.zip"
EXPECTED = {
    "app-core.js": ("36a2cb365c5aec48c133b7e7b90ab3dec1b9aa31d05805aa5662ac7bb3f47ab8", 36957),
    "app-ui.js": ("e523340c4bf1a262e343859727cb62d135061325722ecfa5b5ebf44f5dcda3db", 34151),
    "app-cinema.js": ("846f64bc74b75280f285699082f21671df93833767977567d0d7e850203f62ed", 8987),
    "tools/studio_server.py": ("39c3c7c577b8eae53c65397298d9243682e27013fdae89909011c958581f6458", 11431),
    "tools/vocal_lab.py": ("2b7ddfc779eca371d584142a085c1463388965ffcdc6b0a79d30ceaa82c788fe", 17510),
}

def main() -> int:
    zpath = ROOT / ZIP_NAME
    if not zpath.is_file():
        print(f"FAIL: {ZIP_NAME} not found next to repo root", file=sys.stderr)
        return 2
    fail = 0
    with zipfile.ZipFile(zpath) as zf:
        for rel, (sha, nbytes) in EXPECTED.items():
            data = zf.read(rel)
            h = hashlib.sha256(data).hexdigest()
            if h != sha or len(data) != nbytes:
                print(f"FAIL {rel}: got {len(data)}/{h}")
                fail += 1
                continue
            out = ROOT / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"PASS {rel}: {len(data)} bytes {h[:16]}…")
    return 1 if fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
