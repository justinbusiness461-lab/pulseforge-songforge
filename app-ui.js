
/** Tauri IPC bridge — no-op in plain browser */
function hasNativeShell() {
  return !!(window.__TAURI_IPC__ || (window.__TAURI__ && window.__TAURI__.core));
}
function logToNative(eventType, message) {
  console.log("[UI-Log] [" + eventType + "] " + message);
  try {
    if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke) {
      window.__TAURI__.core.invoke("native_log_event", {
        eventType: String(eventType),
        message: String(message)
      }).catch(function (err) { console.warn("[Tauri]", err); });
    } else if (window.__TAURI__ && window.__TAURI__.tauri && window.__TAURI__.tauri.invoke) {
      window.__TAURI__.tauri.invoke("native_log_event", {
        eventType: String(eventType),
        message: String(message)
      }).catch(function (err) { console.warn("[Tauri]", err); });
    }
  } catch (e) { /* browser-only */ }
}

let activeSectionIdx = 0;

function render() {
  if (!skeleton) return;
  const tb = skeleton.timebase;
  $("meta").innerHTML =
    "<strong>" + (skeleton.title || "Song") + "</strong> · " +
    tb.initial_bpm + " BPM · " + tb.key + " · " + tb.genre +
    "<br/><span style='color:var(--m);font-size:0.75rem'>" + skeleton.song_id +
    " · " + skeleton.tracks.length + " tracks · Phase 4 spatial + vocal</span>";

  $("sections").innerHTML = skeleton.structure.sections.map((s, i) =>
    "<span class='badge" + (i === activeSectionIdx ? " role" : "") + (s.muted ? " muted" : "") + "' data-sec='" + i + "' data-sid='" + s.id + "' style='cursor:pointer'>" +
    s.name + (s.role !== "none" ? " · " + s.role : "") + (s.muted ? " · MUTE" : "") + "</span>"
  ).join("") +
  "<div style='margin-top:8px;display:flex;gap:6px;flex-wrap:wrap'>" +
  "<button class='secondary sm' id='btnSecMute'>Mute section</button>" +
  "<button class='secondary sm' id='btnSecDup'>Duplicate section</button>" +
  "<button class='secondary sm' id='btnRestore'>Restore last save</button>" +
  "</div>";
  document.querySelectorAll("[data-sec]").forEach(el => {
    el.onclick = () => {
      activeSectionIdx = +el.dataset.sec;
      syncSectionEditors();
      render();
    };
  });
  syncSectionEditors();

  const btnSecMute = $("btnSecMute");
  if (btnSecMute) btnSecMute.onclick = () => {
    const sec = skeleton.structure.sections[activeSectionIdx];
    if (!sec) return;
    const r = muteSectionEvents(sec.id, !sec.muted);
    if (r.ok) { render(); setStatus((sec.muted ? "Muted" : "Unmuted") + " section " + sec.name, "ok"); }
  };
  const btnSecDup = $("btnSecDup");
  if (btnSecDup) btnSecDup.onclick = () => {
    const sec = skeleton.structure.sections[activeSectionIdx];
    if (!sec) return;
    const r = duplicateSection(sec.id);
    if (r.ok) { activeSectionIdx = skeleton.structure.sections.length - 1; render(); setStatus("Duplicated → " + r.section_id, "ok"); }
  };
  const btnRestore = $("btnRestore");
  if (btnRestore) btnRestore.onclick = () => {
    restoreProjectFromStorage().catch(e => setStatus('Open failed: ' + e.message, 'warn'));
  };


  const mix = $("mixer");
  mix.innerHTML = "";
  const sel = $("editTrack");
  sel.innerHTML = "";
  skeleton.tracks.forEach(tr => {
    const opt = document.createElement("option");
    opt.value = tr.track_id;
    opt.textContent = tr.name + " [" + tr.type + "]";
    sel.appendChild(opt);
    const el = document.createElement("div");
    el.className = "strip";
    el.innerHTML =
      "<div class='strip-name'>" + tr.name + "</div>" +
      "<div class='strip-row'>" +
      "<label>Vol</label><input type='range' min='-24' max='6' step='0.5' value='" + (tr.volume_db || 0) + "' data-vol='" + tr.track_id + "'/>" +
      "<label>Pan</label><input type='range' min='-1' max='1' step='0.05' value='" + (tr.pan || 0) + "' data-pan='" + tr.track_id + "'/>" +
      "<button class='secondary sm' data-mute='" + tr.track_id + "'>" + (tr.muted ? "Unmute" : "Mute") + "</button>" +
      "</div>";
    mix.appendChild(el);
  });
  mix.querySelectorAll("[data-vol]").forEach(inp => {
    inp.oninput = () => {
      const t = skeleton.tracks.find(x => x.track_id === inp.dataset.vol);
      if (t) t.volume_db = +inp.value;
    };
  });
  mix.querySelectorAll("[data-pan]").forEach(inp => {
    inp.oninput = () => {
      const t = skeleton.tracks.find(x => x.track_id === inp.dataset.pan);
      if (t) t.pan = +inp.value;
    };
  });
  mix.querySelectorAll("[data-mute]").forEach(btn => {
    btn.onclick = () => {
      const t = skeleton.tracks.find(x => x.track_id === btn.dataset.mute);
      if (!t) return;
      t.muted = !t.muted;
      btn.textContent = t.muted ? "Unmute" : "Mute";
      btn.style.background = t.muted ? "var(--danger)" : "";
      btn.style.color = t.muted ? "#fff" : "";
    };
  });
  drawMatrix();
  if (typeof updateTrustChips === "function") updateTrustChips();
}

