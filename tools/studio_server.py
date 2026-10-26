#!/usr/bin/env python3
"""S.A.R.A. Sound Forge local studio server — PWA + disk writes + hybrid + vocal lab."""
from __future__ import annotations

import http.server
import json
import math
import os
import socketserver
import struct
import sys
from pathlib import Path
from urllib.parse import unquote

PORT = int(os.environ.get("STUDIO_PORT", "8765"))
ROOT = Path(__file__).resolve().parent.parent
EXPORT_ROOT = ROOT / "workspace" / "studio_exports"

import hashlib
from datetime import datetime, timezone

MANIFEST_LOG_PATH = EXPORT_ROOT / "manifest_registry.json"


# M040: exact-origin admission, per-process capability, immutable export objects.
import secrets
import fcntl
import tempfile
import re
from urllib.parse import urlsplit

CAPABILITY = secrets.token_urlsafe(32)
MAX_REQUEST = 64 * 1024 * 1024
MAX_ARTIFACT = 16 * 1024 * 1024

def authorized_origin(origin, host):
    if host not in {f"localhost:{PORT}", f"127.0.0.1:{PORT}"} or not origin:
        return False
    try:
        u = urlsplit(origin)
        return (u.scheme == "http" and u.netloc == host and u.hostname in {"localhost", "127.0.0.1"}
                and u.port == PORT and not u.username and not u.password
                and not u.path and not u.query and not u.fragment)
    except (ValueError, TypeError):
        return False

def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def durable_mkdir(path):
    if path.exists():
        if path.is_symlink() or not path.is_dir(): raise ValueError("unsafe directory")
        return
    durable_mkdir(path.parent)
    path.mkdir(mode=0o700)
    sync_dir(path.parent)

def atomic_write_bytes(path, data):
    durable_mkdir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path); sync_dir(path.parent)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def persist_export(root, filename, subdirectory, data):
    root=Path(root).resolve(); durable_mkdir(root)
    fd=os.open(root/".export.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        return _persist_export_locked(root,filename,subdirectory,data)
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

def _persist_export_locked(root, filename, subdirectory, data):
    # Friendly names never designate authority and never accept path syntax.
    for value in (filename, subdirectory):
        if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}",value) or value in {".",".."}:
            raise ValueError("invalid export name")
    if len(data)>MAX_ARTIFACT: raise ValueError("artifact too large")
    root=Path(root).resolve(); durable_mkdir(root)
    digest=hashlib.sha256(data).hexdigest()
    directory=root/"objects"/digest[:2]; durable_mkdir(directory)
    obj=directory/digest
    if obj.exists():
        if obj.is_symlink() or obj.read_bytes()!=data: raise ValueError("immutable object corruption")
    else:
        atomic_write_bytes(obj,data)
    ledger_path=root/"manifest_registry.json"
    registry=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    if not isinstance(registry,list): raise ValueError("invalid existing ledger")
    row={"timestamp":datetime.now(timezone.utc).isoformat(),"filename":filename,"subdirectory":subdirectory,
         "absolute_path":str(obj),"sha256_checksum":"sha256:"+digest,"bytes_written":len(data)}
    registry.append(row)
    atomic_write_bytes(ledger_path,json.dumps(registry,indent=2).encode())
    # Pointer changes only after object and ledger have crossed durability barriers.
    alias_dir=root/"aliases"/subdirectory; durable_mkdir(alias_dir)
    alias=alias_dir/(filename+".json")
    atomic_write_bytes(alias,json.dumps({"sha256":digest,"object_path":str(obj)}).encode())
    return {"status":"SUCCESS","saved_at":str(obj),"alias_at":str(alias),"sha256":digest,"bytes":len(data)}


# M042: one durable project pointer, immutable revision history and fenced saves.
class ProjectConflict(ValueError):
    pass


def project_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def project_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
        raise ValueError("invalid projectId")
    return value


def artifact_bytes(root, digest):
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("invalid artifact digest")
    path = root / "objects" / digest[:2] / digest
    if path.is_symlink() or not path.is_file():
        raise ValueError("referenced artifact unavailable")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("referenced artifact corruption")
    return data


def project_boundary(name):
    """Internal fault-injection seam; not controllable by HTTP callers."""
    pass


