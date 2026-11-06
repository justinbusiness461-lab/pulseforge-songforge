#!/usr/bin/env python3
"""PCM16 structural preflight reusing tools/certify_mix.py. No product certification."""
import argparse, importlib.util, json, pathlib, struct

def validate(path):
    b = pathlib.Path(path).read_bytes()
    if len(b) < 12 or b[:4] != b'RIFF' or b[8:12] != b'WAVE':
        raise ValueError('RIFF/WAVE required')
    if struct.unpack_from('<I', b, 4)[0] + 8 != len(b):
        raise ValueError('RIFF length mismatch')
    pos, fmt, data = 12, None, None
    while pos < len(b):
        if pos + 8 > len(b): raise ValueError('truncated chunk header')
        tag, size = b[pos:pos+4], struct.unpack_from('<I', b, pos+4)[0]
        start, end = pos + 8, pos + 8 + size
        if end + (size & 1) > len(b): raise ValueError('truncated chunk')
        if tag == b'fmt ':
            if fmt is not None or size < 16: raise ValueError('invalid fmt chunk')
            fmt = struct.unpack_from('<HHIIHH', b, start)
        if tag == b'data':
            if data is not None or fmt is None: raise ValueError('invalid data chunk')
            data = size
        pos = end + (size & 1)
    if fmt is None or data is None: raise ValueError('missing PCM chunks')
    codec, channels, rate, byte_rate, align, bits = fmt
    if codec != 1 or channels not in (1, 2) or rate <= 0 or bits != 16:
        raise ValueError('mono/stereo PCM16 required')
    if align != channels * 2 or byte_rate != rate * align or not data or data % align:
        raise ValueError('inconsistent PCM metadata')

def main():
    p = argparse.ArgumentParser(); p.add_argument('--repo', required=True)
    p.add_argument('files', nargs='+'); a = p.parse_args()
    spec = importlib.util.spec_from_file_location('existing_metrics', pathlib.Path(a.repo)/'tools/certify_mix.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    results = []
    for path in a.files:
        try:
            validate(path)
            results.append(dict(path=path, structural_status='PASS', invalid_samples=0, metrics=module.inspect(path)))
        except Exception as exc:
            results.append(dict(path=path, structural_status='FAIL', error=str(exc)))
    print(json.dumps(results, indent=2, allow_nan=False))
    return int(any(r['structural_status']=='FAIL' for r in results))

if __name__ == '__main__': raise SystemExit(main())