function syncSectionEditors() {
  if (!skeleton) return;
  const sec = skeleton.structure.sections[activeSectionIdx];
  if (!sec) return;
  const lyr = $("lyrics");
  const role = $("vocalRole");
  if (lyr) lyr.value = sec.lyrics || "";
  if (role) role.value = sec.role || "none";
}

function drawMatrix() {
  const box = $("matrix");
  box.innerHTML = "";
  if (!skeleton) return;
  const track = skeleton.tracks.find(t => t.track_id === $("editTrack").value);
  if (!track) return;
  const step = TPQ / 2;
  for (let i = 0; i < 16; i++) {
    const tick = i * step;
    const cell = document.createElement("div");
    cell.className = "cell";
    const hit = track.events.find(e => Math.abs(e.tick - tick) < 20);
    if (hit) {
      cell.classList.add("on");
      if (hit.note_number === 36) cell.classList.add("kick");
    }
    cell.onclick = () => {
      if (hit) track.events = track.events.filter(e => e !== hit);
      else {
        const note = track.type === "DRUMS" ? 36 : track.type === "BASS" ? 36 : track.type === "VOCAL" ? 57 : 60;
        track.events.push({
          type: "NOTE_ON", tick, note_number: note, velocity: 100,
          duration_ticks: step - 40, phoneme: "ah", word: "ah", role: "male"
        });
      }
      drawMatrix();
    };
    box.appendChild(cell);
  }
}

function compile(opts) {
  opts = opts || {};
  if (typeof SongForgeChat !== "undefined" && SongForgeChat.chatGenerate && opts.fromChat) {
    return SongForgeChat.chatGenerate();
  }
  const text = ($("prompt").value || "").trim() ||
    "dark 102 BPM alt hip-hop, F# minor, guitar plucks, male verse";
  if (typeof pushSkeletonCheckpoint === "function" && skeleton) pushSkeletonCheckpoint("before_compile");
  const parseOpts = {};
  if (opts.seed != null) parseOpts.seed = opts.seed;
  if (opts.nonce != null) parseOpts.nonce = opts.nonce;
  skeleton = parsePrompt(text, parseOpts);
  window.skeleton = skeleton;
  const titleEl = $("title");
  skeleton.title = (titleEl && titleEl.value) ? titleEl.value : (text.slice(0, 40) || "Generated");
  const bpmO = $("bpmOverride");
  if (bpmO && bpmO.value) skeleton.timebase.initial_bpm = Math.max(60, Math.min(180, +bpmO.value));
  const keyO = $("keyOverride");
  if (keyO && keyO.value) skeleton.timebase.key = keyO.value;
  if (typeof appendChangeLedger === "function") {
    appendChangeLedger("compile", { seed: skeleton.generation_seed, song_id: skeleton.song_id, prompt: text });
  }
  activeSectionIdx = 0;
  render();
  if (typeof updateTrustChips === "function") updateTrustChips();
  if (typeof persistChatSession === "function") persistChatSession();
  setStatus(
    "Compiled · " + skeleton.timebase.initial_bpm + " BPM · " + skeleton.timebase.key +
    " · seed " + skeleton.generation_seed + " · " + skeleton.song_id,
    "ok"
  );
}

function audioBufferToWav(buffer) {
  const nCh = buffer.numberOfChannels, sr = buffer.sampleRate, len = buffer.length;
  const ab = new ArrayBuffer(44 + len * nCh * 2), v = new DataView(ab);
  const w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  w(0, "RIFF"); v.setUint32(4, 36 + len * nCh * 2, true); w(8, "WAVE"); w(12, "fmt ");
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, nCh, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * nCh * 2, true);
  v.setUint16(32, nCh * 2, true); v.setUint16(34, 16, true);
  w(36, "data"); v.setUint32(40, len * nCh * 2, true);
  let off = 44;
  const ch = [];
  for (let c = 0; c < nCh; c++) ch.push(buffer.getChannelData(c));
  for (let i = 0; i < len; i++) for (let c = 0; c < nCh; c++) {
    let s = Math.max(-1, Math.min(1, ch[c][i]));
    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true); off += 2;
  }
  return ab;
}