def project_namespace_fence(path, boundary):
    # Existing-but-unflushed directories from a killed earlier process also count.
    while True:
        sync_dir(path)
        if path == boundary: break
        if path == path.parent: raise ValueError("namespace boundary escaped")
        path = path.parent


def project_artifact_fence(root, digest):
    artifact_bytes(root, digest)
    path = root / "objects" / digest[:2] / digest
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    project_namespace_fence(path.parent, root.parent)


def project_revision(root, directory, pid, rid):
    if not isinstance(rid, str) or not re.fullmatch(r"[a-f0-9]{64}", rid):
        raise ValueError("invalid revisionId")
    path = directory / "revisions" / (rid + ".json")
    if path.is_symlink(): raise ValueError("unsafe revision path")
    revision = json.loads(path.read_text())
    core = {k: v for k, v in revision.items() if k != "revisionId"}
    if revision.get("projectId") != pid or revision.get("revisionId") != rid or hashlib.sha256(project_json(core)).hexdigest() != rid:
        raise ValueError("revision identity mismatch")
    spec = json.loads(artifact_bytes(root, revision["songSpecDigest"]))
    timeline = json.loads(artifact_bytes(root, revision["productionTimelineDigest"]))
    if timeline["songSpecDigest"] != revision["songSpecDigest"]:
        raise ValueError("timeline source mismatch")
    for aid in revision["sourceAssetDigests"] + revision["outputArtifactIds"]:
        artifact_bytes(root, aid)
    return revision, spec, timeline


