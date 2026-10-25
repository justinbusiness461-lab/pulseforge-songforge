"""Real HTTP contract and cold restart probe; all writes stay in this checkout."""
import subprocess,sys,os,pathlib,time,json,urllib.request,urllib.error,re,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/m040';PORT=18765
rows=[]
def req(method,path='/',payload=None,origin='http://127.0.0.1:18765',token=None,host=None,extra=None):
 headers={}
 if origin is not None:headers['Origin']=origin
 if host:headers['Host']=host
 if token:headers['X-Studio-Capability']=token
 if payload is not None:headers['Content-Type']='application/json'
 headers.update(extra or {})
 r=urllib.request.Request(f'http://127.0.0.1:{PORT}'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method=method)
 try:
  with urllib.request.urlopen(r,timeout=10) as x:return x.status,x.read(),dict(x.headers)
 except urllib.error.HTTPError as e:return e.code,e.read(),dict(e.headers)
def start():
 p=subprocess.Popen([sys.executable,'tools/studio_server.py'],cwd=ROOT,env={**os.environ,'STUDIO_PORT':str(PORT)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(50):
  try:
   status,body,_=req('GET');m=re.search(rb'window.__STUDIO_CAPABILITY__="([^"]+)"',body)
   if status==200 and m:return p,m[1].decode()
  except OSError:pass
  time.sleep(.1)
 p.terminate();raise RuntimeError('server failed startup')
def check(name,got,expected):
 rows.append({'name':name,'actual':got,'expected':expected,'pass':got==expected})
def post(data,**kwargs):return req('POST','/api/write_production_file',data,**kwargs)
p,token=start()
try:
 data={'filename':'master.wav','subdirectory':'m040','data_bytes':'version A'}
 for name,origin in [('foreign','https://evil.test'),('deceptive','http://localhost.evil.test:18765'),('wrong-port','http://127.0.0.1:18766'),('missing',None),('malformed','null')]:
  check(name,post(data,origin=origin,token=token)[0],403)
 check('missing-capability',post(data)[0],403)
 check('wrong-capability',post(data,token='wrong')[0],403)
 check('rebind-host',post(data,token=token,host='evil.test:18765')[0],403)
 a=post(data,token=token);check('trusted-write',a[0],200);a=json.loads(a[1]);
 b=post({**data,'data_bytes':'version B'},token=token);check('same-alias-write',b[0],200);b=json.loads(b[1])
 check('historical-A',pathlib.Path(a['saved_at']).read_bytes(),b'version A')
 check('current-B',pathlib.Path(b['saved_at']).read_bytes(),b'version B')
 for name,sub in [('../escape','m040'),('ok','../../escape'),('ok','nested/path')]:check('traversal-'+name+sub,post({**data,'filename':name,'subdirectory':sub},token=token)[0],400)
 check('private-GET',req('GET','/workspace/studio_exports/manifest_registry.json')[0],403)
 check('foreign-GET',req('GET',origin='https://evil.test')[0],403)
 check('public-GET',req('GET','/app-core.js')[0],200)
 for origin,expected in [('http://127.0.0.1:18765',204),('https://evil.test',403)]:
  x=req('OPTIONS','/api/write_production_file',origin=origin,extra={'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-studio-capability'});check('preflight-'+origin,x[0],expected)
  if expected==204:check('preflight-exact-CORS',x[2].get('Access-Control-Allow-Origin'),origin)
 # oversized Content-Length rejected before body allocation (raw socket avoids client rewriting length)
 import socket
 with socket.create_connection(('127.0.0.1',PORT)) as sock:
  sock.sendall(f'POST /api/write_production_file HTTP/1.0\r\nHost: 127.0.0.1:{PORT}\r\nOrigin: http://127.0.0.1:{PORT}\r\nX-Studio-Capability: {token}\r\nContent-Length: 999999999\r\n\r\n'.encode());check('oversized',int(sock.recv(200).split()[1]),413)
 p.terminate();p.wait();p,token2=start();check('restart-token-rotated',token!=token2,True)
 check('old-session-denied',post(data,token=token)[0],403)
 check('history-after-restart',pathlib.Path(a['saved_at']).read_bytes(),b'version A')
 for filename in ['SongSpec.initial.json','SongSpec.edited.json','initial.wav','edited.wav']:
  payload=(OUT/'music'/filename).read_bytes()
  actual=post({'filename':filename,'subdirectory':'music-candidate','data_bytes':list(payload)},token=token2)
  check('actual-export-'+filename,actual[0],200)
  saved=json.loads(actual[1]);check('actual-export-hash-'+filename,saved['sha256'],hashlib.sha256(payload).hexdigest())
  check('actual-export-bytes-'+filename,pathlib.Path(saved['saved_at']).read_bytes()==payload,True)
 p.terminate();p.wait();p,token3=start()
 for filename in ['SongSpec.initial.json','SongSpec.edited.json']:
  alias=json.loads((ROOT/'workspace/studio_exports/aliases/music-candidate'/(filename+'.json')).read_text())
  restored=pathlib.Path(alias['object_path']).read_bytes()
  check('project-reopen-'+filename,restored==(OUT/'music'/filename).read_bytes(),True)
 verifier=subprocess.run([sys.executable,'tools/certify_integrity.py'],cwd=ROOT,capture_output=True,text=True);check('history-verifier',verifier.returncode,0)
 (OUT/'integrity-green.log').write_text(verifier.stdout)
finally:p.terminate();p.wait()
(OUT/'http-contract.json').write_text(json.dumps(rows,indent=2,default=lambda x:x.decode() if isinstance(x,bytes) else str(x)))
print(f'{sum(x["pass"] for x in rows)}/{len(rows)} HTTP/restart checks PASS')
if not all(x['pass'] for x in rows):raise SystemExit(1)
