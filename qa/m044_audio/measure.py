"""Read-only PCM16 WAV QA. No project writes or artistic certification."""
import argparse,hashlib,json,math,pathlib,re,subprocess,sys,wave,tempfile
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from certify_mix import inspect

def db(x):return 20*math.log10(x) if x>0 else None

def runs(mask):
 d=np.diff(np.r_[False,mask,False].astype(int));return [[int(a),int(b)] for a,b in zip(np.where(d==1)[0],np.where(d==-1)[0])]

def metrics(x,rate):
 x=np.asarray(x,dtype=float)
 if x.ndim!=2 or not x.size or not np.isfinite(x).all() or type(rate)!=int or rate<=0:raise ValueError('finite nonempty frame/channel array and positive integer rate required')
 rms=float(np.sqrt(np.mean(x*x)));peak=float(np.max(np.abs(x)));corr=side=mid=ratio=mono=None
 if x.shape[1]==2:
  l,r=x.T;mid=float(np.sqrt(np.mean(((l+r)/2)**2)));side=float(np.sqrt(np.mean(((l-r)/2)**2)))
  if np.std(l)>0 and np.std(r)>0:corr=float(np.corrcoef(l,r)[0,1])
  if mid>0:ratio=db(side/mid)
  if rms>0:mono=db(mid/rms)
 hop=max(1,round(rate*.01));silent=np.zeros(len(x),dtype=bool)
 for a in range(0,len(x),hop):
  block=x[a:a+hop];silent[a:a+len(block)]=float(np.sqrt(np.mean(block*block)))<1e-3
 gaps=[r for r in runs(silent) if r[1]-r[0]>=round(rate*.25)]
 # Welch-style averaged channel power: Hann 4096, 2048 hop; never cancel channels before FFT.
 n=4096;power=np.zeros(n//2+1);count=0
 for a in range(0,len(x),2048):
  block=x[a:a+n];padded=np.zeros((n,x.shape[1]));padded[:len(block)]=block
  power+=np.mean(np.abs(np.fft.rfft(padded*np.hanning(n)[:,None],axis=0))**2,axis=1);count+=1
 freq=np.fft.rfftfreq(n,1/rate);total=float(power.sum());bands={}
 for lo,hi in [(20,120),(120,500),(500,2000),(2000,6000),(6000,rate/2+1)]:
  bands[f'{lo}-{hi if lo!=6000 else "Nyquist"}']=float(power[(freq>=lo)&(freq<hi)].sum()/total) if total else None
 return dict(samplePeakDbfs=db(peak),rmsDbfs=db(rms),dcOffset=np.mean(x,axis=0).tolist(),correlation=corr,sideRms=side,midRms=mid,sideToMidDb=ratio,monoDownmixDbRelativeToStereoRms=mono,crestFactorDb=db(peak/rms) if rms else None,silenceWindows=gaps,silenceMethod='10ms nonoverlapping RMS < -60 dBFS for >=250ms; intentional silence possible',spectralEnergyFractions=bands,spectralMethod='Hann 4096 / hop 2048; channel power averaged; fractions relative to all FFT bins')

def locality(a,b,allowed):
 if a.shape!=b.shape:raise ValueError('PCM shapes differ; no implicit alignment')
 mask=np.zeros(len(a),bool)
 for start,end in allowed:
  if type(start)!=int or type(end)!=int or not 0<=start<end<=len(a):raise ValueError('invalid allowed interval')
  mask[start:end]=True
 diff=np.any(a!=b,axis=1);outside=(a-b)[~mask]
 return dict(differingRuns=runs(diff),outsideExactlyEqual=not bool(np.any(diff&~mask)),outsidePeakDelta=float(np.max(np.abs(outside))) if outside.size else 0,outsideRmsDelta=float(np.sqrt(np.mean(outside**2))) if outside.size else 0)

def decode(path):
 with wave.open(str(path)) as w:
  if w.getsampwidth()!=2 or w.getcomptype()!='NONE':raise ValueError('PCM16 WAV required; convert explicitly outside harness')
  rate,channels,frames=w.getframerate(),w.getnchannels(),w.getnframes();raw=w.readframes(frames)
 if not frames or len(raw)!=frames*channels*2:raise ValueError('empty/truncated audio')
 return np.frombuffer(raw,dtype='<i2').reshape(-1,channels).astype(float)/32768,rate,dict(encoding='signed PCM16 little-endian interleaved',channels=channels,decodedFrames=frames,duration=frames/rate,pcmDigest=hashlib.sha256(raw).hexdigest())

def loudness(path):
 command=['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','ebur128=peak=true','-f','null','-']
 try:
  p=subprocess.run(command,capture_output=True,text=True,timeout=120);log=p.stderr
  if p.returncode:raise ValueError('FFmpeg failed')
  summary=log.rsplit('Summary:',1)[-1];i=re.search(r'I:\s*([-\d.]+) LUFS',summary);peak=re.search(r'Peak:\s*([-\d.]+) dBFS',summary)
  version=subprocess.run(['ffmpeg','-version'],capture_output=True,text=True).stdout.splitlines()[0]
  return dict(status='OBSERVED_NOT_REFERENCE_QUALIFIED',integratedLufs=float(i[1]) if i else None,truePeakEstimateDbtp=float(peak[1]) if peak else None,method='FFmpeg ebur128 peak=true oversampled estimate',version=version,command=command,rawLog=log)
 except (OSError,ValueError,subprocess.TimeoutExpired) as e:return dict(status='UNVERIFIED',reason=str(e),integratedLufs=None,truePeakEstimateDbtp=None)

def section_loudness(x,rate):
 with tempfile.TemporaryDirectory(prefix='m044-qa-') as folder:
  path=pathlib.Path(folder)/'section.wav'
  with wave.open(str(path),'wb') as w:
   w.setnchannels(x.shape[1]);w.setsampwidth(2);w.setframerate(rate);w.writeframes(np.clip(x*32768,-32768,32767).astype('<i2').tobytes())
  return loudness(path)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('audio');ap.add_argument('--manifest',required=True);ap.add_argument('--after');ap.add_argument('--out',required=True);args=ap.parse_args()
 manifest=json.loads(pathlib.Path(args.manifest).read_text());x,rate,identity=decode(args.audio)
 if manifest['sampleRate']!=rate:raise ValueError('manifest clock mismatch')
 out=dict(identity=identity,sampleRate=rate,baseline=inspect(args.audio),whole=metrics(x,rate),loudness=loudness(args.audio),sections=[],scope='physical diagnostics only; no artistic or mastering promotion')
 ids=set()
 for s in manifest.get('sections',[]):
  a,b=s['startSample'],s['endSample']
  if s['id'] in ids or type(a)!=int or type(b)!=int or not 0<=a<b<=len(x):raise ValueError('invalid section identity/bounds')
  ids.add(s['id']);m=metrics(x[a:b],rate);out['sections'].append(dict(section=s,metrics=m,sectionLoudness=section_loudness(x[a:b],rate)))
 levels=[s['metrics']['rmsDbfs'] for s in out['sections'] if s['metrics']['rmsDbfs'] is not None]
 out['sectionRmsRangeDb']=max(levels)-min(levels) if levels else None
 out['sectionDifferentiation']=[dict(left=a['section']['id'],right=b['section']['id'],rmsDeltaDb=b['metrics']['rmsDbfs']-a['metrics']['rmsDbfs'] if a['metrics']['rmsDbfs'] is not None and b['metrics']['rmsDbfs'] is not None else None) for a,b in zip(out['sections'],out['sections'][1:])]
 if args.after:
  y,yr,yi=decode(args.after)
  if yr!=rate:raise ValueError('clock mismatch')
  out['afterIdentity']=yi;out['editLocality']=locality(x,y,manifest.get('allowedEditAndTailIntervals',[]))
 pathlib.Path(args.out).write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
