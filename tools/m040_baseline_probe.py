"""Reproduce the two old defects using exact committed v2.18 archive bytes."""
import pathlib,tempfile,zipfile,subprocess,sys,os,time,urllib.request,json
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 with zipfile.ZipFile(root/'SoundForge-Studio-Release-v2.18.zip') as z:z.extractall(td)
 p=subprocess.Popen([sys.executable,'tools/studio_server.py'],cwd=td,env={**os.environ,'STUDIO_PORT':'18766'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  time.sleep(.5)
  def post(value):
   req=urllib.request.Request('http://127.0.0.1:18766/api/write_production_file',data=json.dumps({'filename':'probe.txt','subdirectory':'probe','data_bytes':value}).encode(),headers={'Content-Type':'application/json','Origin':'https://evil.test'})
   with urllib.request.urlopen(req) as r:return r.status
  a=post('A');b=post('B');verify=subprocess.run([sys.executable,'tools/certify_integrity.py'],cwd=td,capture_output=True,text=True)
  result={'exact_archive_baseline':True,'foreign_write_without_capability_status':a,'same_alias_second_write_status':b,'historical_integrity_exit_after_overwrite':verify.returncode,'red_expected':a==200 and verify.returncode==1}
  (root/'evidence/m040/baseline-red.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
  if not result['red_expected']:raise SystemExit(1)
 finally:p.terminate();p.wait()
