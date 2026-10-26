"""Old PR4 source is complete but has no canonical project API (HTTP 404)."""
import tempfile,pathlib,subprocess,sys,os,time,urllib.request,urllib.error,re,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td);(d/'tools').mkdir()
 for name in ['tools/studio_server.py','index.html']:
  (d/name).write_bytes(subprocess.check_output(['git','show','fcab64b18f325cd718e0ddb76f3d1ba72645fdd2:'+name],cwd=ROOT))
 p=subprocess.Popen([sys.executable,'tools/studio_server.py'],cwd=d,env={**os.environ,'STUDIO_PORT':'18769'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.5);page=urllib.request.urlopen('http://127.0.0.1:18769').read();cap=re.search(rb'window.__STUDIO_CAPABILITY__="([^"]+)"',page)[1].decode()
  req=urllib.request.Request('http://127.0.0.1:18769/api/projects/commit',data=b'{}',headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:18769','X-Studio-Capability':cap})
  try:
   with urllib.request.urlopen(req) as r:status=r.status
  except urllib.error.HTTPError as e:status=e.code
  result={'baseline_head':'fcab64b18f325cd718e0ddb76f3d1ba72645fdd2','project_commit_status':status,'expected_missing_authority':status==404}
  (ROOT/'evidence/m042/baseline-red.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));assert status==404
 finally:p.terminate();p.wait()
