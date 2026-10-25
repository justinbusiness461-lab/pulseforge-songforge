#!/usr/bin/env python3
"""Decoded PCM16 WAV sample metrics. Not true-peak, LUFS or artistic certification."""
import array,hashlib,json,math,sys,wave,pathlib

def amplitude_dbfs(amplitude):
    return 20*math.log10(amplitude) if amplitude>0 else None

def inspect(path):
    with wave.open(str(path),'rb') as w:
        if w.getsampwidth()!=2 or w.getcomptype()!='NONE':raise ValueError('PCM16 WAV required')
        rate,channels,frames=w.getframerate(),w.getnchannels(),w.getnframes()
        data=w.readframes(frames)
    values=array.array('h',data)
    if sys.byteorder!='little':values.byteswap()
    if len(values)!=channels*frames or not frames:raise ValueError('truncated or empty PCM')
    peak=max(abs(v) for v in values)/32768
    dc=[sum(values[c::channels])/(frames*32768) for c in range(channels)]
    rms=math.sqrt(sum((v/32768)**2 for v in values)/len(values))
    zeros=run=maxrun=0
    for i in range(frames):
        silent=all(values[i*channels+c]==0 for c in range(channels))
        run=run+1 if silent else 0;maxrun=max(run,maxrun);zeros+=silent
    correlation=None
    if channels==2:
        l=values[0::2];r=values[1::2];a=sum(l)/frames;b=sum(r)/frames
        numerator=sum((x-a)*(y-b) for x,y in zip(l,r));den=math.sqrt(sum((x-a)**2 for x in l)*sum((y-b)**2 for y in r))
        correlation=numerator/den if den else None
    return {'sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),'sample_rate':rate,'channels':channels,'decoded_sample_frames':frames,'duration_seconds':frames/rate,'sample_peak':peak,'sample_peak_dbfs':amplitude_dbfs(peak),'rms_dbfs':amplitude_dbfs(rms),'dc_offset':dc,'zero_sample_frames':zeros,'longest_exact_zero_run_seconds':maxrun/rate,'channel_correlation':correlation,'full_scale_sample_count':sum(v in (-32768,32767) for v in values),'true_peak_dbTP':None,'loudness_LUFS_I':None,'ceiling':'PCM sample metrics only; silence may be intentional; no true-peak or loudness claim'}
if __name__=='__main__':
    print(json.dumps(inspect(sys.argv[1]),indent=2,allow_nan=False))
