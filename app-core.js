const TPQ=960;
const SCALES={
"F# minor":{root:42,scale:[0,2,3,5,7,8,10],lead:[66,69,71,73]},
"A minor":{root:45,scale:[0,2,3,5,7,8,10],lead:[69,72,74,76]},
"C minor":{root:36,scale:[0,2,3,5,7,8,10],lead:[60,63,65,67]},
"D minor":{root:38,scale:[0,2,3,5,7,8,10],lead:[62,65,67,69]},
"E minor":{root:40,scale:[0,2,3,5,7,8,10],lead:[64,67,69,71]},
"G major":{root:43,scale:[0,2,4,5,7,9,11],lead:[67,71,74,76]}
};
function parsePrompt(text){
const p=(text||"").toLowerCase();
let bpm=102;const m=p.match(/(\d{2,3})\s*bpm/);if(m)bpm=Math.max(60,Math.min(180,parseInt(m[1],10)));
let key="F# minor";
for(const k of Object.keys(SCALES)){if(p.includes(k.toLowerCase())){key=k;break}}
if(p.includes("c minor"))key="C minor";
if(p.includes("a minor"))key="A minor";
if(p.includes("d minor"))key="D minor";
let genre="alt-hip-hop";
if(p.includes("house")||p.includes("club"))genre="house";
else if(p.includes("blues"))genre="electro-blues";
else if(p.includes("trap"))genre="trap";
else if(p.includes("lo-fi")||p.includes("lofi"))genre="lo-fi";
const dark=/dark|smoky|noir|sparse|minimal/.test(p);
const form=[
{name:"Intro",type:"intro",bars:2,role:"none"},
{name:"Verse",type:"verse",bars:4,role:"male"},
{name:"Chorus",type:"chorus",bars:4,role:"both"},
{name:"Verse",type:"verse",bars:4,role:"male"},
{name:"Chorus",type:"chorus",bars:4,role:"both"},
{name:"Outro",type:"outro",bars:2,role:"none"}
];
if(p.includes("bridge"))form.splice(4,0,{name:"Bridge",type:"bridge",bars:2,role:"female"});
let tick=0;
const sections=form.map(s=>{const start=tick;tick+=s.bars*4*TPQ;return{id:"sec-"+start,name:s.name,type:s.type,start_tick:start,end_tick:tick,role:s.role,lyrics:s.type==="chorus"?"It's a bad habit\nBut I can't break it":s.type==="verse"?"Late night, same streetlight":""}});
const sc=SCALES[key]||SCALES["F# minor"];
const drums={track_id:"drums",name:"Drums",type:"DRUMS",volume_db:dark?-3:-1,pan:0,muted:false,events:[]};
const bass={track_id:"bass",name:"Bass",type:"BASS",volume_db:-2,pan:0,muted:false,events:[]};
const lead={track_id:"lead",name:"Lead",type:"LEAD",volume_db:-5,pan:-0.2,muted:false,events:[]};
const pad={track_id:"pad",name:"Pad",type:"PAD",volume_db:-9,pan:0.15,muted:false,events:[]};
const totalTicks=tick,barTicks=4*TPQ,eighth=TPQ/2;
for(let bar=0;bar*barTicks<totalTicks;bar++){
const base=bar*barTicks;
drums.events.push({type:"NOTE_ON",tick:base,note_number:36,velocity:115,duration_ticks:200});
if(!dark||bar%2===0)drums.events.push({type:"NOTE_ON",tick:base+2*TPQ,note_number:38,velocity:100,duration_ticks:180});
for(let e=0;e<8;e++){if(dark&&e%2===1)continue;drums.events.push({type:"NOTE_ON",tick:base+e*eighth,note_number:42,velocity:e%2===0?70:45,duration_ticks:80})}
if(genre==="trap")drums.events.push({type:"NOTE_ON",tick:base+3*TPQ,note_number:38,velocity:90,duration_ticks:160});
}
const progression=[0,0,5,3,0,7,5,0];
for(let bar=0;bar*barTicks<totalTicks;bar++){
const deg=progression[bar%progression.length];
const note=sc.root+sc.scale[deg%sc.scale.length];
const base=bar*barTicks,dens=dark?2:4;
for(let i=0;i<dens;i++)bass.events.push({type:"NOTE_ON",tick:base+i*(barTicks/dens),note_number:note,velocity:105,duration_ticks:Math.floor(barTicks/dens)-40});
}
sections.forEach(sec=>{if(sec.type==="intro"||sec.type==="outro")return;const deg=sec.type==="chorus"?0:5;pad.events.push({type:"NOTE_ON",tick:sec.start_tick,note_number:sc.root+12+sc.scale[deg%sc.scale.length],velocity:70,duration_ticks:sec.end_tick-sec.start_tick-100})});
sections.filter(s=>s.type==="chorus"||s.type==="bridge").forEach(sec=>{for(let i=0;i<4;i++)lead.events.push({type:"NOTE_ON",tick:sec.start_tick+i*TPQ,note_number:sc.lead[i%sc.lead.length],velocity:95,duration_ticks:TPQ-80})});
return{$schema:"pulseforge.songforge.skeleton.v2.5",song_id:"sf-"+Date.now().toString(36),title:"Generated",timebase:{ticks_per_quarter_note:TPQ,initial_bpm:bpm,sample_rate:44100,key,genre,meter:"4/4"},structure:{sections},tracks:[drums,bass,pad,lead],prompt:text,created_at:new Date().toISOString()};
}
let skeleton=null,audioCtx=null,playing=false,nodes=[];
const $=id=>document.getElementById(id);
function setStatus(msg,kind){$("status").textContent=msg;$("status").className="status "+(kind||"ok")}
function midiToFreq(n){return 440*Math.pow(2,(n-69)/12)}
function ticksToSec(ticks){return(ticks/TPQ)*(60/skeleton.timebase.initial_bpm)}
function totalTicks(){return skeleton.structure.sections.reduce((m,s)=>Math.max(m,s.end_tick),0)}
function ensureAudio(){if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext);if(audioCtx.state==="suspended")audioCtx.resume();return audioCtx}
function playKick(ctx,t,g,dest){const o=ctx.createOscillator(),gn=ctx.createGain();o.frequency.setValueAtTime(150,t);o.frequency.exponentialRampToValueAtTime(40,t+0.12);gn.gain.setValueAtTime(0.55*g,t);gn.gain.exponentialRampToValueAtTime(0.001,t+0.28);o.connect(gn);gn.connect(dest);o.start(t);o.stop(t+0.3);nodes.push(o)}
function playSnare(ctx,t,g,dest){const len=Math.floor(ctx.sampleRate*0.12),buf=ctx.createBuffer(1,len,ctx.sampleRate),d=buf.getChannelData(0);for(let i=0;i<len;i++)d[i]=(Math.random()*2-1)*Math.exp(-10*i/len);const src=ctx.createBufferSource(),gn=ctx.createGain(),f=ctx.createBiquadFilter();src.buffer=buf;f.type="bandpass";f.frequency.value=2800;gn.gain.setValueAtTime(0.35*g,t);gn.gain.exponentialRampToValueAtTime(0.001,t+0.12);src.connect(f);f.connect(gn);gn.connect(dest);src.start(t);nodes.push(src)}
function playHat(ctx,t,g,dest){const len=Math.floor(ctx.sampleRate*0.04),buf=ctx.createBuffer(1,len,ctx.sampleRate),d=buf.getChannelData(0);for(let i=0;i<len;i++)d[i]=(Math.random()*2-1)*Math.exp(-14*i/len);const src=ctx.createBufferSource(),gn=ctx.createGain(),f=ctx.createBiquadFilter();src.buffer=buf;f.type="highpass";f.frequency.value=7000;gn.gain.value=0.12*g;src.connect(f);f.connect(gn);gn.connect(dest);src.start(t);nodes.push(src)}
function playNote(ctx,note,t,dur,type,g,dest,opts){opts=opts||{};const o=ctx.createOscillator(),gn=ctx.createGain();o.type=type;o.frequency.value=midiToFreq(note);gn.gain.setValueAtTime(0,t);gn.gain.linearRampToValueAtTime(g,t+(opts.attack||0.02));gn.gain.setValueAtTime(g*(opts.sustain||0.7),t+dur*0.6);gn.gain.exponentialRampToValueAtTime(0.001,t+Math.max(0.06,dur));let node=o;if(opts.filter){const f=ctx.createBiquadFilter();f.type="lowpass";f.frequency.value=opts.filter;o.connect(f);node=f}node.connect(gn);gn.connect(dest);o.start(t);o.stop(t+dur+0.08);nodes.push(o)}
function stopAll(){nodes.forEach(n=>{try{n.stop()}catch(e){}});nodes=[];playing=false;$("prog").style.width="0%";$("btnPlay").textContent="Play"}
function playScore(){if(!skeleton)compile();stopAll();const ctx=ensureAudio();playing=true;$("btnPlay").textContent="Stop";setStatus("Playing Score Graph…","ok");const t0=ctx.currentTime+0.06,total=ticksToSec(totalTicks());
skeleton.tracks.forEach(track=>{if(track.muted)return;const gScale=Math.pow(10,(track.volume_db||0)/20);const gain=ctx.createGain();gain.gain.value=gScale;gain.connect(ctx.destination);
track.events.forEach(ev=>{if(ev.type!=="NOTE_ON")return;const t=t0+ticksToSec(ev.tick),dur=ticksToSec(ev.duration_ticks||TPQ/2),vel=(ev.velocity||100)/127;
if(track.type==="DRUMS"){if(ev.note_number===36)playKick(ctx,t,vel,gain);else if(ev.note_number===38)playSnare(ctx,t,vel,gain);else playHat(ctx,t,vel,gain)}
else if(track.type==="BASS")playNote(ctx,ev.note_number,t,dur,"sawtooth",0.22*vel,gain,{filter:900,attack:0.01,sustain:0.6});
else if(track.type==="PAD")playNote(ctx,ev.note_number,t,dur,"triangle",0.1*vel,gain,{attack:0.12,sustain:0.85});
else playNote(ctx,ev.note_number,t,dur*0.7,"square",0.12*vel,gain,{filter:4000,attack:0.005,sustain:0.2})})});
const tick=()=>{if(!playing)return;const e=audioCtx.currentTime-t0;$("prog").style.width=Math.min(100,(e/total)*100)+"%";if(e<total)requestAnimationFrame(tick);else{stopAll();setStatus("Playback complete","ok");$("prog").style.width="100%"}};requestAnimationFrame(tick)}
