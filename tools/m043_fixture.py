"""Reproduce an authenticated synthetic spoken fixture with system Flite (optional).
The word-separated construction provides independent placement bounds, not phoneme truth.
"""
import ctypes as c
import hashlib
import io
import json
import pathlib
import struct
import wave

ROOT = pathlib.Path(__file__).resolve().parents[1]

def generate():
    lib = c.CDLL('libflite.so.1', mode=c.RTLD_GLOBAL)
    voice_lib = c.CDLL('libflite_cmu_us_kal.so.1')
    lib.flite_init()
    voice_lib.register_cmu_us_kal.restype = c.c_void_p
    voice = voice_lib.register_cmu_us_kal(None)
    lib.flite_text_to_wave.argtypes = [c.c_char_p, c.c_void_p]; lib.flite_text_to_wave.restype = c.c_void_p
    lib.cst_wave_save_riff.argtypes = [c.c_void_p, c.c_char_p]; lib.delete_wave.argtypes = [c.c_void_p]
    import tempfile
    parts = []; bounds = []; offset = 4000
    for word in ['rise', 'higher']:
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td)/'word.wav'; obj = lib.flite_text_to_wave(word.encode(), voice)
            if not obj: raise RuntimeError('Flite synthesis failed')
            lib.cst_wave_save_riff(obj, str(p).encode()); lib.delete_wave(obj)
            with wave.open(str(p), 'rb') as w:
                assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (8000, 1, 2)
                raw = w.readframes(w.getnframes())
        vals = struct.unpack('<'+'h'*(len(raw)//2), raw)
        active = [i for i,x in enumerate(vals) if abs(x) >= 400]
        a,b = active[0],active[-1]+1; raw = raw[a*2:b*2]
        bounds.append({'text':word,'decodedSampleStart':offset,'decodedSampleEnd':offset+len(raw)//2})
        parts.append(raw); offset += len(raw)//2 + 4000
    pcm = bytes(8000) + parts[0] + bytes(8000) + parts[1] + bytes(8000)
    out = ROOT/'evidence/m043/fixtures'; out.mkdir(parents=True,exist_ok=True)
    p=out/'rise-higher.wav'
    with wave.open(str(p),'wb') as w:w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(pcm)
    manifest={'kind':'synthetic spoken test fixture; NOT singing or production vocals','generator':'system Flite 2.2 cmu_us_kal via ctypes',
              'sourceArtifactId':hashlib.sha256(p.read_bytes()).hexdigest(),'sourceAudioDigest':hashlib.sha256(pcm).hexdigest(),
              'sourceSampleRate':8000,'decodedFrameCount':len(pcm)//2,'knownWords':bounds,
              'boundaryMethod':'word-by-word synthesis, trim at absolute PCM sample threshold 400; concatenate with 500ms silence',
              'boundaryCeiling':'signal placement bounds; not human annotated phoneme onset/offset',
              'candidateTranscript':'rise fire','intentionalCorrection':{'wordId':'w1','before':'fire','after':'higher'},
              'licenseNote':'system Flite synthetic voice, no cloned identity; fixture generated locally'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':generate()
