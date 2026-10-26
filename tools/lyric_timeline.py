"""Mission 043 — sample-bound LyricTimeline authority.

A lyric model produces evidence. It does not own lyric truth.
Timing authority is integer sample coordinates, half-open [start, end).
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

FORMAT = "1.0.0"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".lyric-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def validate_range(start: int, end: int, frame_count: int) -> None:
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("sample coordinates must be integers")
    if start < 0 or end < 0:
        raise ValueError("negative sample coordinate")
    if not (0 <= start < end <= frame_count):
        raise ValueError(f"invalid half-open range [{start},{end}) for frames={frame_count}")


def validate_timeline(doc: dict, *, frame_count: int, source_digest: str) -> None:
    if doc.get("sourceAudioDigest") != source_digest:
        raise ValueError("wrong source audio digest")
    if int(doc.get("sourceSampleRate") or 0) <= 0:
        raise ValueError("sourceSampleRate required")
    words = doc.get("words") or []
    if not isinstance(words, list):
        raise ValueError("words must be list")
    last_end = 0
    for w in words:
        validate_range(int(w["decodedSampleStart"]), int(w["decodedSampleEnd"]), frame_count)
        if int(w["decodedSampleStart"]) < last_end:
            raise ValueError("overlapping or out-of-order words")
        last_end = int(w["decodedSampleEnd"])
        conf = w.get("confidence")
        if conf is not None and not (0.0 <= float(conf) <= 1.0):
            raise ValueError("confidence out of range")
        if conf is not None and float(conf) >= 0.5 and not doc.get("alignmentModelOrMethod"):
            raise ValueError("confidence requires alignmentModelOrMethod")
    for p in doc.get("phrases") or []:
        validate_range(int(p["decodedSampleStart"]), int(p["decodedSampleEnd"]), frame_count)


class LyricStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str, revision_id: str) -> Path:
        return self.root / project_id / "lyrics" / f"{revision_id}.json"

    def create_machine_r1(
        self,
        project_id: str,
        *,
        source_audio_digest: str,
        source_sample_rate: int,
        frame_count: int,
        words: list[dict],
        phrases: list[dict] | None = None,
        language: str = "en",
        alignment_model_or_method: str,
        evidence_artifact_id: str | None = None,
    ) -> dict:
        rid = f"ltr-{secrets.token_hex(8)}"
        doc = {
            "formatVersion": FORMAT,
            "sourceAudioDigest": source_audio_digest,
            "sourceSampleRate": int(source_sample_rate),
            "decodedFrameCount": int(frame_count),
            "revisionId": rid,
            "parentRevisionId": None,
            "language": language,
            "alignmentModelOrMethod": alignment_model_or_method,
            "evidenceArtifactId": evidence_artifact_id or source_audio_digest[:16],
            "phrases": phrases
            or [
                {
                    "text": " ".join(w["text"] for w in words),
                    "decodedSampleStart": words[0]["decodedSampleStart"],
                    "decodedSampleEnd": words[-1]["decodedSampleEnd"],
                }
            ]
            if words
            else [],
            "words": words,
            "confidence": None,
            "correctionHistory": [],
            "createdAt": _utc(),
        }
        validate_timeline(doc, frame_count=frame_count, source_digest=source_audio_digest)
        _atomic(self._path(project_id, rid), json.dumps(doc, indent=2).encode())
        doc["digest"] = _digest({k: doc[k] for k in doc if k != "digest"})
        return doc

    def correct_word(
        self,
        project_id: str,
        *,
        parent_revision_id: str,
        word_index: int,
        new_text: str,
        corrected_by: str = "user",
        reason: str = "intentional_correction",
        expected_parent_digest: str | None = None,
    ) -> dict:
        parent_path = self._path(project_id, parent_revision_id)
        if not parent_path.is_file():
            raise FileNotFoundError("parent lyric revision missing")
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        if expected_parent_digest and _digest({k: parent[k] for k in parent if k != "digest"}) != expected_parent_digest:
            raise ValueError("stale_lyric_parent")
        words = [dict(w) for w in parent["words"]]
        if word_index < 0 or word_index >= len(words):
            raise ValueError("word_index out of range")
        old = words[word_index]["text"]
        words[word_index]["text"] = new_text
        words[word_index]["confidence"] = 1.0
        rid = f"ltr-{secrets.token_hex(8)}"
        history = list(parent.get("correctionHistory") or [])
        history.append(
            {
                "fromRevisionId": parent_revision_id,
                "wordIndex": word_index,
                "fromText": old,
                "toText": new_text,
                "correctedBy": corrected_by,
                "reason": reason,
                "at": _utc(),
            }
        )
        doc = {
            "formatVersion": FORMAT,
            "sourceAudioDigest": parent["sourceAudioDigest"],
            "sourceSampleRate": parent["sourceSampleRate"],
            "decodedFrameCount": parent["decodedFrameCount"],
            "revisionId": rid,
            "parentRevisionId": parent_revision_id,
            "language": parent["language"],
            "alignmentModelOrMethod": parent["alignmentModelOrMethod"],
            "evidenceArtifactId": parent["evidenceArtifactId"],
            "phrases": [
                {
                    "text": " ".join(w["text"] for w in words),
                    "decodedSampleStart": words[0]["decodedSampleStart"],
                    "decodedSampleEnd": words[-1]["decodedSampleEnd"],
                }
            ],
            "words": words,
            "confidence": None,
            "correctionHistory": history,
            "createdAt": _utc(),
        }
        validate_timeline(
            doc,
            frame_count=int(doc["decodedFrameCount"]),
            source_digest=doc["sourceAudioDigest"],
        )
        _atomic(self._path(project_id, rid), json.dumps(doc, indent=2).encode())
        doc["digest"] = _digest({k: doc[k] for k in doc if k != "digest"})
        return doc

    def get(self, project_id: str, revision_id: str) -> dict:
        path = self._path(project_id, revision_id)
        if not path.is_file():
            raise FileNotFoundError("lyric revision not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def instrumental_r1(
        self,
        project_id: str,
        *,
        source_audio_digest: str,
        source_sample_rate: int,
        frame_count: int,
    ) -> dict:
        rid = f"ltr-{secrets.token_hex(8)}"
        doc = {
            "formatVersion": FORMAT,
            "sourceAudioDigest": source_audio_digest,
            "sourceSampleRate": int(source_sample_rate),
            "decodedFrameCount": int(frame_count),
            "revisionId": rid,
            "parentRevisionId": None,
            "language": "und",
            "alignmentModelOrMethod": "instrumental_null_v1",
            "evidenceArtifactId": source_audio_digest[:16],
            "phrases": [],
            "words": [],
            "confidence": 0.0,
            "correctionHistory": [],
            "status": "no_vocal_detected",
            "createdAt": _utc(),
        }
        _atomic(self._path(project_id, rid), json.dumps(doc, indent=2).encode())
        doc["digest"] = _digest({k: doc[k] for k in doc if k != "digest"})
        return doc
