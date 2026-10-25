/** Exact app-core + existing WAV renderer, executed headlessly. Not browser playback. */
const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),path=require('path');
const {OfflineAudioContext}=require('web-audio-engine');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'evidence/m040/music');fs.mkdirSync(dir,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const context={console,window:{},document:{getElementById:()=>null},OfflineAudioContext,Float32Array,ArrayBuffer,DataView,Math};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'app-core.js'),'utf8'),context);
const ui=fs.readFileSync(path.join(root,'app-ui.js'),'utf8');
vm.runInContext(ui.slice(ui.indexOf('function audioBufferToWav('),ui.indexOf('async function exportWav()')),context);
(async()=>{
 if(process.argv.includes('--reopen')){
 context.project=JSON.parse(fs.readFileSync(path.join(dir,'SongSpec.edited.json'),'utf8'));
 vm.runInContext('loadProjectObject(project)',context);const restored=await vm.runInContext('renderMixBuffer()',context);context.audio=restored.buffer;
 const actual=sha(Buffer.from(vm.runInContext('audioBufferToWav(audio)',context)));const expected=JSON.parse(fs.readFileSync(path.join(dir,'render-receipt.json'),'utf8')).edited_sha256;
 fs.writeFileSync(path.join(dir,'cold-reopen.json'),JSON.stringify({new_process:true,audio_sha256:actual,matches_prior:actual===expected},null,2));if(actual!==expected)throw Error('cold reopen audio mismatch');return;
 }
 const initial=vm.runInContext(`(()=>{let s=parsePrompt('original dark 96 BPM E minor guitar',{seed:4040});s.song_id='sf-m040-original-4040';s.created_at='2026-10-25T00:00:00Z';s.revision_id='m040-initial';s.title='Night Signal — local instrumental study';let names=['Opening','Statement','Refrain','Turn','Refrain return','Closing'];s.structure.sections=s.structure.sections.map((v,i)=>({...v,id:'m040-'+i,name:names[i],role:'none',lyrics:''}));s.tracks=s.tracks.filter(t=>t.type!=='VOCAL');loadProjectObject(s);return JSON.parse(serializeProject())})()`,context);
 fs.writeFileSync(path.join(dir,'SongSpec.initial.json'),JSON.stringify(initial,null,2));
 let rendered=await vm.runInContext('renderMixBuffer()',context);context.audio=rendered.buffer;let bytes=Buffer.from(vm.runInContext('audioBufferToWav(audio)',context));fs.writeFileSync(path.join(dir,'initial.wav'),bytes);
 const editStart=initial.structure.sections[3].start_tick,editEnd=initial.structure.sections[3].end_tick;context.editStart=editStart;context.editEnd=editEnd;
 const edited=vm.runInContext(`(()=>{const s=JSON.parse(serializeProject());s.revision_id='m040-edit-1';s.parent_revision_id='m040-initial';s.tracks.find(t=>t.type==='BASS').events.forEach(e=>{if(e.tick>=editStart&&e.tick<editEnd)e.note_number-=12});loadProjectObject(s);return JSON.parse(serializeProject())})()`,context);
 fs.writeFileSync(path.join(dir,'SongSpec.edited.json'),JSON.stringify(edited,null,2));
 let second=await vm.runInContext('renderMixBuffer()',context);context.audio=second.buffer;let bytes2=Buffer.from(vm.runInContext('audioBufferToWav(audio)',context));fs.writeFileSync(path.join(dir,'edited.wav'),bytes2);
 // Separate VM process boundary is supplied by --reopen, using the exact saved file.
 const expected=JSON.stringify(edited,null,2);context.project=JSON.parse(fs.readFileSync(path.join(dir,'SongSpec.edited.json'),'utf8'));let reopen=vm.runInContext('loadProjectObject(project);serializeProject()',context)===expected;
 const changed=[];for(let i=0;i<bytes.length-44;i+=4){if(!bytes.subarray(44+i,48+i).equals(bytes2.subarray(44+i,48+i)))changed.push(i/4)}
 let rate=44100;const start=editStart/960*60/96*rate,end=editEnd/960*60/96*rate,tail=.1*rate;
 let outside=changed.filter(x=>x<start||x>end+tail);
 let structural=true;initial.tracks.forEach((tr,i)=>{const a=tr.events.filter(e=>e.tick<editStart||e.tick>=editEnd),b=edited.tracks[i].events.filter(e=>e.tick<editStart||e.tick>=editEnd);if(JSON.stringify(a)!==JSON.stringify(b))structural=false});
 const result={executor:'web-audio-engine@0.13.4; headless; existing renderMixBuffer; not browser',original_instrumental:true,initial_sha256:sha(bytes),edited_sha256:sha(bytes2),initial_metrics:rendered.metrics,edited_metrics:second.metrics,unchanged_symbolic_regions:structural,json_roundtrip:reopen,changed_sample_frames:changed.length,first_changed:changed[0],last_changed:changed.at(-1),outside_declared_edit_and_100ms_release_tail:outside.length,claim:'six-section fifty-second original instrumental candidate; no vocal/music-quality certification; offline/live DSP parity unearned'};
 const timeline={schema:'soundforge.production-timeline.v1',song_spec_sha256:sha(Buffer.from(JSON.stringify(edited,null,2))),revision_id:edited.revision_id,timebase:edited.timebase,sections:edited.structure.sections,tracks:edited.tracks};
 fs.writeFileSync(path.join(dir,'ProductionTimeline.json'),JSON.stringify(timeline,null,2));
 result.binding={song_spec_sha256:timeline.song_spec_sha256,production_timeline_sha256:sha(Buffer.from(JSON.stringify(timeline,null,2))),decoded_pcm_sha256:sha(bytes2.subarray(44)),app_core_sha256:sha(fs.readFileSync(path.join(root,'app-core.js'))),app_ui_sha256:sha(fs.readFileSync(path.join(root,'app-ui.js')))};
 fs.writeFileSync(path.join(dir,'render-receipt.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));if(!reopen||!structural||outside.length||!changed.length||!rendered.metrics.nonzero)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
