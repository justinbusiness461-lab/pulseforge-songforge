"""Real HTTP lyric revision workflow; known-text alignment, not speech recognition."""
import hashlib,io,json,os,pathlib,re,subprocess,sys,time,urllib.request,urllib.error,wave
ROOT=pathlib.Path(__file__).resolve().parents[1];PORT=18769;OUT=ROOT/'evidence/m043';checks=[]
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)
def call(route,data,cap):
 req=urllib.request.Request(f'http://127.0.0.1:{PORT}/api/'+route,data=json.dumps(data).encode(),headers={'Origin':f'http://127.0.0.1:{PORT}','Content-Type':'application/json','X-Studio-Capability':cap})
 try:
  with urllib.request.urlopen(req,timeout=30) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
def start():
 p=subprocess.Popen([sys.executable,'tools/studio_server.py'],cwd=ROOT,env={**os.environ,'STUDIO_PORT':str(PORT)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:
   raw=urllib.request.urlopen(f'http://127.0.0.1:{PORT}').read();m=re.search(rb'window.__STUDIO_CAPABILITY__="([^"]+)"',raw)
   if m:return p,m[1].decode()
  except OSError:pass
  time.sleep(.05)
 raise RuntimeError('server unavailable')
def export(data,name):
 status,r=call('write_production_file',{'filename':name,'subdirectory':'m043-fixtures','data_bytes':list(data)},cap)
 check('immutable-import-'+name,status==200 and r['sha256']==hashlib.sha256(data).hexdigest());return r['sha256']
def req(a,**fields):return {'projectId':a['manifest']['projectId'],'expectedCurrentRevisionId':a['revision']['revisionId'],**fields}
p,cap=start()
try:
 audio=(OUT/'fixtures/rise-higher.wav').read_bytes();manifest=json.loads((OUT/'fixtures/manifest.json').read_text())
 aid=export(audio,'rise-higher.wav')
 spec=json.loads((OUT/'fixtures/SongSpec.json').read_text())
 status,base=call('projects/commit',{'expectedCurrentRevisionId':None,'songSpec':spec},cap);check('project-create',status==200)
 status,r1=call('projects/lyrics',req(base,action='candidate',sourceArtifactId=aid,knownTranscript='rise fire',language='en'),cap);check('machine-guided-R1',status==200)
 doc=r1['lyricTimeline'];check('audio-digest-exact',doc['sourceAudioDigest']==manifest['sourceAudioDigest'])
 check('sample-rate-exact',doc['sourceSampleRate']==8000)
 check('two-timed-occurrences',len(doc['words'])==2 and len({w['id'] for w in doc['words']})==2)
 check('confidence-honest',doc['confidence'] is None and doc['alignmentModelOrMethod']=='known-text-energy-islands-v1')
 status,r2=call('projects/lyrics',req(r1,action='correct',expectedLyricRevisionId=doc['revisionId'],changes=[{'wordId':'w1','text':'higher'}],actor='work-a-fixture-test',reason='intentional known-text correction'),cap);check('correct-R2',status==200)
 doc2=r2['lyricTimeline'];check('R2-parent-is-R1',doc2['parentRevisionId']==doc['revisionId'])
 check('corrected-word',[w['text'] for w in doc2['words']]==['rise','higher'])
 check('audio-unchanged',doc2['sourceAudioDigest']==doc['sourceAudioDigest'])
 check('word-timing-unchanged',[(w['decodedSampleStart'],w['decodedSampleEnd']) for w in doc2['words']]==[(w['decodedSampleStart'],w['decodedSampleEnd']) for w in doc['words']])
 check('evidence-preserved',doc2['evidenceArtifactId']==doc['evidenceArtifactId'])
 check('project-advanced',r2['revision']['parentRevisionId']==r1['revision']['revisionId'])
 p.kill();p.wait();p,cap=start()
 status,current=call('projects/open',{'projectId':r2['manifest']['projectId']},cap);check('fresh-process-cache-free-R2',status==200 and current==r2)
 status,old=call('projects/open',{'projectId':r1['manifest']['projectId'],'revisionId':r1['revision']['revisionId']},cap);check('R1-history-immutable',status==200 and old['lyricTimeline']==doc)
 status,_=call('projects/lyrics',req(r1,action='correct',expectedLyricRevisionId=doc['revisionId'],changes=[{'wordId':'w1','text':'bad'}],actor='stale-editor'),cap);check('stale-project-409',status==409)
 status,_=call('projects/lyrics',req(r2,action='correct',expectedLyricRevisionId=doc['revisionId'],changes=[{'wordId':'w1','text':'bad'}],actor='stale-editor'),cap);check('stale-lyric-409',status==409)
 status,after=call('projects/open',{'projectId':r2['manifest']['projectId']},cap);check('stale-save-keeps-R2',status==200 and after==r2)
 # Actual retained instrumental excerpt; lack of supplied known text must stay unknown.
 instrumental=(OUT/'fixtures/instrumental.wav').read_bytes()
 iid=export(instrumental,'instrumental.wav')
 status,ib=call('projects/commit',{'expectedCurrentRevisionId':None,'songSpec':spec},cap);check('negative-project-create',status==200)
 status,negative=call('projects/lyrics',req(ib,action='candidate',sourceArtifactId=iid,knownTranscript=''),cap)
 check('instrumental-no-invented-words',status==200 and negative['lyricTimeline']['words']==[] and negative['lyricTimeline']['phrases']==[] and negative['lyricTimeline']['status']=='unknown' and negative['lyricTimeline']['confidence'] is None)
 bad=export(b'not a WAV','invalid.wav')
 status,_=call('projects/lyrics',req(base,action='candidate',sourceArtifactId=bad,knownTranscript='x'),cap)
 # base is stale; CAS must win before parsing any proposed audio.
 check('stale-rejected-before-audio-work',status==409)
 status,fresh=call('projects/commit',{'expectedCurrentRevisionId':None,'songSpec':spec},cap)
 status,_=call('projects/lyrics',req(fresh,action='candidate',sourceArtifactId=bad,knownTranscript='x'),cap)
 check('invalid-audio-400',status==400)
 errors=[]
 for word,truth in zip(doc['words'],manifest['knownWords']):
  a=word['decodedSampleStart']-truth['decodedSampleStart'];b=word['decodedSampleEnd']-truth['decodedSampleEnd']
  errors.append({'word':truth['text'],'startErrorSamples':a,'endErrorSamples':b,'startErrorMs':a/8,'endErrorMs':b/8,'ceiling':'signal placement reference, not perceptual annotation'})
 snapshot=lambda r:{k:v for k,v in r.items() if k not in ('songSpec','productionTimeline')}
 receipt={'checks':checks,'fixture':manifest,'R1':snapshot(r1),'R2':snapshot(r2),'instrumentalNegative':snapshot(negative),'timingErrorOwnerMeasurement':errors,'newProcess':True,'browserCacheUsed':False,
          'ceiling':'owner HTTP/filesystem/restart qualification; provided-text alignment, NOT ASR; C/D independent physical/perceptual review pending'}
 (OUT/'lyric-discriminator.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(f'{len(checks)}/{len(checks)} lyric HTTP/restart checks PASS')
finally:p.terminate();p.wait()