/** Offline render of current skeleton; returns {buffer, metrics} with RMS/peak proof. */
async function renderMixBuffer() {
  if (!skeleton) compile();
  const sr = 44100;
  const dur = ticksToSec(totalTicks()) + 0.5;
  const off = new OfflineAudioContext(2, Math.ceil(sr * dur), sr);
  skeleton.tracks.forEach(track => {
    if (track.muted) return;
    const gScale = Math.pow(10, (track.volume_db || 0) / 20);
    track.events.forEach(ev => {
      if (ev.type !== "NOTE_ON" || ev.velocity === 0) return;
      const rnd = mulberry32(hashSeed(track.track_id + "|" + ev.tick + "|" + (skeleton.generation_seed || 0)));
      const t = ticksToSec(ev.tick);
      const durN = ticksToSec(ev.duration_ticks || TPQ / 2);
      const vel = (ev.velocity || 100) / 127;
      if (track.type === "DRUMS") {
        if (ev.note_number === 36) {
          const o = off.createOscillator(), gn = off.createGain();
          o.frequency.setValueAtTime(150, t);
          o.frequency.exponentialRampToValueAtTime(40, t + 0.12);
          gn.gain.setValueAtTime(0.45 * gScale * vel, t);
          gn.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
          o.connect(gn); gn.connect(off.destination);
          o.start(t); o.stop(t + 0.28);
        } else if (ev.note_number === 38) {
          const len = Math.floor(sr * 0.12);
          const buf = off.createBuffer(1, len, sr);
          const d = buf.getChannelData(0);
          for (let i = 0; i < len; i++) d[i] = (rnd() * 2 - 1) * Math.exp(-12 * i / len);
          const src = off.createBufferSource(), gn = off.createGain();
          src.buffer = buf;
          gn.gain.setValueAtTime(0.35 * gScale * vel, t);
          gn.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
          src.connect(gn); gn.connect(off.destination);
          src.start(t);
        } else {
          const o = off.createOscillator(), gn = off.createGain();
          o.type = "square";
          o.frequency.value = 8000;
          gn.gain.setValueAtTime(0.08 * gScale * vel, t);
          gn.gain.exponentialRampToValueAtTime(0.001, t + 0.04);
          o.connect(gn); gn.connect(off.destination);
          o.start(t); o.stop(t + 0.05);
        }
      } else if (track.type === "BASS" || track.type === "LEAD" || track.type === "PAD" || track.type === "VOCAL" || track.type === "STRINGS") {
        const o = off.createOscillator(), gn = off.createGain();
        o.type = track.type === "BASS" ? "sawtooth" : (track.type === "PAD" ? "triangle" : "sine");
        o.frequency.value = midiToFreq(ev.note_number);
        gn.gain.setValueAtTime(0, t);
        gn.gain.linearRampToValueAtTime(0.14 * gScale * vel, t + 0.02);
        gn.gain.exponentialRampToValueAtTime(0.001, t + Math.max(0.05, durN));
        o.connect(gn); gn.connect(off.destination);
        o.start(t); o.stop(t + durN + 0.05);
      }
    });
  });
  const buffer = await off.startRendering();
  let peak = 0, sumSq = 0, n = 0;
  for (let c = 0; c < buffer.numberOfChannels; c++) {
    const data = buffer.getChannelData(c);
    for (let i = 0; i < data.length; i++) {
      const s = data[i];
      const a = Math.abs(s);
      if (a > peak) peak = a;
      sumSq += s * s;
      n++;
    }
  }
  const rms = n ? Math.sqrt(sumSq / n) : 0;
  const metrics = {
    duration_sec: buffer.duration,
    sample_rate: buffer.sampleRate,
    channels: buffer.numberOfChannels,
    peak: peak,
    rms: rms,
    nonzero: rms > 1e-5,
    frames: buffer.length
  };
  return { buffer, metrics };
}

async function exportWav() {
  if (!skeleton) compile();
  const renderSpec = JSON.parse(serializeProject());
  const expectedRef = durableProjectRef && { ...durableProjectRef };
  const renderSourceAssets = durableSourceAssets.slice();
  setStatus("Rendering mix WAV…", "warn");
  try {
    const { buffer, metrics } = await renderMixBuffer();
    if (!metrics.nonzero) {
      setStatus("Export blocked: silent buffer (RMS=" + metrics.rms.toFixed(6) + ")", "warn");
      return null;
    }
    const wav = audioBufferToWav(buffer);
    const written = await fetch('/api/write_production_file', {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Studio-Capability': window.__STUDIO_CAPABILITY__ || '' },
      body: JSON.stringify({ filename: (renderSpec.song_id || 'song') + '_mix.wav', subdirectory: 'audio-masters', data_bytes: Array.from(new Uint8Array(wav)) })
    });
    const artifact = await written.json();
    if (!written.ok || artifact.status !== 'SUCCESS') throw new Error(artifact.error || 'Export persistence failed');
    await commitProjectSnapshot(renderSpec, [artifact.sha256], expectedRef, renderSourceAssets);
    if (artifact.sha256 && typeof setLastExportDigest === "function") setLastExportDigest(artifact.sha256);
    if (typeof SongForgeChat !== "undefined" && SongForgeChat.pushMessage) {
      SongForgeChat.pushMessage("system", "WAV exported · sha256:" + String(artifact.sha256).slice(0, 16) + "…", { action: "export_wav" });
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([wav], { type: "audio/wav" }));
    a.download = (renderSpec.song_id || "song") + "_mix.wav";
    a.click();
    setStatus(
      "Mix WAV exported · " + metrics.duration_sec.toFixed(1) + "s · peak " +
      metrics.peak.toFixed(3) + " · RMS " + metrics.rms.toFixed(4),
      "ok"
    );
    return metrics;
  } catch (e) {
    setStatus("Export failed: " + e.message, "warn");
    return null;
  }
}