def project_operation(root, request, commit=False):
    import uuid
    root = Path(root).resolve()
    pid = request.get("projectId")
    if pid is None:
        if not commit or request.get("expectedCurrentRevisionId") is not None:
            raise ValueError("projectId required")
        pid = uuid.uuid4().hex
    pid = project_id(pid)
    directory = root / "projects" / pid
    if not commit and not directory.is_dir(): raise ValueError("unknown project")
    durable_mkdir(directory)
    fd = os.open(directory / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        path = directory / "ProjectManifest.json"
        if path.is_symlink(): raise ValueError("unsafe manifest path")
        manifest = json.loads(path.read_text()) if path.exists() else None
        current = manifest["currentRevisionId"] if manifest else None
        if manifest and (manifest.get("projectId") != pid or manifest.get("formatVersion") != 1):
            raise ValueError("invalid project manifest")
        if not commit:
            if not manifest: raise ValueError("project has no committed revision")
            rid = request.get("revisionId") or current
            ancestor, seen = current, set()
            while ancestor != rid:
                if ancestor is None or ancestor in seen:
                    raise ValueError("revision is not in committed project history")
                seen.add(ancestor)
                previous, _, _ = project_revision(root, directory, pid, ancestor)
                ancestor = previous["parentRevisionId"]
            revision, spec, timeline = project_revision(root, directory, pid, rid)
            return {"status": "SUCCESS", "manifest": manifest, "revision": revision, "songSpec": spec, "productionTimeline": timeline}
        if "expectedCurrentRevisionId" not in request or request["expectedCurrentRevisionId"] != current:
            raise ProjectConflict("stale project revision; reopen before saving")
        if current:
            # Fail closed if existing authority is corrupt; never overwrite it as a repair.
            project_revision(root, directory, pid, current)
        spec = request.get("songSpec")
        if not isinstance(spec, dict) or not isinstance(spec.get("tracks"), list) or (not isinstance(spec.get("structure"), dict) or not isinstance(spec["structure"].get("sections"), list)) or not isinstance(spec.get("timebase"), dict):
            raise ValueError("SongSpec required")
        if request.get("lyricTimelineDigest") is not None:
            raise ValueError("lyric revisions are not enabled in M042")
        sources = request.get("sourceAssetDigests", [])
        outputs = request.get("outputArtifactIds", [])
        if not isinstance(sources, list) or not isinstance(outputs, list) or len(sources) + len(outputs) > 128:
            raise ValueError("invalid artifact bindings")
        for aid in sources + outputs: artifact_bytes(root, aid)
        spec_bytes = project_json(spec)
        song_digest = persist_export(root, "SongSpec.json", "project-metadata", spec_bytes)["sha256"]
        timeline = {"formatVersion": 1, "songSpecDigest": song_digest, "timebase": spec["timebase"], "sections": spec["structure"]["sections"], "tracks": spec["tracks"]}
        timeline_digest = persist_export(root, "ProductionTimeline.json", "project-metadata", project_json(timeline))["sha256"]
        core = {"projectId": pid, "formatVersion": 1, "parentRevisionId": current,
                "songSpecDigest": song_digest, "productionTimelineDigest": timeline_digest,
                "lyricTimelineDigest": None, "sourceAssetDigests": sorted(set(sources)),
                "outputArtifactIds": sorted(set(outputs)), "createdAt": datetime.now(timezone.utc).isoformat(),
                "outputBindings": [{"artifactId": aid, "songSpecDigest": song_digest, "productionTimelineDigest": timeline_digest} for aid in sorted(set(outputs))]}
        rid = hashlib.sha256(project_json(core)).hexdigest()
        revision = {"revisionId": rid, **core}
        revisions = directory / "revisions"
        durable_mkdir(revisions)
        revision_path = revisions / (rid + ".json")
        if revision_path.exists(): raise ValueError("revision already exists")
        atomic_write_bytes(revision_path, project_json(revision))
        project_boundary("revision_durable_before_reread")
        # Verify exact references from disk, not from in-memory objects.
        project_revision(root, directory, pid, rid)
        for aid in [song_digest, timeline_digest] + sources + outputs:
            project_artifact_fence(root, aid)
        project_namespace_fence(revisions, root.parent)
        project_boundary("before_manifest_promotion")
        new_manifest = {"projectId": pid, "currentRevisionId": rid, "formatVersion": 1}
        atomic_write_bytes(path, project_json(new_manifest))
        project_boundary("after_manifest_promotion")
        if json.loads(path.read_text()) != new_manifest:
            raise ValueError("project manifest reread mismatch")
        return {"status": "SUCCESS", "manifest": new_manifest, "revision": revision, "songSpec": spec, "productionTimeline": timeline}
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def write_stereo_wav(path: Path, duration_sec: float = 8.0, bpm: float = 102.0) -> int:
    sample_rate = 44100
    n = int(sample_rate * duration_sec)
    frames = bytearray()
    beat = 60.0 / max(40.0, bpm)
    for s in range(n):
        t = s / sample_rate
        env = min(1.0, t * 4) * max(0.0, 1.0 - (t / duration_sec) * 0.85)
        phase = (t % beat) / beat
        kick = math.sin(2 * math.pi * (80 - 40 * phase) * t) * math.exp(-phase * 8) * 0.35
        bass = math.sin(2 * math.pi * 55 * t) * 0.2 * env
        hat = (1 if (s % max(1, int(sample_rate * beat / 4))) < 80 else 0) * 0.08
        mid = math.sin(2 * math.pi * 220 * t) * 0.06 * env
        l = kick + bass + hat + mid
        r = kick * 0.9 + bass * 1.05 + hat * 0.85 + mid * 1.1
        frames += struct.pack(
            "<hh",
            max(-32767, min(32767, int(l * 32767))),
            max(-32767, min(32767, int(r * 32767))),
        )
    data_size = len(frames)
    header = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, 2, sample_rate, sample_rate * 4, 4, 16)
    header += b"data" + struct.pack("<I", data_size)
    atomic_write_bytes(path, header + frames)
    return data_size


class StudioHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[Studio-Server] {fmt % args}")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        if authorized_origin(self.headers.get("Origin"), self.headers.get("Host")):
            self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
            self.send_header("Vary", "Origin")
        super().end_headers()

    def _host_allowed(self):
        return self.headers.get("Host") in {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}

    def do_GET(self):
        if not self._host_allowed(): return self._json(403,{"status":"ERROR","error":"host denied"})
        if self.headers.get("Origin") and not authorized_origin(self.headers["Origin"], self.headers["Host"]):
            return self._json(403,{"status":"ERROR","error":"origin denied"})
        path=unquote(self.path.split("?",1)[0])
        if path.startswith("/workspace") or path.startswith("/.git"):
            return self._json(403,{"status":"ERROR","error":"private storage"})
        if path in {"/","/index.html"}:
            # Fresh same-origin capability, never cached by the service worker.
            body=(ROOT/"index.html").read_text().replace("<head>","<head><script>window.__STUDIO_CAPABILITY__="+json.dumps(CAPABILITY)+";</script>").encode()
            self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body);return
        public={"/app-core.js","/app-ui.js","/app-chat.js","/app-cinema.js","/service-worker.js","/manifest.json","/icons/icon.svg","/icons/icon-192.png","/icons/icon-512.png"}
        if path not in public: return self._json(404,{"status":"ERROR","error":"not a public asset"})
        return super().do_GET()

    def do_OPTIONS(self):
        if not authorized_origin(self.headers.get("Origin"), self.headers.get("Host")):
            return self._json(403,{"status":"ERROR","error":"origin denied"})
        if self.headers.get("Access-Control-Request-Method") not in {"GET","POST"}:
            return self._json(403,{"status":"ERROR","error":"method denied"})
        requested={v.strip().lower() for v in self.headers.get("Access-Control-Request-Headers","").split(",") if v.strip()}
        if not requested <= {"content-type","x-studio-capability"}:
            return self._json(403,{"status":"ERROR","error":"headers denied"})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods","GET, POST")
        self.send_header("Access-Control-Allow-Headers","Content-Type, X-Studio-Capability")
        self.end_headers()

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        if authorized_origin(self.headers.get("Origin"), self.headers.get("Host")):
            self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not authorized_origin(self.headers.get("Origin"),self.headers.get("Host")):
            return self._json(403,{"status":"ERROR","error":"origin denied"})
        supplied=self.headers.get("X-Studio-Capability","")
        if not secrets.compare_digest(supplied,CAPABILITY):
            return self._json(403,{"status":"ERROR","error":"capability denied"})
        path = unquote(self.path.split("?",1)[0])
        try:
            if self.headers.get("Transfer-Encoding"): raise ValueError("transfer encoding unsupported")
            length=int(self.headers.get("Content-Length","-1"))
            if length<0 or length>MAX_REQUEST:
                return self._json(413,{"status":"ERROR","error":"request too large or missing length"})
            payload=json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload,dict): raise ValueError("object required")
        except (ValueError,UnicodeError):
            return self._json(400,{"status":"ERROR","error":"invalid request"})

        if path in {"/api/projects/commit", "/api/projects/open"}:
            try:
                return self._json(200, project_operation(EXPORT_ROOT, payload, commit=path.endswith("/commit")))
            except ProjectConflict as e:
                return self._json(409, {"status": "CONFLICT", "error": str(e)})
            except (ValueError, KeyError, TypeError, OSError):
                return self._json(400, {"status": "ERROR", "error": "invalid or unavailable project authority"})
        if path == "/api/write_production_file":
            self._handle_write(payload)
            return
        if path == "/api/dispatch_neural_compilation":
            self._handle_neural(payload)
            return
        if path == "/api/local_neural_vocal_synthesis":
            self._handle_vocal_lab(payload)
            return
        self.send_error(404, "Not found")

    def _handle_write(self, payload: dict):
        try:
            raw=payload.get("data_bytes")
            if isinstance(raw,str): data=raw.encode()
            elif isinstance(raw,list) and all(type(v) is int and 0<=v<=255 for v in raw): data=bytes(raw)
            else: raise ValueError("invalid data_bytes")
            receipt=persist_export(EXPORT_ROOT,payload.get("filename","export.bin"),payload.get("subdirectory","exports"),data)
            self._json(200,receipt)
        except ValueError as e: self._json(400,{"status":"ERROR","error":str(e)})
        except OSError: self._json(500,{"status":"ERROR","error":"storage failure"})

    def _handle_neural(self, request_data: dict):
        try:
            title = str(request_data.get("title") or "SARA_RELEASE_TRACK")
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:80]
            cfg = request_data.get("configuration") or {}
            bpm = float(cfg.get("target_bpm") or 102)
            scale = str(cfg.get("target_scale") or "F# minor")
            lyrics = str(request_data.get("lyrics") or "")
            prompt = str(request_data.get("prompt_directive") or "")
            masters = EXPORT_ROOT / "production_masters"
            otio_dir = EXPORT_ROOT / "otio_packages"
            masters.mkdir(parents=True, exist_ok=True)
            otio_dir.mkdir(parents=True, exist_ok=True)
            wav_path = masters / f"{safe}_broadcast_master.wav"
            otio_path = otio_dir / f"{safe}_broadcast_interchange.otio.json"
            duration = 8.0
            nbytes = write_stereo_wav(wav_path, duration_sec=duration, bpm=bpm)
            otio = {
                "OTIO_SCHEMA": "Timeline.1",
                "name": f"{title} Broadcast Master Timeline",
                "metadata": {
                    "neural_provider_attribution": "SARA_LOCAL_HYBRID_PROXY",
                    "model_version_pin": "local_deterministic_wav_proxy_v1",
                    "target_bpm": bpm,
                    "target_scale": scale,
                    "prompt_directive": prompt[:500],
                    "lyrics_character_count": len(lyrics),
                },
                "tracks": {
                    "OTIO_SCHEMA": "Stack.1",
                    "name": "Tracks Stack",
                    "children": [
                        {
                            "OTIO_SCHEMA": "Track.1",
                            "name": "Vocal Broadcast Channel",
                            "kind": "Video",
                            "children": [
                                {
                                    "OTIO_SCHEMA": "Clip.1",
                                    "name": "Hybrid_Performance_Block",
                                    "source_range": {
                                        "OTIO_SCHEMA": "TimeRange.1",
                                        "start_time": {
                                            "OTIO_SCHEMA": "RationalTime.1",
                                            "rate": 30,
                                            "value": 0,
                                        },
                                        "duration": {
                                            "OTIO_SCHEMA": "RationalTime.1",
                                            "rate": 30,
                                            "value": int(duration * 30),
                                        },
                                    },
                                }
                            ],
                        }
                    ],
                },
            }
            atomic_write_bytes(otio_path, json.dumps(otio, indent=2).encode("utf-8"))
            print(f"[Studio-Server] hybrid master {wav_path} ({nbytes} PCM bytes)")
            wav_receipt=persist_export(EXPORT_ROOT,wav_path.name,"production_masters",wav_path.read_bytes())
            otio_receipt=persist_export(EXPORT_ROOT,otio_path.name,"otio_packages",otio_path.read_bytes())
            self._json(
                200,
                {
                    "status": "SUCCESS",
                    "saved_master_path": wav_receipt["saved_at"],
                    "saved_otio_path": otio_receipt["saved_at"],
                    "provider": "local_hybrid_proxy",
                },
            )
        except Exception as e:
            print(f"[Studio-Server] neural fault: {e}")
            self._json(500, {"status": "ERROR", "error": str(e)})

    def _handle_vocal_lab(self, request_data: dict):
        try:
            tools = str(Path(__file__).resolve().parent)
            if tools not in sys.path:
                sys.path.insert(0, tools)
            from vocal_lab import render_vocal_job

            result = render_vocal_job(request_data, EXPORT_ROOT)
            print(f"[Vocal-Lab] {result.get('engine')} → {result.get('saved_master_path')}")
            vocal_path=Path(result["saved_master_path"])
            receipt=persist_export(EXPORT_ROOT,vocal_path.name,"vocal_stems",vocal_path.read_bytes())
            result["saved_master_path"]=receipt["saved_at"]
            result["file_sha256"]=receipt["sha256"]
            self._json(200,result)
        except Exception as e:
            print(f"[Vocal-Lab] fault: {e}")
            self._json(500, {"status": "ERROR", "error": str(e)})


def main():
    durable_mkdir(EXPORT_ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), StudioHandler) as httpd:
        print("=" * 72)
        print(f"[Studio-Server] http://localhost:{PORT}")
        print(f"[Studio-Server] root {ROOT}")
        print(f"[Studio-Server] exports {EXPORT_ROOT}")
        print("[Studio-Server] POST /api/write_production_file")
        print("[Studio-Server] POST /api/dispatch_neural_compilation")
        print("[Studio-Server] POST /api/local_neural_vocal_synthesis")
        print("=" * 72)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Studio-Server] shutdown")
            sys.exit(0)


if __name__ == "__main__":
    main()
