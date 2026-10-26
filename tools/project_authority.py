"""Durable project authority for Sound Forge (Mission 042).

Browser localStorage is cache only. Canonical chain:

  ProjectManifest.currentRevisionId
    → ProjectRevision
      → songSpecDigest / productionTimelineDigest / lyricTimelineDigest
      → outputArtifactIds[]

Writes use compare-and-set on currentRevisionId.
currentRevisionId advances only after revision payload is durable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FORMAT_VERSION = "1.0.0"
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_obj(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _digest_bytes(raw)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".proj-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            dfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _validate_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError(f"invalid {label}")
    return value


class ProjectStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _manifest_path(self, project_id: str) -> Path:
        return self.root / project_id / "ProjectManifest.json"

    def _revision_path(self, project_id: str, revision_id: str) -> Path:
        return self.root / project_id / "revisions" / f"{revision_id}.json"

    def create_project(self, project_id: str | None = None) -> dict:
        pid = _validate_id(project_id or f"prj-{secrets.token_hex(8)}", "projectId")
        mpath = self._manifest_path(pid)
        if mpath.exists():
            raise ValueError("project already exists")
        rid = f"rev-{secrets.token_hex(8)}"
        revision = {
            "revisionId": rid,
            "parentRevisionId": None,
            "songSpecDigest": None,
            "productionTimelineDigest": None,
            "lyricTimelineDigest": None,
            "sourceAssetDigests": [],
            "outputArtifactIds": [],
            "createdAt": _utc(),
            "formatVersion": FORMAT_VERSION,
        }
        manifest = {
            "projectId": pid,
            "currentRevisionId": rid,
            "formatVersion": FORMAT_VERSION,
            "createdAt": _utc(),
            "updatedAt": _utc(),
        }
        _atomic_write(self._revision_path(pid, rid), json.dumps(revision, indent=2).encode())
        _atomic_write(mpath, json.dumps(manifest, indent=2).encode())
        return {"manifest": manifest, "revision": revision}

    def get_manifest(self, project_id: str) -> dict:
        pid = _validate_id(project_id, "projectId")
        path = self._manifest_path(pid)
        if not path.is_file():
            raise FileNotFoundError("project not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("projectId") != pid:
            raise ValueError("corrupt manifest")
        return data

    def get_revision(self, project_id: str, revision_id: str) -> dict:
        pid = _validate_id(project_id, "projectId")
        rid = _validate_id(revision_id, "revisionId")
        path = self._revision_path(pid, rid)
        if not path.is_file():
            raise FileNotFoundError("revision not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("revisionId") != rid:
            raise ValueError("corrupt revision")
        return data

    def commit_revision(
        self,
        project_id: str,
        *,
        expected_current_revision_id: str,
        parent_revision_id: str,
        song_spec: dict | None = None,
        production_timeline: dict | None = None,
        lyric_timeline: dict | None = None,
        source_asset_digests: list | None = None,
        output_artifact_ids: list | None = None,
    ) -> dict:
        pid = _validate_id(project_id, "projectId")
        expected = _validate_id(expected_current_revision_id, "expectedCurrentRevisionId")
        parent = _validate_id(parent_revision_id, "parentRevisionId")
        manifest = self.get_manifest(pid)
        if manifest["currentRevisionId"] != expected:
            raise ValueError(
                f"stale_revision: current={manifest['currentRevisionId']} expected={expected}"
            )
        if parent != expected:
            raise ValueError("parent_must_equal_expected_current")
        self.get_revision(pid, parent)

        new_id = f"rev-{secrets.token_hex(8)}"
        revision = {
            "revisionId": new_id,
            "parentRevisionId": parent,
            "songSpecDigest": _digest_obj(song_spec) if song_spec is not None else None,
            "productionTimelineDigest": _digest_obj(production_timeline)
            if production_timeline is not None
            else None,
            "lyricTimelineDigest": _digest_obj(lyric_timeline) if lyric_timeline is not None else None,
            "sourceAssetDigests": list(source_asset_digests or []),
            "outputArtifactIds": list(output_artifact_ids or []),
            "createdAt": _utc(),
            "formatVersion": FORMAT_VERSION,
            "songSpec": song_spec,
            "productionTimeline": production_timeline,
            "lyricTimeline": lyric_timeline,
        }
        _atomic_write(self._revision_path(pid, new_id), json.dumps(revision, indent=2).encode())
        manifest2 = self.get_manifest(pid)
        if manifest2["currentRevisionId"] != expected:
            raise ValueError(
                f"stale_revision_race: current={manifest2['currentRevisionId']} expected={expected}"
            )
        manifest2["currentRevisionId"] = new_id
        manifest2["updatedAt"] = _utc()
        _atomic_write(self._manifest_path(pid), json.dumps(manifest2, indent=2).encode())
        return {"manifest": manifest2, "revision": revision}

    def bind_output(
        self,
        project_id: str,
        revision_id: str,
        artifact_id: str,
        *,
        expected_current_revision_id: str | None = None,
    ) -> dict:
        pid = _validate_id(project_id, "projectId")
        rid = _validate_id(revision_id, "revisionId")
        art = _validate_id(artifact_id, "artifactId")
        manifest = self.get_manifest(pid)
        if expected_current_revision_id is not None:
            if manifest["currentRevisionId"] != expected_current_revision_id:
                raise ValueError("stale_revision")
        if rid != manifest["currentRevisionId"]:
            raise ValueError("can_only_bind_output_to_current_revision")
        rev = self.get_revision(pid, rid)
        outs = list(rev.get("outputArtifactIds") or [])
        if art not in outs:
            outs.append(art)
        rev["outputArtifactIds"] = outs
        _atomic_write(self._revision_path(pid, rid), json.dumps(rev, indent=2).encode())
        return rev

    def reopen(self, project_id: str) -> dict:
        manifest = self.get_manifest(project_id)
        revision = self.get_revision(project_id, manifest["currentRevisionId"])
        return {
            "manifest": manifest,
            "revision": revision,
            "authority": "durable_disk",
            "browserCacheRole": "ignored",
        }