function exportMEG() {
  if (!skeleton) compile();
  logToNative("EXPORT_MEG", "Compiling Cinema Music Event Graph");
  const events = [];
  const bpm = skeleton.timebase.initial_bpm;
  skeleton.structure.sections.forEach(s => {
    events.push({
      type: "SECTION_START", tick: s.start_tick,
      sample: Math.round(ticksToSec(s.start_tick) * 44100),
      name: s.name, vocal_role: s.role, lyrics: s.lyrics || ""
    });
    events.push({
      type: "SECTION_END", tick: s.end_tick,
      sample: Math.round(ticksToSec(s.end_tick) * 44100),
      name: s.name
    });
  });
  const vocal = skeleton.tracks.find(t => t.type === "VOCAL");
  if (vocal) {
    vocal.events.forEach(ev => {
      events.push({
        type: "PHONEME",
        tick: ev.tick,
        sample: Math.round(ticksToSec(ev.tick) * 44100),
        end_sample: Math.round(ticksToSec(ev.tick + (ev.duration_ticks || TPQ / 2)) * 44100),
        phoneme: ev.phoneme || "ah",
        word: ev.word || "",
        note: ev.note_number,
        role: ev.role || "male",
        viseme: (ev.phoneme === "ee" ? "E" : ev.phoneme === "oo" ? "U" : ev.phoneme === "oh" ? "O" : "A")
      });
    });
  }

  // Auto-run cinematic viseme preview from exported phonemes
  const visemeChain = [];
  events.forEach(ev => {
    if (ev.type === "PHONEME" && (ev.viseme || ev.phoneme)) {
      visemeChain.push(ev.viseme || ev.phoneme);
    }
  });
  if (!visemeChain.length) visemeChain.push("A", "E", "O", "U");
  if (window.pulseForgeCinemaSync) {
    logToNative("HARNESS_SOLVER", "Driving viewport with " + visemeChain.length + " visemes");
    window.pulseForgeCinemaSync.animateVocalPerformanceLoop(visemeChain, 280);
    visemeChain.slice(0, 8).forEach(v => {
      const t = window.pulseForgeCinemaSync.solveVisemeMechanics(v);
      logToNative("HARNESS_OUTPUT", "Viseme [" + t.viseme + "] jawY=" + t.jawY + " scaleX=" + t.scaleX);
    });
  }

  events.sort((a, b) => a.tick - b.tick);
  const meg = {
    $schema: "pulseforge.music_event_graph.v2",
    song_id: skeleton.song_id,
    timebase: skeleton.timebase,
    events,
    generated_at: new Date().toISOString()
  };
  const megName = (skeleton.song_id || "song") + "_MusicEventGraph.json";
  savePayload(megName, JSON.stringify(meg, null, 2), "meg", "application/json");
  setStatus("Music Event Graph + viseme preview exported", "ok");
  logToNative("EXPORT_COMPLETE", "MEG written");
}

let durableProjectRef = null;
let durableSourceAssets = [];

async function projectRequest(route, payload) {
  const response = await fetch('/api/projects/' + route, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Studio-Capability': window.__STUDIO_CAPABILITY__ || '' },
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  if (!response.ok || result.status !== 'SUCCESS') throw new Error(result.error || 'Project request failed');
  return result;
}

function showProjectAuthority(result) {
  durableProjectRef = { projectId: result.manifest.projectId, revisionId: result.revision.revisionId };
  durableSourceAssets = result.revision.sourceAssetDigests.slice();
  try { localStorage.setItem('sf_project_ref', JSON.stringify(durableProjectRef)); } catch (_) {}
  if ($('projectId')) $('projectId').value = durableProjectRef.projectId;
  if ($('projectRevision')) $('projectRevision').textContent = 'Saved revision: ' + durableProjectRef.revisionId;
}

async function commitProjectSnapshot(spec, outputArtifactIds, expectedRef, sourceAssets = durableSourceAssets.slice()) {
  const entered = $('projectId') && $('projectId').value.trim();
  if ((!expectedRef && entered) || (expectedRef && entered !== expectedRef.projectId)) throw new Error('Open the selected project before saving, or choose New project');
  const result = await projectRequest('commit', {
    projectId: expectedRef ? expectedRef.projectId : null,
    expectedCurrentRevisionId: expectedRef ? expectedRef.revisionId : null,
    songSpec: spec,
    sourceAssetDigests: sourceAssets,
    outputArtifactIds: outputArtifactIds || []
  });
  const active = durableProjectRef;
  if ((!expectedRef && !active) || (expectedRef && active && expectedRef.projectId === active.projectId && expectedRef.revisionId === active.revisionId)) {
    showProjectAuthority(result);
  }
  return result;
}

async function saveJSON() {
  if (!skeleton) compile();
  // Capture draft and expected pointer together; pending edits cannot change the commit.
  const spec = JSON.parse(serializeProject());
  const expected = durableProjectRef && { ...durableProjectRef };
  const result = await commitProjectSnapshot(spec, [], expected);
  setStatus('Project saved · ' + result.manifest.projectId, 'ok');
  return result;
}

async function restoreProjectFromStorage() {
  let id = $('projectId') && $('projectId').value.trim();
  if (!id) {
    // Cache contains an address only, never the song or the authoritative pointer.
    try { id = JSON.parse(localStorage.getItem('sf_project_ref') || '{}').projectId; } catch (_) {}
  }
  if (!id) throw new Error('Enter a durable project ID');
  const result = await projectRequest('open', { projectId: id });
  const loaded = loadProjectObject(result.songSpec);
  if (!loaded.ok) throw new Error(loaded.error);
  showProjectAuthority(result);
  if ($('title')) $('title').value = result.songSpec.title || '';
  if ($('prompt')) $('prompt').value = result.songSpec.prompt || '';
  render();
  setStatus('Opened durable revision · ' + result.revision.revisionId, 'ok');
  return result;
}


$("btnCompile").onclick = compile;
$("btnPlay").onclick = () => {
  if (playing) {
    stopAll();
    if (window.pulseForgeCinemaSync) window.pulseForgeCinemaSync.stopLoop();
    logToNative("TRANSPORT", "stopped");
  } else {
    logToNative("TRANSPORT", "play");
    playScore();
    if (window.pulseForgeCinemaSync) {
      const chain = ["REST", "A", "E", "REST", "O", "U", "REST", "A", "E", "O", "U"];
      let fromEvents = chain;
      if (skeleton) {
        const vocal = skeleton.tracks.find(t => t.type === "VOCAL");
        if (vocal && vocal.events.length) {
          fromEvents = vocal.events.slice(0, 16).map(e => e.viseme || e.phoneme || "A");
        }
      }
      window.pulseForgeCinemaSync.animateVocalPerformanceLoop(fromEvents, 300);
    }
  }
};
$("btnStop").onclick = () => {
  stopAll();
  if (window.pulseForgeCinemaSync) window.pulseForgeCinemaSync.stopLoop();
  setStatus("Stopped");
  logToNative("TRANSPORT", "stopped");
};
$("btnWav").onclick = exportWav;
$("btnMEG").onclick = exportMEG;
$("btnSave").onclick = () => saveJSON().catch(e => setStatus("Save failed: " + e.message, "warn"));
$("editTrack").onchange = drawMatrix;

const lyricsEl = $("lyrics");
if (lyricsEl) {
  lyricsEl.oninput = () => {
    if (!skeleton) return;
    const sec = skeleton.structure.sections[activeSectionIdx];
    if (sec) {
      if (typeof applySectionLyrics === "function") applySectionLyrics(sec.id, lyricsEl.value);
      else { sec.lyrics = lyricsEl.value; rebuildVocalsFromLyrics(); }
      drawMatrix();
      if (typeof persistChatSession === "function") persistChatSession();
    }
  };
}
const roleEl = $("vocalRole");
if (roleEl) {
  roleEl.onchange = () => {
    if (!skeleton) return;
    const sec = skeleton.structure.sections[activeSectionIdx];
    if (sec) {
      if (typeof applySectionRole === "function") applySectionRole(sec.id, roleEl.value);
      else { sec.role = roleEl.value; rebuildVocalsFromLyrics(); }
      render();
      if (typeof persistChatSession === "function") persistChatSession();
    }
  };
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {});
  });
}

