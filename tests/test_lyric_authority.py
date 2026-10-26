import copy, hashlib, json, pathlib, subprocess, sys, tempfile, unittest, io, wave
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import studio_server as s
import lyric_timeline as l
from test_project_authority import SPEC
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Lyrics(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)/'exports'
  self.audio=(ROOT/'evidence/m043/fixtures/rise-higher.wav').read_bytes()
  self.aid=s.persist_export(self.root,'voice.wav','test',self.audio)['sha256']
  self.base=s.project_operation(self.root,{'songSpec':SPEC,'expectedCurrentRevisionId':None},True)
 def tearDown(self):self.tmp.cleanup()
 def req(self,base,**fields):return {'projectId':base['manifest']['projectId'],'expectedCurrentRevisionId':base['revision']['revisionId'],**fields}
 def initial(self):return s.project_operation(self.root,self.req(self.base,action='candidate',sourceArtifactId=self.aid,knownTranscript='rise fire'),True,True)
 def correct(self,a,**fields):
  return s.project_operation(self.root,self.req(a,action='correct',expectedLyricRevisionId=a['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':'higher'}],actor='test-editor',reason='known fixture transcript',**fields),True,True)
 def test_revision_loop_audio_and_history(self):
  a=self.initial();b=self.correct(a)
  self.assertEqual([w['text'] for w in b['lyricTimeline']['words']],['rise','higher'])
  self.assertEqual(b['lyricTimeline']['parentRevisionId'],a['lyricTimeline']['revisionId'])
  self.assertEqual(b['lyricTimeline']['evidenceArtifactId'],a['lyricTimeline']['evidenceArtifactId'])
  self.assertEqual(l.pcm_info(self.audio)[0]['sourceAudioDigest'],b['lyricTimeline']['sourceAudioDigest'])
  history=s.project_operation(self.root,{'projectId':a['manifest']['projectId'],'revisionId':a['revision']['revisionId']})
  self.assertEqual(history['lyricTimeline'],a['lyricTimeline'])
  self.assertEqual(s.artifact_bytes(self.root,self.aid),self.audio)
  self.assertEqual([(w['decodedSampleStart'],w['decodedSampleEnd']) for w in a['lyricTimeline']['words']],[(w['decodedSampleStart'],w['decodedSampleEnd']) for w in b['lyricTimeline']['words']])
 def test_stale_project_and_stale_lyric(self):
  a=self.initial();b=self.correct(a)
  with self.assertRaises(s.ProjectConflict):self.correct(a)
  bad=self.req(b,action='correct',expectedLyricRevisionId=a['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':'x'}],actor='a')
  with self.assertRaises(s.ProjectConflict):s.project_operation(self.root,bad,True,True)
  self.assertEqual(s.project_operation(self.root,{'projectId':b['manifest']['projectId']}),b)
 def test_new_process_restart(self):
  b=self.correct(self.initial());pid=b['manifest']['projectId']
  code='import studio_server as s,json,sys;print(json.dumps(s.project_operation(sys.argv[1],{"projectId":sys.argv[2]})))'
  r=subprocess.run([sys.executable,'-c',code,str(self.root),pid],cwd=ROOT/'tools',capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(r.stdout),b)
 def test_crash_before_lyric_promotion(self):
  a=self.initial()
  for point in ['lyric_durable_before_project_revision','revision_durable_before_reread','before_manifest_promotion']:
   req=self.req(a,action='correct',expectedLyricRevisionId=a['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':'higher'}],actor='test')
   code='''import studio_server as s,json,sys,os
s.project_boundary=lambda name:os._exit(75) if name==sys.argv[3] else None
s.project_operation(sys.argv[1],json.loads(sys.argv[2]),True,True)'''
   p=subprocess.run([sys.executable,'-c',code,str(self.root),json.dumps(req),point],cwd=ROOT/'tools')
   self.assertEqual(p.returncode,75)
   self.assertEqual(s.project_operation(self.root,{'projectId':a['manifest']['projectId']}),a)
 def test_regular_save_preserves_lyric_truth(self):
  a=self.initial();b=s.project_operation(self.root,self.req(a,songSpec=SPEC,sourceAssetDigests=[self.aid]),True)
  self.assertEqual(a['lyricTimeline'],b['lyricTimeline'])
  with self.assertRaises(ValueError):s.project_operation(self.root,self.req(b,songSpec=SPEC),True)
 def test_unknown_without_known_transcript(self):
  a=s.project_operation(self.root,self.req(self.base,action='candidate',sourceArtifactId=self.aid,knownTranscript=''),True,True)
  self.assertEqual(a['lyricTimeline']['status'],'unknown');self.assertEqual(a['lyricTimeline']['words'],[])
  self.assertIsNone(a['lyricTimeline']['confidence'])
 def test_no_replacement_of_corrected_truth(self):
  a=self.initial()
  with self.assertRaises(ValueError):s.project_operation(self.root,self.req(a,action='candidate',sourceArtifactId=self.aid,knownTranscript='other'),True,True)
 def test_bad_sample_ranges_source_and_containment(self):
  a=self.initial()['lyricTimeline'];ev=json.loads(s.artifact_bytes(self.root,a['evidenceArtifactId']))
  def validate(d):
   d.pop('revisionId');d['revisionId']=hashlib.sha256(l.canonical(d)).hexdigest();return l.validate(d,self.audio,ev)
  mutations=[lambda d:d['words'][0].update(decodedSampleEnd=d['words'][0]['decodedSampleStart']),
             lambda d:d['words'][1].update(decodedSampleStart=0),lambda d:d['words'][0].update(decodedSampleEnd=999999),
             lambda d:d.update(sourceAudioDigest='a'*64),lambda d:d['phrases'][0].update(decodedSampleEnd=4100),
             lambda d:d['phrases'][0].update(wordIds=[]),lambda d:d.update(confidence=.93),
             lambda d:d.update(alignmentModelOrMethod='')]
  for mutate in mutations:
   d=copy.deepcopy(a);mutate(d)
   with self.assertRaises(ValueError):validate(d)
 def test_unicode_punctuation_and_occurrences(self):
  a=self.initial();a2=self.correct(a)
  for text in ['higher!','élève','don’t']:
   a2=s.project_operation(self.root,self.req(a2,action='correct',expectedLyricRevisionId=a2['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':text}],actor='editor'),True,True)
   self.assertEqual(a2['lyricTimeline']['words'][1]['text'],text)
  info,_=l.pcm_info(self.audio)
  doc=l.candidate(self.audio,self.aid,'a'*64,'rise rise')
  self.assertEqual(len({w['id'] for w in doc['words']}),2)
 def test_missing_evidence_and_tampered_audio_fail_closed(self):
  a=self.initial();ev=a['lyricTimeline']['evidenceArtifactId'];path=self.root/'objects'/ev[:2]/ev;path.unlink()
  with self.assertRaises(ValueError):s.project_operation(self.root,{'projectId':a['manifest']['projectId']})
 def test_tampered_audio_fail_closed(self):
  a=self.initial();path=self.root/'objects'/self.aid[:2]/self.aid;path.write_bytes(b'tampered')
  with self.assertRaises(ValueError):s.project_operation(self.root,{'projectId':a['manifest']['projectId']})
 def test_concurrent_lyric_writers_one_winner(self):
  a=self.initial();req=self.req(a,action='correct',expectedLyricRevisionId=a['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':'higher'}],actor='writer')
  code="""import studio_server as s,sys,json
try:s.project_operation(sys.argv[1],json.loads(sys.argv[2]),True,True);sys.exit(0)
except s.ProjectConflict:sys.exit(9)"""
  jobs=[subprocess.Popen([sys.executable,'-c',code,str(self.root),json.dumps(req)],cwd=ROOT/'tools') for _ in range(2)]
  self.assertEqual(sorted(j.wait() for j in jobs),[0,9])
 def test_death_after_promotion_reopens_valid_R2(self):
  a=self.initial();req=self.req(a,action='correct',expectedLyricRevisionId=a['lyricTimeline']['revisionId'],changes=[{'wordId':'w1','text':'higher'}],actor='writer')
  code="""import studio_server as s,json,sys,os
s.project_boundary=lambda name:os._exit(75) if name=='after_manifest_promotion' else None
s.project_operation(sys.argv[1],json.loads(sys.argv[2]),True,True)"""
  p=subprocess.run([sys.executable,'-c',code,str(self.root),json.dumps(req)],cwd=ROOT/'tools')
  self.assertEqual(p.returncode,75)
  b=s.project_operation(self.root,{'projectId':a['manifest']['projectId']})
  self.assertEqual(b['lyricTimeline']['words'][1]['text'],'higher')
  self.assertEqual(b['lyricTimeline']['parentRevisionId'],a['lyricTimeline']['revisionId'])
 def test_reference_fences_include_lyrics_evidence_and_audio(self):
  a=self.initial();seen=[];original=s.project_artifact_fence
  def fence(root,digest):seen.append(digest);original(root,digest)
  with patch.object(s,'project_artifact_fence',fence):b=self.correct(a)
  for digest in [self.aid,b['revision']['lyricTimelineDigest'],a['revision']['lyricTimelineDigest'],a['lyricTimeline']['evidenceArtifactId']]:self.assertIn(digest,seen)
if __name__=='__main__':unittest.main()
