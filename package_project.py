#!/usr/bin/env python3
"""Release packager: checksum core assets and zip a deployable studio bundle."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone

REQUIRED = [
    "index.html",
    "app-core.js",
    "app-ui.js",
    "app-cinema.js",
    "manifest.json",
    "service-worker.js",
]

OPTIONAL = [
    "README.md",
    "INSTALL.md",
    "icons/icon.svg",
    "icons/icon-192.png",
    "icons/icon-512.png",
    "tools/armature_solver.py",
    "tools/test_harness.py",
    "tools/README.md",
    "tools/studio_server.py",
    "tools/vocal_lab.py",
    "tools/certify_otio.py",
    "tools/certify_integrity.py",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def execute_release_packaging(target_directory: str = ".") -> bool:
    archive_name = "SoundForge-Studio-Release-v2.18.zip"
    manifest_name = "Release-Provenance-Manifest.json"

    os.makedirs("models/vocal", exist_ok=True)
    open("models/vocal/.gitkeep", "a").close()
    print(f"[Packager] Scanning {os.path.abspath(target_directory)}")
    provenance = {
        "release_version": "2.18.0",
        "compiled_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checksums": {},
    }

    for asset in REQUIRED:
        path = os.path.join(target_directory, asset)
        if not os.path.exists(path):
            print(f"Error: missing required asset: {asset}")
            return False
        digest = sha256_file(path)
        provenance["checksums"][asset] = f"sha256:{digest}"
        print(f"  OK  {asset:<22} sha256:{digest[:16]}…")

    for asset in OPTIONAL:
        path = os.path.join(target_directory, asset)
        if os.path.exists(path):
            digest = sha256_file(path)
            provenance["checksums"][asset] = f"sha256:{digest}"
            print(f"  +   {asset:<22} sha256:{digest[:16]}…")

    man_path = os.path.join(target_directory, manifest_name)
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)

    out_path = os.path.join(target_directory, archive_name)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for asset in REQUIRED:
            zf.write(os.path.join(target_directory, asset), asset)
        for asset in OPTIONAL:
            path = os.path.join(target_directory, asset)
            if os.path.exists(path):
                zf.write(path, asset)
        zf.write(man_path, manifest_name)

    print(f"\n[Packager] Wrote {archive_name}")
    print(f"[Packager] Manifest {manifest_name}\n")
    return True


if __name__ == "__main__":
    ok = execute_release_packaging(".")
    raise SystemExit(0 if ok else 1)