if ($("prompt") && !$("prompt").value) {
  $("prompt").value = "dark 102 BPM alt hip-hop, F# minor, guitar plucks, male verse, female chorus";
}
// Initial compile deferred to initChatStudio() (session restore or welcome Generate path).
if (typeof initChatStudio !== "function") {
  compile({ nonce: "0" });
}

const btnLoad = $("btnLoad");
const fileIn = $("fileIn");
if (btnLoad && fileIn) {
  btnLoad.onclick = () => fileIn.click();
  fileIn.onchange = (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      try {
        const d = JSON.parse(r.result);
        if (d.structure && d.tracks) {
          const lr = loadProjectObject(d);
          if (!lr.ok) { setStatus("Load failed: " + lr.error, "warn"); return; }
          if ($("title") && d.title) $("title").value = d.title;
          if ($("prompt") && d.prompt) $("prompt").value = d.prompt;
          render();
          setStatus("ScoreGraph loaded", "ok");
        } else setStatus("Not a SongSpec JSON", "warn");
      } catch (err) { setStatus("Load failed: " + err.message, "warn"); }
    };
    r.readAsText(f);
  };
}

logToNative("ENGINE_INIT", "Sound Forge UI ready · Tauri=" + hasNativeShell());



/* Phase 6 UI: mic ingest + look-at armature */
let lookAtTarget = { x: 0, y: 1.75, z: 4 };

async function toggleMicrophoneIngest(btn) {
  if (typeof micActive !== "undefined" && micActive) {
    disconnectLiveMicrophone();
    if (btn) {
      btn.textContent = "Enable Mic Ingest";
      btn.style.background = "";
      btn.style.color = "";
    }
    setStatus("Mic closed", "ok");
    logToNative("MIC_INGEST", "closed");
    return;
  }
  const ok = await initLiveMicrophoneIngest(function (hz) {
    const st = $("micHz");
    if (st) st.textContent = hz.toFixed(1) + " Hz";
    if (window.pulseForgeCinemaSync) {
      const map = ["A", "E", "O", "U"];
      // Map pitch bands roughly to visemes for visual feedback
      let v = "A";
      if (hz < 120) v = "O";
      else if (hz < 180) v = "A";
      else if (hz < 280) v = "E";
      else v = "U";
      window.pulseForgeCinemaSync.solveVisemeMechanics(v);
    }
    logToNative("MIC_TELEMETRY", hz.toFixed(1) + " Hz");
  });
  if (ok) {
    if (btn) {
      btn.textContent = "Mic Active";
      btn.style.background = "var(--ok)";
      btn.style.color = "#000";
    }
    setStatus("Mic ingest active · pitch → viseme", "ok");
    logToNative("MIC_INGEST", "active");
  } else {
    setStatus("Mic unavailable — using synthetic guides", "warn");
    logToNative("MIC_INGEST", "denied");
  }
}

function updateLookAtTrackingTarget(val, dim) {
  lookAtTarget[dim] = parseFloat(val);
  if (window.pulseForgeCinemaSync) {
    window.pulseForgeCinemaSync.solveAnatomicalBones(
      lookAtTarget.x, lookAtTarget.y, lookAtTarget.z
    );
  }
}



