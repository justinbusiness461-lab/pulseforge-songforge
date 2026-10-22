#!/usr/bin/env python3
"""
PULSEFORGE OTIO schema compliance harness
Validates Timeline.1 / Stack.1 / Track / Clip.1 / Gap.1 structure and telemetry metadata.
Accepts *.otio and *.otio.json under workspace/studio_exports/otio_packages/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXPORT_DIR = Path(__file__).resolve().parent.parent / "workspace" / "studio_exports" / "otio_packages"


def audit_file(path: Path) -> bool:
    print(f"\n[Certifier] Analyzing: {path.name}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as err:
        print(f" ❌ Parse Exception: {err}")
        return False

    ok = True

    if doc.get("OTIO_SCHEMA") != "Timeline.1":
        print(" ❌ Schema Failure: root must be Timeline.1")
        ok = False
    else:
        print("  ✓ OTIO Schema Root Signature: COMPLIANT")

    if "name" not in doc:
        print(" ❌ Missing timeline name")
        ok = False

    tracks_stack = doc.get("tracks") or {}
    if tracks_stack.get("OTIO_SCHEMA") not in ("Stack.1", "Track.1"):
        print(" ❌ Layout Failure: tracks must be Stack.1 or Track.1")
        ok = False
    else:
        print(f"  ✓ Tracks hierarchy: {tracks_stack.get('OTIO_SCHEMA')}")

    children = tracks_stack.get("children") or []
    if not children:
        print(" ❌ Channel Failure: no track children")
        ok = False
    else:
        print(f"  ✓ Active tracks: {len(children)}")

    for ti, track in enumerate(children):
        if not isinstance(track, dict):
            print(f" ❌ Track[{ti}] not an object")
            ok = False
            continue
        elements = track.get("children") or []
        print(f"  ✓ Track[{ti}] '{track.get('name')}' | elements: {len(elements)}")
        for element in elements:
            if not isinstance(element, dict):
                continue
            schema_type = element.get("OTIO_SCHEMA")
            name = element.get("name")
            if schema_type == "Clip.1":
                metadata = element.get("metadata") or {}
                if "vocal_role_contract" not in metadata and "bars" not in metadata:
                    print(f"    · Clip '{name}' (no vocal_role_contract — acceptable if instrumental)")
                else:
                    role = metadata.get("vocal_role_contract", metadata.get("bars", ""))
                    print(f"    - Clip certified: '{name}' | meta: {role}")
            elif schema_type == "Gap.1":
                print(f"    - Gap certified: '{name}'")
            elif schema_type == "Marker.1":
                print(f"    - Marker: '{name}'")

    meta_stack = tracks_stack.get("metadata") or {}
    meta_root = doc.get("metadata") or {}
    pf = meta_root.get("pulseforge") or {}
    onset = (
        meta_stack.get("extracted_transient_onset_count")
        or pf.get("extracted_transient_onset_count")
        or pf.get("onset_count")
    )
    if onset is not None:
        print(f"  ✓ Telemetry: onset_count={onset}")
    else:
        print("  · Telemetry: no onset_count (optional if pre-flux export)")

    return ok


def main() -> int:
    print("=" * 72)
    print(" PULSEFORGE OTIO SCHEMA COMPLIANCE HARNESS")
    print("=" * 72)

    targets = []
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    elif EXPORT_DIR.is_dir():
        targets = sorted(EXPORT_DIR.glob("*.otio")) + sorted(EXPORT_DIR.glob("*.otio.json")) + sorted(
            EXPORT_DIR.glob("*.json")
        )

    if not targets:
        print(f"[Certifier] No packages under {EXPORT_DIR}")
        print(" -> Export OTIO Package from the UI first.")
        return 2

    all_ok = True
    for t in targets:
        if not audit_file(t):
            all_ok = False

    print("\n" + "=" * 72)
    if all_ok:
        print(" ✅ OTIO MANIFEST PACKAGES CERTIFIED PASS")
        print("=" * 72)
        return 0
    print(" ❌ CERTIFICATION COMPLIANCE REJECTED")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
