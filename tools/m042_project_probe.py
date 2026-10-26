"""Real project APIs + actual retained audio; cold restart never reads browser storage."""
import pathlib,subprocess,os,sys,json,urllib.request,urllib.error,re,time,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];PORT=18768;OUT=ROOT/'evidence/m042';OUT.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,passed):
 checks.append({'name':name,'pass':bool(passed)})
 if not passed:raise AssertionError(name)
def request(route,payload,cap):
 req=urllib.request.Request(f'http://127.0.0.1:{PORT}/api/'+route,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':f'http://127.0.0.1:{PORT}','X-Studio-Capability':cap})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  try:return e.code,json.loads(e.read())
  except ValueError:return e.code,{}
def start():
 p=subprocess.Popen([sys.executable,'tools/studio_server.py'],cwd=ROOT,env={**os.environ,'STUDIO_PORT':str(PORT)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(50):
  try:
   page=urllib.request.urlopen(f'http://127.0.0.1:{PORT}').read();m=re.search(rb'window.__STUDIO_CAPABILITY__="([^"]+)"',page)
   if m:return p,m[1].decode()
  except OSError:pass
  time.sleep(.1)
 raise RuntimeError('server failed')
def export(name,cap):
 data=(ROOT/'evidence/m040/music'/name).read_bytes();status,r=request('write_production_file',{'filename':name,'subdirectory':'m042-music','data_bytes':list(data)},cap)
 check('export-'+name,status==200 and r['sha256']==hashlib.sha256(data).hexdigest());return r['sha256']
p,cap=start();receipt={}
try:
 spec1=json.loads((ROOT/'evidence/m040/music/SongSpec.initial.json').read_text());spec2=json.loads((ROOT/'evidence/m040/music/SongSpec.edited.json').read_text())
 a1=export('initial.wav',cap)
 status,r1=request('projects/commit',{'projectId':None,'expectedCurrentRevisionId':None,'songSpec':spec1,'outputArtifactIds':[a1]},cap);check('create-R1',status==200)
 pid=r1['manifest']['projectId'];rid1=r1['revision']['revisionId']
 a2=export('edited.wav',cap)
 status,r2=request('projects/commit',{'projectId':pid,'expectedCurrentRevisionId':rid1,'songSpec':spec2,'outputArtifactIds':[a2]},cap);check('commit-R2',status==200)
 rid2=r2['revision']['revisionId'];check('R2-parent-is-R1',r2['revision']['parentRevisionId']==rid1)
 # End process; obtain a new session; no localStorage or in-memory project used for open.
 p.terminate();p.wait();p,cap=start()
 status,current=request('projects/open',{'projectId':pid},cap);check('cold-open-by-projectId',status==200 and current==r2)
 check('R2-current',current['manifest']['currentRevisionId']==rid2)
 check('exact-R2-SongSpec',current['songSpec']==spec2)
 canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
 check('R2-SongSpec-digest',hashlib.sha256(canonical(current['songSpec'])).hexdigest()==current['revision']['songSpecDigest'])
 check('R2-timeline-digest',hashlib.sha256(canonical(current['productionTimeline'])).hexdigest()==current['revision']['productionTimelineDigest'])
 check('output-bound-to-R2',current['revision']['outputArtifactIds']==[a2] and current['revision']['outputBindings']==[{'artifactId':a2,'songSpecDigest':current['revision']['songSpecDigest'],'productionTimelineDigest':current['revision']['productionTimelineDigest']}])
 status,historic=request('projects/open',{'projectId':pid,'revisionId':rid1},cap);check('R1-retained',status==200 and historic['songSpec']==spec1 and historic['revision']['outputArtifactIds']==[a1])
 status,_=request('projects/commit',{'projectId':pid,'expectedCurrentRevisionId':rid1,'songSpec':spec1},cap);check('stale-R1-409',status==409)
 status,current2=request('projects/open',{'projectId':pid},cap);check('stale-write-no-authority-change',status==200 and current2==current)
 status,_=request('projects/open',{'projectId':pid},'wrong');check('unauthorized-project-read-reject',status==403)
 receipt={'checks':checks,'browser_cache_used':False,'new_server_process':True,'R1':r1['revision'],'R2':r2['revision'],'ProjectManifest':current['manifest'],'media':{'initial':a1,'edited':a2},'ceiling':'real HTTP/filesystem/process restart and retained real WAVs; no browser UI or power-loss claim'}
finally:p.terminate();p.wait()
(OUT/'project-discriminator.json').write_text(json.dumps(receipt,indent=2));print(f'{len(checks)}/{len(checks)} project HTTP/restart checks PASS')