/** Invoke Tauri write or browser download for a UTF-8 / binary payload */
function savePayload(filename, data, subdirectory, mime) {
  mime = mime || "application/octet-stream";
  const bytes =
    typeof data === "string"
      ? new TextEncoder().encode(data)
      : data instanceof ArrayBuffer
        ? new Uint8Array(data)
        : data instanceof Uint8Array
          ? data
          : new TextEncoder().encode(String(data));

  function browserFallback() {
    const blob = new Blob([bytes], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    logToNative("EXPORT_BROWSER", filename);
  }

  function tryLocalBroker() {
    return fetch("/api/write_production_file", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Studio-Capability": window.__STUDIO_CAPABILITY__ || "" },
      body: JSON.stringify({
        filename: filename,
        subdirectory: subdirectory || "exports",
        data_bytes: Array.from(bytes)
      })
    }).then(function (res) {
      return res.json().then(function (j) {
        if (!res.ok || j.status !== "SUCCESS") throw new Error(j.error || res.statusText);
        setStatus("Saved: " + j.saved_at, "ok");
        logToNative("LOCAL_BROKER", j.saved_at);
        if (j.sha256 && typeof setLastExportDigest === "function") setLastExportDigest(j.sha256);
        if (typeof persistChatSession === "function") persistChatSession();
        return j;
      });
    });
  }

  function tryTauri() {
    const args = {
      filename: filename,
      dataBytes: Array.from(bytes),
      subdirectory: subdirectory || "exports"
    };
    if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke) {
      return window.__TAURI__.core.invoke("native_write_production_file", args);
    }
    if (window.__TAURI__ && window.__TAURI__.tauri && window.__TAURI__.tauri.invoke) {
      return window.__TAURI__.tauri.invoke("native_write_production_file", args);
    }
    return Promise.reject(new Error("no tauri"));
  }

  // Order: Tauri → local studio_server broker → browser download
  tryTauri()
    .then(function (path) {
      setStatus("Saved natively: " + path, "ok");
      logToNative("IPC_SUCCESS", path);
    })
    .catch(function () {
      tryLocalBroker().catch(function () {
        browserFallback();
      });
    });
}

/**
 * Frame-quantized armature timeline (30 fps) — OTIO-inspired schema, not full OTIO XML.
 * Sample-indexed viseme + neck yaw + eye rotation tracks from live skeleton / cinema state.
 */
function exportCinematicAnimationTimeline() {
  if (!skeleton) compile();
  logToNative("EXPORT_ANIMATION", "Compiling cinematic armature timeline");

  const fps = 30;
  const sampleRate = 44100;
  const bpm = skeleton.timebase.initial_bpm || 102;
  const totalSec = ticksToSec(totalTicks()) || 8;
  const totalFrames = Math.max(1, Math.floor(totalSec * fps));
  const vocal = skeleton.tracks.find(function (t) { return t.type === "VOCAL"; });

  function visemeAtTick(tick) {
    if (!vocal) return "REST";
    let best = null;
    for (let i = 0; i < vocal.events.length; i++) {
      const e = vocal.events[i];
      if (e.type !== "NOTE_ON") continue;
      if (e.tick <= tick && (!best || e.tick >= best.tick)) best = e;
    }
    if (!best) return "REST";
    const v = (best.viseme || best.phoneme || "A").toUpperCase();
    const alias = { AH: "A", EE: "E", EH: "E", OH: "O", OO: "U" };
    return alias[v] || (["A", "E", "O", "U"].indexOf(v) >= 0 ? v : "A");
  }

  function sectionAtTick(tick) {
    const secs = skeleton.structure.sections || [];
    for (let i = 0; i < secs.length; i++) {
      const s = secs[i];
      if (tick >= s.start_tick && tick < s.end_tick) return s;
    }
    return null;
  }

  const cinema = window.pulseForgeCinemaSync;
  const neckYaw0 =
    cinema && cinema.neckBone ? cinema.neckBone.rotation.y : 0;
  const eyeYaw0 =
    cinema && cinema.leftEye ? cinema.leftEye.rotation.y : 0;

  const tracks = {
    vocal_visemes: [],
    neck_rotation_yaw: [],
    eyes_rotation_yaw: []
  };

  for (let frame = 0; frame < totalFrames; frame++) {
    const tSec = frame / fps;
    const sample = Math.floor(tSec * sampleRate);
    const tick = Math.round((tSec * bpm / 60) * TPQ);
    const sec = sectionAtTick(tick);
    let viseme = "REST";
    if (sec && sec.role !== "none") viseme = visemeAtTick(tick);

    // Optional gentle modulation of neck from look-at if available
    let neck = neckYaw0;
    let eye = eyeYaw0;
    if (cinema && cinema.lookAt) {
      const dx = cinema.lookAt.x || 0;
      const dz = cinema.lookAt.z || 4;
      neck = Math.max(-0.785, Math.min(0.785, Math.atan2(dx, dz) * 0.45));
      eye = Math.max(-0.4, Math.min(0.4, (Math.atan2(dx, dz) - neck) * 0.5));
    }

    tracks.vocal_visemes.push({ frame: frame, sample: sample, tick: tick, value: viseme });
    tracks.neck_rotation_yaw.push({
      frame: frame,
      sample: sample,
      value: parseFloat(neck.toFixed(5))
    });
    tracks.eyes_rotation_yaw.push({
      frame: frame,
      sample: sample,
      value: parseFloat(eye.toFixed(5))
    });
  }

  const timeline = {
    $schema: "pulseforge.cinematic_armature_timeline.v2",
    format: "pulseforge.cinematic_armature_timeline.v2",
    song_id: skeleton.song_id,
    title: skeleton.title || "Song",
    metadata: {
      fps: fps,
      sample_rate: sampleRate,
      total_frames: totalFrames,
      total_samples: Math.floor(totalSec * sampleRate),
      bpm: bpm,
      key: skeleton.timebase.key,
      note: "Frame-quantized guide tracks — not full OpenTimelineIO XML",
      generated_at: new Date().toISOString()
    },
    tracks: tracks
  };

  const filename = (skeleton.song_id || "song") + "_3D_AnimationTimeline.json";
  const json = JSON.stringify(timeline, null, 2);
  savePayload(filename, json, "animation_timelines", "application/json");
  setStatus("3D animation timeline exported · " + totalFrames + " frames @ " + fps + "fps", "ok");
  logToNative("EXPORT_COMPLETE", filename);
}

