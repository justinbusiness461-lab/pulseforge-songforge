// Executes exact UI authority functions against real HTTP. Not a browser/PWA claim.
const fs=require('fs'),vm=require('vm'),path=require('path'),{spawn}=require('child_process');
const root=path.resolve(__dirname,'..'),base='http://127.0.0.1:18770';
const server=spawn('python3',['tools/studio_server.py'],{cwd:root,env:{...process.env,STUDIO_PORT:'18770'},stdio:'ignore'});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{let page;for(let i=0;i<50;i++){try{page=await(await fetch(base)).text();if(page.includes('__STUDIO_CAPABILITY__'))break;}catch{}await wait(100)}
const token=page.match(/window.__STUDIO_CAPABILITY__="([^"]+)"/)[1];
async function api(route,payload){const r=await fetch(base+'/api/projects/'+route,{method:'POST',headers:{Origin:base,'Content-Type':'application/json','X-Studio-Capability':token},body:JSON.stringify(payload)});return r.json()}
const spec1=JSON.parse(fs.readFileSync(root+'/evidence/m040/music/SongSpec.initial.json'));const spec2=JSON.parse(fs.readFileSync(root+'/evidence/m040/music/SongSpec.edited.json'));
const a=await api('commit',{projectId:null,expectedCurrentRevisionId:null,songSpec:spec1});const b=await api('commit',{projectId:a.manifest.projectId,expectedCurrentRevisionId:a.revision.revisionId,songSpec:spec2});
const cache=new Map([['sf_project',JSON.stringify({title:'corrupt stale browser song'})],['sf_project_ref',JSON.stringify({projectId:a.manifest.projectId,revisionId:a.revision.revisionId})]]);const accessed=[];const fields={projectId:{value:a.manifest.projectId},projectRevision:{textContent:''}};
const ctx={console,window:{__STUDIO_CAPABILITY__:token},document:{getElementById:id=>fields[id]||null},localStorage:{getItem:k=>{accessed.push(k);return cache.get(k)||null},setItem:(k,v)=>cache.set(k,v)},fetch:(url,opts)=>fetch(base+url,{...opts,headers:{...opts.headers,Origin:base}})};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(root+'/app-core.js','utf8'),ctx);ctx.$=id=>fields[id]||null;ctx.render=()=>{};ctx.setStatus=()=>{};
const ui=fs.readFileSync(root+'/app-ui.js','utf8');vm.runInContext(ui.slice(ui.indexOf('let durableProjectRef ='),ui.indexOf('$("btnCompile").onclick')),ctx);
await vm.runInContext('restoreProjectFromStorage()',ctx);const restored=JSON.parse(vm.runInContext('serializeProject()',ctx));
const exact=require("util").isDeepStrictEqual(restored,spec2);const authoritativeRef=vm.runInContext('durableProjectRef.revisionId',ctx)===b.revision.revisionId;
ctx.stale={projectId:a.manifest.projectId,revisionId:a.revision.revisionId};vm.runInContext('durableProjectRef=stale',ctx);let rejected=false;try{await vm.runInContext('saveJSON()',ctx)}catch(e){rejected=e.message.includes('stale')}
const current=await api('open',{projectId:a.manifest.projectId});
const result={ceiling:'exact UI functions in Node VM with minimal DOM/storage adapters and actual HTTP; not browser UI certification',ignores_full_browser_snapshot:!accessed.includes('sf_project'),opens_current_R2_over_stale_cache:exact&&authoritativeRef,stale_UI_save_rejected:rejected,current_R2_unchanged:current.manifest.currentRevisionId===b.revision.revisionId};
fs.writeFileSync(root+'/evidence/m042/ui-authority.json',JSON.stringify(result,null,2));console.log(result);if(!Object.entries(result).filter(([k])=>k!=='ceiling').every(([,v])=>v))throw Error('UI authority failed');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>server.kill());
