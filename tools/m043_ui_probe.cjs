// Exact lyric UI functions + real HTTP; minimal DOM adapter, not browser certification.
const fs=require('fs'),vm=require('vm'),path=require('path'),{spawn}=require('child_process');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:18771';
const server=spawn('python3',['tools/studio_server.py'],{cwd:root,env:{...process.env,STUDIO_PORT:'18771'},stdio:'ignore'});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let page;for(let i=0;i<100;i++){try{page=await(await fetch(base)).text();if(page.includes('__STUDIO_CAPABILITY__'))break;}catch{}await wait(50)}
 const token=page.match(/window.__STUDIO_CAPABILITY__="([^"]+)"/)[1];
 async function api(route,payload){const r=await fetch(base+'/api/'+route,{method:'POST',headers:{Origin:base,'Content-Type':'application/json','X-Studio-Capability':token},body:JSON.stringify(payload)});if(!r.ok)throw Error(await r.text());return r.json()}
 const spec=JSON.parse(fs.readFileSync(root+'/evidence/m043/fixtures/SongSpec.json'));
 const project=await api('projects/commit',{expectedCurrentRevisionId:null,songSpec:spec});
 const audio=await api('write_production_file',{filename:'ui-fixture.wav',subdirectory:'m043-ui',data_bytes:[...fs.readFileSync(root+'/evidence/m043/fixtures/rise-higher.wav')]});
 const r1=await api('projects/lyrics',{projectId:project.manifest.projectId,expectedCurrentRevisionId:project.revision.revisionId,action:'candidate',sourceArtifactId:audio.sha256,knownTranscript:'rise fire'});
 const node=()=>({value:'',textContent:'',children:[],append(...items){this.children.push(...items)},replaceChildren(){this.children=[]}});
 const fields={projectId:node(),projectRevision:node(),lyricWords:node(),lyricStatus:node()};
 const cache=new Map(),ctx={console,window:{__STUDIO_CAPABILITY__:token},document:{createElement:node},localStorage:{getItem:k=>cache.get(k)||null,setItem:(k,v)=>cache.set(k,v)},fetch:(url,opts)=>fetch(base+url,{...opts,headers:{...opts.headers,Origin:base}})};
 vm.createContext(ctx);ctx.$=id=>fields[id]||null;ctx.setStatus=()=>{};
 const ui=fs.readFileSync(root+'/app-ui.js','utf8');
 vm.runInContext(ui.slice(ui.indexOf('let durableProjectRef ='),ui.indexOf('$("btnCompile").onclick')),ctx);
 vm.runInContext(ui.slice(ui.indexOf('let durableLyricTimeline =')),ctx);
 ctx.r1=r1;vm.runInContext('showProjectAuthority(r1)',ctx);
 const checks={word_occurrences_rendered:fields.lyricWords.children.length===2,confidence_visible:fields.lyricStatus.textContent.includes('confidence unknown')};
 await vm.runInContext("saveLyricChange({action:'correct',expectedLyricRevisionId:r1.lyricTimeline.revisionId,changes:[{wordId:'w1',text:'higher'}],actor:'ui-test'})",ctx);
 const r2=await api('projects/open',{projectId:r1.manifest.projectId});
 checks.corrected_saved_word_visible=fields.lyricWords.children[1].children[0].textContent.startsWith('higher');
 checks.server_R2_authoritative=r2.lyricTimeline.parentRevisionId===r1.lyricTimeline.revisionId;
 ctx.r1=r1;vm.runInContext('showProjectAuthority(r1)',ctx);let rejected=false;
 try{await vm.runInContext("saveLyricChange({action:'correct',expectedLyricRevisionId:r1.lyricTimeline.revisionId,changes:[{wordId:'w1',text:'wrong'}],actor:'stale-ui'})",ctx)}catch(e){rejected=e.message.includes('stale')}
 checks.stale_UI_save_rejected=rejected;
 checks.no_transcript_cache=cache.size===1&&cache.has('sf_project_ref');
 fs.writeFileSync(root+'/evidence/m043/ui-lyrics.json',JSON.stringify({checks,ceiling:'Node VM exact UI functions, minimal DOM, real HTTP; no browser/PWA claim'},null,2)+'\n');
 console.log(checks);if(!Object.values(checks).every(Boolean))throw Error('lyric UI failed');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>server.kill());