const btnAnim = $("btnAnim");
if (btnAnim) btnAnim.onclick = exportCinematicAnimationTimeline;


/**
 * OTIO-inspired timeline package (JSON).
 * Not a full OpenTimelineIO Python/C++ schema dump — labeled honestly for NLE import experiments.
 */
function exportOTIOPackage() {
  if (!skeleton) compile();
  logToNative("EXPORT_OTIO", "Compiling OTIO-inspired Timeline.1 package");

  const fps = 30;
  const bpm = skeleton.timebase.initial_bpm || 102;
  const tpq = typeof TPQ !== "undefined" ? TPQ : 960;
  const ledger = typeof getTelemetryLedger === "function" ? getTelemetryLedger() : [];
  const onsets = ledger.filter(function (r) { return r.is_rhythmic_onset; });

  function RT(frames) {
    return { OTIO_SCHEMA: "RationalTime.1", rate: fps, value: Math.max(0, Math.round(frames)) };
  }
  function TR(startF, durF) {
    return { OTIO_SCHEMA: "TimeRange.1", start_time: RT(startF), duration: RT(durF) };
  }

  const trackChildren = [];
  let tickOff = 0;
  (skeleton.structure.sections || []).forEach(function (sec) {
    const secTicks = (sec.bars || 1) * 4 * tpq;
    const startSec = (tickOff / tpq) * (60 / bpm);
    const durSec = (secTicks / tpq) * (60 / bpm);
    const startF = Math.floor(startSec * fps);
    const durF = Math.max(1, Math.floor(durSec * fps));
    const endSec = startSec + durSec;

    const localized = onsets.filter(function (o) {
      const t = o.time_sec != null ? o.time_sec : (o.sample_index / 44100);
      return t >= startSec && t < endSec;
    }).map(function (o) {
      const t = o.time_sec != null ? o.time_sec : (o.sample_index / 44100);
      return {
        OTIO_SCHEMA: "Marker.1",
        name: "Transient_Onset_" + (o.sample_index || 0),
        marked_range: TR(Math.floor(t * fps), 1),
        metadata: { spectral_flux: o.spectral_flux, tick_clock: o.tick_clock }
      };
    });

    // Viseme markers from vocal events in section tick range
    const vocal = skeleton.tracks.find(function (t) { return t.type === "VOCAL"; });
    if (vocal && sec.role !== "none") {
      vocal.events.forEach(function (ev) {
        if (ev.type !== "NOTE_ON") return;
        if (ev.tick < tickOff || ev.tick >= tickOff + secTicks) return;
        const t = ticksToSec(ev.tick);
        localized.push({
          OTIO_SCHEMA: "Marker.1",
          name: "viseme_" + (ev.viseme || ev.phoneme || "A"),
          marked_range: TR(Math.floor(t * fps), Math.max(1, Math.floor(ticksToSec(ev.duration_ticks || tpq / 2) * fps))),
          metadata: { phoneme: ev.phoneme, note: ev.note_number }
        });
      });
    }

    if (sec.role === "none") {
      trackChildren.push({
        OTIO_SCHEMA: "Gap.1",
        name: "Instrumental_Gap_" + sec.name,
        metadata: { section_type: sec.type || sec.role, bars: sec.bars },
        source_range: TR(0, durF),
        markers: localized
      });
    } else {
      trackChildren.push({
        OTIO_SCHEMA: "Clip.1",
        name: "Vocal_Performance_" + sec.name,
        metadata: {
          vocal_role_contract: sec.role,
          raw_lyrics_text: sec.lyrics || "",
          viseme_layout_pattern: ["A", "E", "O", "U"],
          bars: sec.bars
        },
        source_range: TR(0, durF),
        markers: localized
      });
    }
    tickOff += secTicks;
  });

  const videoTrack = {
    OTIO_SCHEMA: "Track.1",
    name: "Vocal_Viseme_Track_Channel",
    kind: "Video",
    children: trackChildren,
    markers: []
  };

  const otioTimeline = {
    OTIO_SCHEMA: "Timeline.1",
    name: ((typeof $ === "function" && $("title") && $("title").value) || skeleton.title || "SARA_TRACK") + " Studio Master Timeline",
    metadata: {
      pulseforge_song_id: skeleton.song_id,
      project_title: (typeof $ === "function" && $("title") && $("title").value) || skeleton.title || "SARA_TRACK",
      generated_timestamp: new Date().toISOString(),
      pulseforge: {
        schema_note: "OTIO-inspired JSON (Timeline.1 / Track.1 / Clip.1 / Gap.1 / Marker.1)",
        bpm: bpm,
        key: skeleton.timebase.key,
        onset_count: onsets.length,
        extracted_transient_onset_count: onsets.length,
        timebase_bpm: bpm,
        timebase_key_scale: skeleton.timebase.key
      }
    },
    tracks: {
      OTIO_SCHEMA: "Stack.1",
      name: "Tracks Stack",
      metadata: {
        timebase_bpm: bpm,
        extracted_transient_onset_count: onsets.length
      },
      children: [videoTrack]
    }
  };

  const filename = (skeleton.song_id || "song") + "_Interchange.otio.json";
  savePayload(filename, JSON.stringify(otioTimeline, null, 2), "otio_packages", "application/json");
  setStatus("OTIO package · " + trackChildren.length + " clips/gaps · " + onsets.length + " onsets", "ok");
  logToNative("EXPORT_COMPLETE", filename);
}


