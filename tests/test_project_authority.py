import unittest,pathlib,sys,tempfile,json,copy,subprocess,hashlib
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import studio_server as s
SPEC={'song_id':'authority-test','timebase':{'initial_bpm':96,'ticks_per_quarter_note':960},'structure':{'sections':[{'id':'verse','start_tick':0,'end_tick':3840}]},'tracks':[{'track_id':'bass','events':[{'tick':0,'note_number':48}]}]}
class ProjectAuthority(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)/'exports'
 def tearDown(self):self.temp.cleanup()
 def create(self):return s.project_operation(self.root,{'projectId':None,'expectedCurrentRevisionId':None,'songSpec':SPEC},True)
 def update(self,a):
  spec=copy.deepcopy(SPEC);spec['tracks'][0]['events'][0]['note_number']=36
  output=s.persist_export(self.root,'render.wav','test',b'actual fixture bytes')['sha256']
  return s.project_operation(self.root,{'projectId':a['manifest']['projectId'],'expectedCurrentRevisionId':a['revision']['revisionId'],'songSpec':spec,'outputArtifactIds':[output]},True)
 def test_chain_history_and_output(self):
  a=self.create();b=self.update(a);pid=a['manifest']['projectId']
  current=s.project_operation(self.root,{'projectId':pid})
  self.assertEqual(current,b);self.assertEqual(b['revision']['parentRevisionId'],a['revision']['revisionId'])
  self.assertEqual(s.project_operation(self.root,{'projectId':pid,'revisionId':a['revision']['revisionId']})['songSpec'],SPEC)
  rev=b['revision'];self.assertEqual(rev['outputBindings'][0]['songSpecDigest'],rev['songSpecDigest'])
  self.assertEqual(hashlib.sha256(s.project_json(b['songSpec'])).hexdigest(),rev['songSpecDigest'])
  self.assertEqual(hashlib.sha256(s.project_json(b['productionTimeline'])).hexdigest(),rev['productionTimelineDigest'])
 def test_stale_rejected(self):
  a=self.create();b=self.update(a)
  with self.assertRaises(s.ProjectConflict):self.update(a)
  self.assertEqual(s.project_operation(self.root,{'projectId':a['manifest']['projectId']})['manifest'],b['manifest'])
 def test_cold_process_no_cache(self):
  a=self.create();b=self.update(a)
  code='import studio_server as s,json,sys;print(json.dumps(s.project_operation(sys.argv[1],{"projectId":sys.argv[2]})))'
  r=subprocess.run([sys.executable,'-c',code,str(self.root),a['manifest']['projectId']],cwd=pathlib.Path(s.__file__).parent,capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(r.stdout),b)
 def test_bad_output_and_lyric_rejected(self):
  a=self.create();base={'projectId':a['manifest']['projectId'],'expectedCurrentRevisionId':a['revision']['revisionId'],'songSpec':SPEC}
  for fields in [{'outputArtifactIds':['f'*64]},{'lyricTimelineDigest':'a'*64}]:
   with self.assertRaises(ValueError):s.project_operation(self.root,{**base,**fields},True)
 def test_corrupt_project_fail_closed(self):
  a=self.create();p=self.root/'projects'/a['manifest']['projectId']/'revisions'/(a['revision']['revisionId']+'.json');p.write_text('{}')
  with self.assertRaises(ValueError):s.project_operation(self.root,{'projectId':a['manifest']['projectId']})
 def test_crash_before_and_after_promotion(self):
  for boundary in ['revision_durable_before_reread','before_manifest_promotion','after_manifest_promotion']:
   a=self.create();pid=a['manifest']['projectId'];rid=a['revision']['revisionId']
   code='''import studio_server as s,sys,json,os
s.project_boundary=lambda name: os._exit(75) if name==sys.argv[4] else None
s.project_operation(sys.argv[1],{'projectId':sys.argv[2],'expectedCurrentRevisionId':sys.argv[3],'songSpec':json.loads(sys.argv[5])},True)'''
   r=subprocess.run([sys.executable,'-c',code,str(self.root),pid,rid,boundary,json.dumps(SPEC)],cwd=pathlib.Path(s.__file__).parent,capture_output=True,text=True)
   self.assertEqual(r.returncode,75)
   reopened=s.project_operation(self.root,{'projectId':pid})
   self.assertEqual(reopened['revision']['revisionId']==rid,boundary!='after_manifest_promotion')
   self.assertEqual(s.project_operation(self.root,{'projectId':pid,'revisionId':rid})['songSpec'],SPEC)
 def test_uncommitted_revision_not_history(self):
  a=self.create()
  def stop(name):
   if name=='before_manifest_promotion':raise RuntimeError('injected')
  with patch.object(s,'project_boundary',stop):
   with self.assertRaises(RuntimeError):self.update(a)
  revisions=self.root/'projects'/a['manifest']['projectId']/'revisions'
  orphan=next(p.stem for p in revisions.iterdir() if p.stem!=a['revision']['revisionId'])
  with self.assertRaises(ValueError):s.project_operation(self.root,{'projectId':a['manifest']['projectId'],'revisionId':orphan})
 def test_one_of_two_stale_writers(self):
  a=self.create();req={'projectId':a['manifest']['projectId'],'expectedCurrentRevisionId':a['revision']['revisionId'],'songSpec':SPEC}
  code='''import studio_server as s,sys,json
try:s.project_operation(sys.argv[1],json.loads(sys.argv[2]),True);sys.exit(0)
except s.ProjectConflict:sys.exit(9)'''
  jobs=[subprocess.Popen([sys.executable,'-c',code,str(self.root),json.dumps(req)],cwd=pathlib.Path(s.__file__).parent) for _ in range(2)]
  self.assertEqual(sorted(j.wait() for j in jobs),[0,9])
 def test_reference_namespace_fenced_before_pointer(self):
  a=self.create();events=[];original=s.sync_dir
  def sync(p):events.append(pathlib.Path(p));original(p)
  def boundary(name):
   if name=='before_manifest_promotion':
    self.assertIn(self.root/'projects',events);self.assertIn(self.root/'objects',events);self.assertIn(self.root.parent,events)
  with patch.object(s,'sync_dir',sync),patch.object(s,'project_boundary',boundary):self.update(a)
if __name__=='__main__':unittest.main()