const btnOTIO = $("btnOTIO");
if (btnOTIO) btnOTIO.onclick = exportOTIOPackage;

(function wireShelves() {
  function apply() {
    const lo = $("shelfLow");
    const hi = $("shelfHigh");
    if (typeof setShelfParams === "function" && lo && hi) {
      setShelfParams(parseFloat(lo.value), parseFloat(hi.value));
    }
  }
  const lo = $("shelfLow");
  const hi = $("shelfHigh");
  if (lo) lo.oninput = apply;
  if (hi) hi.oninput = apply;
})();


async function triggerNeuralCompilationPipeline() {
  setStatus("Dispatching hybrid broadcast master…", "warn");
  logToNative("NEURAL_BROKER", "Packaging lyrics + prompt for hybrid proxy");

  const sections = (skeleton && skeleton.structure && skeleton.structure.sections) || [];
  const fullLyrics = sections.map(function (s) {
    return "[" + (s.name || "").toUpperCase() + " - " + String(s.role || "none").toUpperCase() + "]\n" + (s.lyrics || "");
  }).join("\n\n");

  const submission = {
    title: ($("title") && $("title").value) || (skeleton && skeleton.title) || "SARA_RELEASE_TRACK",
    prompt_directive: ($("prompt") && $("prompt").value) || "",
    lyrics: fullLyrics,
    configuration: {
      target_bpm: (skeleton && skeleton.timebase && skeleton.timebase.initial_bpm) || parseInt(($("bpmOverride") && $("bpmOverride").value) || "102", 10),
      target_scale: (skeleton && skeleton.timebase && skeleton.timebase.key) || (($("keyOverride") && $("keyOverride").value) || "F# minor"),
      audio_profile: "broadcast_studio_youtube_master"
    }
  };

  try {
    const res = await fetch("/api/dispatch_neural_compilation", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Studio-Capability": window.__STUDIO_CAPABILITY__ || "" },
      body: JSON.stringify(submission)
    });
    const data = await res.json();
    if (!res.ok || data.status !== "SUCCESS") {
      throw new Error(data.error || res.statusText);
    }
    setStatus("Broadcast master written · " + data.provider, "ok");
    logToNative("BROKER_SUCCESS", data.saved_master_path);
    alert("Hybrid master ready\nWAV: " + data.saved_master_path + "\nOTIO: " + data.saved_otio_path);
  } catch (err) {
    console.warn("[Broker]", err);
    setStatus("Hybrid broker offline — use local Play / WAV export", "warn");
    logToNative("BROKER_FALLBACK", String(err));
  }
}

const btnNeural = $("btnNeural");
if (btnNeural) btnNeural.onclick = function () { triggerNeuralCompilationPipeline(); };


async function runVocalLab() {
  if (!skeleton) compile();
  const vocal = skeleton.tracks.find(function (t) { return t.type === "VOCAL"; });
  const events = vocal ? vocal.events : [];
  const lyrics = (skeleton.structure.sections || []).map(function (s) { return s.lyrics || ""; }).join(" ");
  const roleSec = (skeleton.structure.sections || []).find(function (s) { return s.role && s.role !== "none"; });
  const roleProfile = roleSec ? (roleSec.role === "both" ? "male" : roleSec.role) : "male";
  const qEl = $("vocalQuality");
  const quality = (qEl && qEl.value) || "production";
  setStatus("Vocal lab · " + quality + "…", "warn");
  const receipt = await renderLocalNeuralVocalPhrase(
    events,
    lyrics || "la la late night streetlight",
    roleProfile,
    quality
  );
  if (receipt) {
    setStatus("Vocal · " + (receipt.engine || quality) + " · " + (receipt.asset_hash || "").slice(0, 10), "ok");
    alert(
      "Vocal Lab\n" +
      (receipt.engine || "") + "\n" +
      (receipt.saved_master_path || "") + "\n" +
      (receipt.ceiling_note || "")
    );
  }
}
const btnVocalLab = $("btnVocalLab");
if (btnVocalLab) btnVocalLab.onclick = function () { runVocalLab(); };

const btnVocalLab2 = $("btnVocalLab2");
if (btnVocalLab2) btnVocalLab2.onclick = function () { runVocalLab(); };

// Project address survives independently of browser cache; enter it on any fresh client.
if ($('btnOpenProject')) $('btnOpenProject').onclick = () => restoreProjectFromStorage().catch(e => setStatus('Open failed: ' + e.message, 'warn'));
if ($('btnNewProject')) $('btnNewProject').onclick = () => {
  durableProjectRef = null; durableSourceAssets = [];
  if ($('projectId')) $('projectId').value = '';
  if ($('projectRevision')) $('projectRevision').textContent = 'Unsaved draft — no durable project yet';
  setStatus('New project draft · Save to create a durable project', 'warn');
};
