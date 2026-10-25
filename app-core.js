const TPQ = 960;
const SCALES = {
  "F# minor": { root: 42, scale: [0, 2, 3, 5, 7, 8, 10], lead: [66, 69, 71, 73], pluck: [54, 57, 61, 64], vocal: [54, 57, 59, 61] },
  "A minor":  { root: 45, scale: [0, 2, 3, 5, 7, 8, 10], lead: [69, 72, 74, 76], pluck: [57, 60, 64, 67], vocal: [57, 60, 62, 64] },
  "C minor":  { root: 36, scale: [0, 2, 3, 5, 7, 8, 10], lead: [60, 63, 65, 67], pluck: [48, 51, 55, 58], vocal: [48, 51, 53, 55] },
  "D minor":  { root: 38, scale: [0, 2, 3, 5, 7, 8, 10], lead: [62, 65, 67, 69], pluck: [50, 53, 57, 60], vocal: [50, 53, 55, 57] },
  "E minor":  { root: 40, scale: [0, 2, 3, 5, 7, 8, 10], lead: [64, 67, 69, 71], pluck: [52, 55, 59, 62], vocal: [52, 55, 57, 59] },
  "G major":  { root: 43, scale: [0, 2, 4, 5, 7, 9, 11], lead: [67, 71, 74, 76], pluck: [55, 59, 62, 67], vocal: [55, 59, 62, 64] }
};

/* Simple lyric → syllable/phoneme tokens (deterministic, offline) */
function lyricsToPhonemes(text) {
  const words = (text || "").toLowerCase().replace(/[^a-z\s']/g, " ").split(/\s+/).filter(Boolean);
  const out = [];
  const vowelMap = {
    a: "ah", e: "eh", i: "ee", o: "oh", u: "oo",
    ay: "ee", ey: "ee", ow: "oh", ou: "oo", ea: "ee", oo: "oo",
    ai: "ee", ie: "ee", oa: "oh"
  };
  words.forEach((w) => {
    // rough syllable chunks: split on vowel groups
    const parts = w.match(/[^aeiouy]*[aeiouy]+[^aeiouy]*/gi) || [w];
    parts.forEach((part) => {
      let ph = "ah";
      if (/ee|ea|i|y|ay|ey/.test(part)) ph = "ee";
      else if (/oo|u|ou/.test(part)) ph = "oo";
      else if (/o|oa|ow/.test(part)) ph = "oh";
      else if (/e|eh/.test(part)) ph = "eh";
      else if (/a|ah/.test(part)) ph = "ah";
      out.push({ word: w, phoneme: ph, syllable: part });
    });
  });
  return out.length ? out : [{ word: "ah", phoneme: "ah", syllable: "ah" }];
}


/** Deterministic mulberry32 PRNG for reproducible generation variation */
function mulberry32(a) {
  return function() {
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function hashSeed(str) {
  let h = 2166136261 >>> 0;
  const s = String(str || "");
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function parsePrompt(text, opts) {
  opts = opts || {};
  const p = (text || "").toLowerCase();
  const seedVal = (opts.seed != null ? opts.seed : hashSeed(p + "|" + (opts.nonce || "0"))) >>> 0;
  const rnd = mulberry32(seedVal);
  let bpm = 102;
  const m = p.match(/(\d{2,3})\s*bpm/);
  if (m) bpm = Math.max(60, Math.min(180, parseInt(m[1], 10)));

  let key = "F# minor";
  for (const k of Object.keys(SCALES)) {
    if (p.includes(k.toLowerCase())) { key = k; break; }
  }
  if (p.includes("c minor")) key = "C minor";
  if (p.includes("a minor")) key = "A minor";
  if (p.includes("d minor")) key = "D minor";

  let genre = "alt-hip-hop";
  if (p.includes("house") || p.includes("club")) genre = "house";
  else if (p.includes("blues")) genre = "electro-blues";
  else if (p.includes("trap")) genre = "trap";
  else if (p.includes("lo-fi") || p.includes("lofi")) genre = "lo-fi";

  const dark = /dark|smoky|noir|sparse|minimal/.test(p);
  const wantPluck = /guitar|pluck|string|acoustic|blues/.test(p);

  const form = [
    { name: "Intro", type: "intro", bars: 2, role: "none",
      lyrics: "" },
    { name: "Verse", type: "verse", bars: 4, role: "male",
      lyrics: "late night same streetlight i keep telling myself im fine" },
    { name: "Chorus", type: "chorus", bars: 4, role: "both",
      lyrics: "its a bad habit but i cant break it" },
    { name: "Verse", type: "verse", bars: 4, role: "male",
      lyrics: "same song different room same old tune" },
    { name: "Chorus", type: "chorus", bars: 4, role: "female",
      lyrics: "its a bad habit but i cant break it" },
    { name: "Outro", type: "outro", bars: 2, role: "none",
      lyrics: "" }
  ];
  if (p.includes("bridge")) {
    form.splice(4, 0, { name: "Bridge", type: "bridge", bars: 2, role: "female",
      lyrics: "if i said stay would you mean it" });
  }

  let tick = 0;
  const sections = form.map(s => {
    const start = tick;
    tick += s.bars * 4 * TPQ;
    return {
      id: "sec-" + start, name: s.name, type: s.type,
      start_tick: start, end_tick: tick, role: s.role,
      lyrics: s.lyrics
    };
  });

  const sc = SCALES[key] || SCALES["F# minor"];
  const drums = { track_id: "drums", name: "Drums", type: "DRUMS", volume_db: dark ? -3 : -1, pan: 0, muted: false, events: [] };
  const bass  = { track_id: "bass",  name: "Bass",  type: "BASS",  volume_db: -2, pan: 0, muted: false, events: [] };
  const pad   = { track_id: "pad",   name: "Pad",   type: "PAD",   volume_db: -10, pan: -0.2, muted: false, events: [] };
  const lead  = { track_id: "lead",  name: "Lead",  type: "LEAD",  volume_db: -6, pan: 0.15, muted: false, events: [] };
  const pluck = { track_id: "pluck", name: "Pluck", type: "STRINGS", volume_db: -4, pan: 0.25, muted: false, events: [] };
  const vocal = { track_id: "vocal", name: "Vocal", type: "VOCAL", volume_db: -3, pan: -0.05, muted: false, events: [] };

  const totalTicks = tick, barTicks = 4 * TPQ, eighth = TPQ / 2;

  for (let bar = 0; bar * barTicks < totalTicks; bar++) {
    const base = bar * barTicks;
    drums.events.push({ type: "NOTE_ON", tick: base, note_number: 36, velocity: 115, duration_ticks: 200 });
    if (!dark || bar % 2 === 0) {
      drums.events.push({ type: "NOTE_ON", tick: base + 2 * TPQ, note_number: 38, velocity: 100, duration_ticks: 180 });
    }
    for (let e = 0; e < 8; e++) {
      if (dark && e % 2 === 1) continue;
      drums.events.push({ type: "NOTE_ON", tick: base + e * eighth, note_number: 42, velocity: e % 2 === 0 ? 70 : 45, duration_ticks: 80 });
    }
  }

  const progression = [0, 0, 5, 3, 0, 7, 5, 0];
  for (let bar = 0; bar * barTicks < totalTicks; bar++) {
    const deg = progression[bar % progression.length];
    const note = sc.root + sc.scale[deg % sc.scale.length];
    const base = bar * barTicks;
    const dens = dark ? 2 : 4;
    for (let i = 0; i < dens; i++) {
      bass.events.push({
        type: "NOTE_ON", tick: base + i * (barTicks / dens),
        note_number: note, velocity: 105,
        duration_ticks: Math.floor(barTicks / dens) - 40
      });
    }
  }

  sections.forEach(sec => {
    if (sec.type === "intro" || sec.type === "outro") return;
    const deg = sec.type === "chorus" ? 0 : 5;
    pad.events.push({
      type: "NOTE_ON", tick: sec.start_tick,
      note_number: sc.root + 12 + sc.scale[deg % sc.scale.length],
      velocity: 70, duration_ticks: sec.end_tick - sec.start_tick - 100
    });
  });

  sections.filter(s => s.type === "chorus" || s.type === "bridge").forEach(sec => {
    for (let i = 0; i < 4; i++) {
      lead.events.push({
        type: "NOTE_ON", tick: sec.start_tick + i * TPQ,
        note_number: sc.lead[i % sc.lead.length],
        velocity: 95, duration_ticks: TPQ - 80
      });
    }
  });

  sections.filter(s => s.type === "verse" || s.type === "chorus" || wantPluck).forEach(sec => {
    for (let i = 0; i < 4; i++) {
      pluck.events.push({
        type: "NOTE_ON",
        tick: sec.start_tick + i * TPQ + (wantPluck ? 0 : TPQ / 2),
        note_number: sc.pluck[i % sc.pluck.length],
        velocity: wantPluck ? 100 : 75,
        duration_ticks: 480
      });
    }
  });

  // Note-conditioned vocal alignment: distribute phonemes across section ticks
  sections.forEach(sec => {
    if (sec.role === "none" || !sec.lyrics) return;
    const phones = lyricsToPhonemes(sec.lyrics);
    const span = sec.end_tick - sec.start_tick;
    const step = Math.max(TPQ / 2, Math.floor(span / Math.max(1, phones.length)));
    phones.forEach((ph, i) => {
      const t = sec.start_tick + i * step;
      if (t >= sec.end_tick) return;
      const note = sc.vocal[i % sc.vocal.length] + (sec.role === "female" ? 5 : 0);
      vocal.events.push({
        type: "NOTE_ON",
        tick: t,
        note_number: note,
        velocity: 100,
        duration_ticks: Math.min(step - 40, TPQ),
        phoneme: ph.phoneme,
        word: ph.word,
        role: sec.role === "both" ? (i % 2 === 0 ? "male" : "female") : sec.role
      });
    });
  });

  return {
    $schema: "pulseforge.songforge.skeleton.v2.8",
    song_id: "sf-" + seedVal.toString(36) + "-" + Date.now().toString(36),
    generation_seed: seedVal,
    title: "Generated",
    engine: "phase4-spatial-bbd",
    timebase: {
      ticks_per_quarter_note: TPQ,
      initial_bpm: bpm,
      sample_rate: 44100,
      key, genre, meter: "4/4"
    },
    structure: { sections },
    tracks: [drums, bass, pad, lead, pluck, vocal],
    prompt: text,
    created_at: new Date().toISOString()
  };
}

/** Rebuild vocal events from current section lyrics (after user edits) */
function rebuildVocalsFromLyrics() {
  if (!skeleton) return;
  const sc = SCALES[skeleton.timebase.key] || SCALES["F# minor"];
  const vocal = skeleton.tracks.find(t => t.type === "VOCAL");
  if (!vocal) return;
  vocal.events = [];
  skeleton.structure.sections.forEach(sec => {
    if (sec.role === "none" || !sec.lyrics) return;
    const phones = lyricsToPhonemes(sec.lyrics);
    const span = sec.end_tick - sec.start_tick;
    const step = Math.max(TPQ / 2, Math.floor(span / Math.max(1, phones.length)));
    phones.forEach((ph, i) => {
      const t = sec.start_tick + i * step;
      if (t >= sec.end_tick) return;
      const note = sc.vocal[i % sc.vocal.length] + (sec.role === "female" ? 5 : 0);
      vocal.events.push({
        type: "NOTE_ON", tick: t, note_number: note, velocity: 100,
        duration_ticks: Math.min(step - 40, TPQ),
        phoneme: ph.phoneme, word: ph.word,
        role: sec.role === "both" ? (i % 2 === 0 ? "male" : "female") : sec.role
      });
    });
  });
}

let skeleton = null, audioCtx = null, masterBus = null, playing = false, nodes = [];
const $ = id => document.getElementById(id);
function setStatus(msg, kind) {
  const el = $("status");
  if (el) { el.textContent = msg; el.className = "status " + (kind || "ok"); }
}
function midiToFreq(n) { return 440 * Math.pow(2, (n - 69) / 12); }
function ticksToSec(ticks) { return (ticks / TPQ) * (60 / skeleton.timebase.initial_bpm); }
function totalTicks() {
  return skeleton.structure.sections.reduce((m, s) => Math.max(m, s.end_tick), 0);
}


function makeSaturationCurve(amount) {
  const k = amount || 35;
  const n = 4096;
  const curve = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const x = (i * 2) / n - 1;
    // Asymmetrical soft-clip (tape-style)
    curve[i] = ((3 + k) * x * Math.PI / 9) / (Math.PI + k * Math.abs(x));
  }
  return curve;
}

/** Stereo BBD-style delay: L/R offset, feedback, cross-feed, HF damping */
function createSpatialBBD(ctx, destNode) {
  const delayL = ctx.createDelay(2.0);
  const delayR = ctx.createDelay(2.0);
  const fbL = ctx.createGain();
  const fbR = ctx.createGain();
  const xL = ctx.createGain();
  const xR = ctx.createGain();
  const dampL = ctx.createBiquadFilter();
  const dampR = ctx.createBiquadFilter();
  const wet = ctx.createGain();
  const splitter = ctx.createChannelSplitter(2);
  const merger = ctx.createChannelMerger(2);
  const input = ctx.createGain();

  dampL.type = "lowpass";
  dampR.type = "lowpass";
  dampL.frequency.value = 1800;
  dampR.frequency.value = 1800;
  dampL.Q.value = 0.7;
  dampR.Q.value = 0.7;

  // Multi-tap BBD: 28ms L / 42ms R early reflections + cross-feedback
  delayL.delayTime.value = 0.028;
  delayR.delayTime.value = 0.042;
  fbL.gain.value = 0.38;
  fbR.gain.value = 0.38;
  xL.gain.value = 0.22;
  xR.gain.value = 0.22;
  wet.gain.value = 0.42;

  input.connect(splitter);
  splitter.connect(delayL, 0);
  splitter.connect(delayR, 1);

  delayL.connect(dampL);
  delayR.connect(dampR);

  dampL.connect(fbL);
  fbL.connect(delayL);
  dampR.connect(fbR);
  fbR.connect(delayR);

  // Cross-feed
  dampL.connect(xL);
  xL.connect(delayR);
  dampR.connect(xR);
  xR.connect(delayL);

  dampL.connect(merger, 0, 0);
  dampR.connect(merger, 0, 1);
  merger.connect(wet);
  wet.connect(destNode);

  return {
    input,
    wet,
    setParams(delaySec, feedback, cross, dampHz, wetAmt) {
      const t = ctx.currentTime;
      // delaySec = L early; R = L * 1.5 (e.g. 28ms → 42ms) for constant-power widen
      const dL = delaySec;
      const dR = delaySec * 1.5;
      delayL.delayTime.setValueAtTime(dL, t);
      delayR.delayTime.setValueAtTime(dR, t);
      fbL.gain.setValueAtTime(feedback, t);
      fbR.gain.setValueAtTime(feedback, t);
      xL.gain.setValueAtTime(cross, t);
      xR.gain.setValueAtTime(cross, t);
      dampL.frequency.setValueAtTime(dampHz, t);
      dampR.frequency.setValueAtTime(dampHz, t);
      wet.gain.setValueAtTime(wetAmt, t);
    }
  };
}

let spatialBBD = null;

let lowShelf = null;
let masterLimiter = null;
let highShelf = null;
let mixAnalyser = null;
let fluxRaf = null;
let fluxPrev = null;
let fluxHistory = [];
let telemetryLedger = [];
let fluxSampleClock = 0;

function createShelvingFilter(ctx, type, cutoffHz, gainDb) {
  const f = ctx.createBiquadFilter();
  f.type = type === "low" ? "lowshelf" : "highshelf";
  f.frequency.value = cutoffHz;
  f.gain.value = gainDb;
  return f;
}

function setShelfParams(lowGainDb, highGainDb) {
  if (lowShelf) lowShelf.gain.value = lowGainDb;
  if (highShelf) highShelf.gain.value = highGainDb;
}

function ensureAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    masterBus = audioCtx.createGain();
    masterBus.gain.value = 0.70;
    // Look-ahead-ish brickwall: DynamicsCompressor hard knee on master
    masterLimiter = audioCtx.createDynamicsCompressor();
    masterLimiter.threshold.value = -1.0;
    masterLimiter.knee.value = 0;
    masterLimiter.ratio.value = 20;
    masterLimiter.attack.value = 0.003;
    masterLimiter.release.value = 0.08;

    // Phase 5: master low/high shelves (isolate sub vs presence)
    lowShelf = createShelvingFilter(audioCtx, "low", 120, 2.0);
    highShelf = createShelvingFilter(audioCtx, "high", 4500, 1.5);

    // Phase 4: asymmetric tape shaper
    const sat = audioCtx.createWaveShaper();
    sat.curve = makeSaturationCurve(35);
    try { sat.oversample = "4x"; } catch (e) { sat.oversample = "2x"; }

    masterBus.connect(lowShelf);
    lowShelf.connect(highShelf);
    highShelf.connect(sat);
    if (!masterLimiter) {
      masterLimiter = audioCtx.createDynamicsCompressor();
      masterLimiter.threshold.value = -1.0;
      masterLimiter.knee.value = 0;
      masterLimiter.ratio.value = 20;
      masterLimiter.attack.value = 0.003;
      masterLimiter.release.value = 0.08;
    }
    sat.connect(masterLimiter);
    masterLimiter.connect(audioCtx.destination);

    // Analyser tap (no ScriptProcessor) for spectral flux
    mixAnalyser = audioCtx.createAnalyser();
    mixAnalyser.fftSize = 512;
    mixAnalyser.smoothingTimeConstant = 0.2;
    masterBus.connect(mixAnalyser);

    spatialBBD = createSpatialBBD(audioCtx, masterBus);
    spatialBBD.setParams(0.028, 0.38, 0.22, 2400, 0.42); // multi-tap BBD widen
  }
  if (audioCtx.state === "suspended") audioCtx.resume();
  return audioCtx;
}

/** Half-wave rectified spectral flux onset detector (AnalyserNode magnitudes) */
function startFluxAnalysis() {
  stopFluxAnalysis();
  if (!mixAnalyser) return;
  const bins = mixAnalyser.frequencyBinCount;
  fluxPrev = new Float32Array(bins);
  const curr = new Float32Array(bins);
  fluxHistory = [];
  telemetryLedger = [];
  fluxSampleClock = 0;
  const hop = mixAnalyser.fftSize;

  const tick = () => {
    if (!playing || !mixAnalyser) return;
    mixAnalyser.getFloatFrequencyData(curr);
    // convert dB to relative linear-ish energy
    let flux = 0;
    for (let i = 0; i < bins; i++) {
      const lin = Math.pow(10, curr[i] / 20);
      const prev = fluxPrev[i] || 0;
      const d = lin - prev;
      if (d > 0) flux += d;
      fluxPrev[i] = lin;
    }
    fluxHistory.push(flux);
    if (fluxHistory.length > 40) fluxHistory.shift();
    let avg = 0;
    for (let i = 0; i < fluxHistory.length; i++) avg += fluxHistory[i];
    avg = fluxHistory.length ? avg / fluxHistory.length : 0;
    const thr = avg * 1.55 + 0.015;
    const onset = flux > thr && flux > 0.03;

    const bpm = (skeleton && skeleton.timebase && skeleton.timebase.initial_bpm) || 102;
    const tSec = fluxSampleClock / (audioCtx.sampleRate || 44100);
    const tickClock = Math.round((tSec * bpm / 60) * (typeof TPQ !== "undefined" ? TPQ : 960));

    const rec = {
      sample_index: fluxSampleClock,
      time_sec: +tSec.toFixed(4),
      tick_clock: tickClock,
      spectral_flux: +flux.toFixed(5),
      is_rhythmic_onset: onset
    };
    telemetryLedger.push(rec);
    if (telemetryLedger.length > 800) telemetryLedger.shift();

    if (onset && window.pulseForgeCinemaSync) {
      const vs = ["A", "E", "O", "U"];
      const v = vs[Math.floor(flux * 12) % vs.length];
      window.pulseForgeCinemaSync.solveVisemeMechanics(v);
      if (typeof window.pulseForgeCinemaSync.registerTransientLookAtNudge === "function") {
        window.pulseForgeCinemaSync.registerTransientLookAtNudge(flux);
      }
    }
    const fluxEl = document.getElementById("fluxReadout");
    if (fluxEl) fluxEl.textContent = onset ? ("ONSET " + flux.toFixed(3)) : flux.toFixed(3);

    fluxSampleClock += hop;
    fluxRaf = requestAnimationFrame(tick);
  };
  fluxRaf = requestAnimationFrame(tick);
}

function stopFluxAnalysis() {
  if (fluxRaf) {
    cancelAnimationFrame(fluxRaf);
    fluxRaf = null;
  }
}

function getTelemetryLedger() {
  return telemetryLedger.slice();
}

/**
 * Track destination: dry to master; optional wet send to BBD for space tracks
 * spatial: true for STRINGS / LEAD / VOCAL / PAD
 */
function trackDest(ctx, gScale, pan, spatial) {
  const gain = ctx.createGain();
  gain.gain.value = gScale;
  let node = gain;
  if (ctx.createStereoPanner) {
    const p = ctx.createStereoPanner();
    p.pan.value = Math.max(-1, Math.min(1, pan || 0));
    gain.connect(p);
    node = p;
  }
  node.connect(masterBus || ctx.destination);
  if (spatial && spatialBBD) {
    // Parallel send (keeps dry, adds widened wet)
    try { node.connect(spatialBBD.input); } catch (e) {}
  }
  return gain;
}

function playKick(ctx, t, g, dest) {
  const o = ctx.createOscillator(), gn = ctx.createGain();
  o.type = "sine";
  o.frequency.setValueAtTime(150, t);
  o.frequency.exponentialRampToValueAtTime(40, t + 0.12);
  gn.gain.setValueAtTime(0.55 * g, t);
  gn.gain.exponentialRampToValueAtTime(0.001, t + 0.28);
  o.connect(gn); gn.connect(dest);
  o.start(t); o.stop(t + 0.3);
  nodes.push(o);
}

function playSnare(ctx, t, g, dest) {
  const len = Math.floor(ctx.sampleRate * 0.12);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-10 * i / len);
  const src = ctx.createBufferSource(), gn = ctx.createGain(), f = ctx.createBiquadFilter();
  src.buffer = buf; f.type = "bandpass"; f.frequency.value = 2800;
  gn.gain.setValueAtTime(0.35 * g, t);
  gn.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
  src.connect(f); f.connect(gn); gn.connect(dest);
  src.start(t);
  nodes.push(src);
}

function playHat(ctx, t, g, dest) {
  const len = Math.floor(ctx.sampleRate * 0.04);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.exp(-14 * i / len);
  const src = ctx.createBufferSource(), gn = ctx.createGain(), f = ctx.createBiquadFilter();
  src.buffer = buf; f.type = "highpass"; f.frequency.value = 7000;
  gn.gain.value = 0.12 * g;
  src.connect(f); f.connect(gn); gn.connect(dest);
  src.start(t);
  nodes.push(src);
}

function playBass(ctx, note, t, dur, vel, dest) {
  const freq = midiToFreq(note);
  const gAmt = 0.28 * vel;
  const o1 = ctx.createOscillator(), o2 = ctx.createOscillator();
  const f = ctx.createBiquadFilter(), gn = ctx.createGain();
  o1.type = "sawtooth"; o2.type = "sawtooth";
  o1.frequency.setValueAtTime(freq - 1.2, t);
  o2.frequency.setValueAtTime(freq + 1.2, t);
  f.type = "lowpass"; f.Q.value = 4;
  f.frequency.setValueAtTime(220, t);
  f.frequency.exponentialRampToValueAtTime(720, t + 0.06);
  f.frequency.exponentialRampToValueAtTime(160, t + Math.max(0.1, dur));
  gn.gain.setValueAtTime(0, t);
  gn.gain.linearRampToValueAtTime(gAmt, t + 0.012);
  gn.gain.setValueAtTime(gAmt * 0.85, t + dur * 0.7);
  gn.gain.exponentialRampToValueAtTime(0.001, t + Math.max(0.08, dur));
  o1.connect(f); o2.connect(f); f.connect(gn);
  // Channel low shelf: isolate sub thickness before sum
  const bassShelf = ctx.createBiquadFilter();
  bassShelf.type = "lowshelf";
  bassShelf.frequency.value = 120;
  bassShelf.gain.value = 3.5;
  gn.connect(bassShelf); bassShelf.connect(dest);
  o1.start(t); o2.start(t);
  o1.stop(t + dur + 0.06); o2.stop(t + dur + 0.06);
  nodes.push(o1, o2);
}

function playFM(ctx, note, t, dur, vel, isLead, dest) {
  const carFreq = midiToFreq(note);
  const gAmt = (isLead ? 0.16 : 0.11) * vel;
  const carrier = ctx.createOscillator();
  const modulator = ctx.createOscillator();
  const modGain = ctx.createGain();
  const mainGain = ctx.createGain();
  carrier.type = "sine";
  carrier.frequency.setValueAtTime(carFreq, t);
  modulator.type = "sine";
  modulator.frequency.setValueAtTime(carFreq * 2, t);
  const idx = isLead ? 620 : 280;
  modGain.gain.setValueAtTime(idx, t);
  modGain.gain.exponentialRampToValueAtTime(8, t + Math.max(0.05, dur));
  mainGain.gain.setValueAtTime(0, t);
  mainGain.gain.linearRampToValueAtTime(gAmt, t + (isLead ? 0.008 : 0.08));
  mainGain.gain.setValueAtTime(gAmt * 0.7, t + dur * 0.65);
  mainGain.gain.exponentialRampToValueAtTime(0.001, t + Math.max(0.08, dur));
  modulator.connect(modGain);
  modGain.connect(carrier.frequency);
  carrier.connect(mainGain);
  const fmShelf = ctx.createBiquadFilter();
  fmShelf.type = isLead ? "highshelf" : "lowshelf";
  fmShelf.frequency.value = isLead ? 3500 : 200;
  fmShelf.gain.value = isLead ? 2.0 : 1.5;
  mainGain.connect(fmShelf); fmShelf.connect(dest);
  modulator.start(t); carrier.start(t);
  modulator.stop(t + dur + 0.06); carrier.stop(t + dur + 0.06);
  nodes.push(carrier, modulator);
}

function playWaveguide(ctx, note, t, vel, dest) {
  const freq = midiToFreq(note);
  const gAmt = 0.4 * vel;
  const period = Math.max(2, Math.round(ctx.sampleRate / freq));
  const impulse = ctx.createBuffer(1, period, ctx.sampleRate);
  const data = impulse.getChannelData(0);
  for (let i = 0; i < period; i++) data[i] = Math.random() * 2 - 1;
  const src = ctx.createBufferSource();
  src.buffer = impulse;
  const delay = ctx.createDelay(1.0);
  delay.delayTime.setValueAtTime(1 / freq, t);
  const damp = ctx.createBiquadFilter();
  damp.type = "lowpass";
  damp.frequency.setValueAtTime(Math.min(ctx.sampleRate * 0.22, freq * 8), t);
  const fb = ctx.createGain();
  fb.gain.setValueAtTime(0.985, t);
  const out = ctx.createGain();
  out.gain.setValueAtTime(gAmt, t);
  out.gain.exponentialRampToValueAtTime(0.001, t + 1.8);
  src.connect(delay);
  delay.connect(damp);
  damp.connect(fb);
  fb.connect(delay);
  delay.connect(out);
  const wgShelf = ctx.createBiquadFilter();
  wgShelf.type = "highshelf";
  wgShelf.frequency.value = 2500;
  wgShelf.gain.value = 1.5;
  out.connect(wgShelf); wgShelf.connect(dest);
  src.start(t);
  src.stop(t + 1 / freq + 0.002);
  nodes.push(src);
}

/**
 * Formant vocal phoneme — harmonic source + dual bandpass formants + light vibrato
 * Not a neural singer; deterministic local guide vocal.
 */
function playVocalPhoneme(ctx, note, t, dur, vel, role, phoneme, dest) {
  const fund = midiToFreq(note);
  const gAmt = 0.22 * vel;
  const carrier = ctx.createOscillator();
  carrier.type = "sawtooth";
  carrier.frequency.setValueAtTime(fund, t);

  const vib = ctx.createOscillator();
  const vibG = ctx.createGain();
  vib.type = "sine";
  vib.frequency.setValueAtTime(5.2, t);
  vibG.gain.setValueAtTime(2.0, t);
  vib.connect(vibG);
  vibG.connect(carrier.frequency);

  // Formant table (Hz) for simplified English vowels
  let f1 = 700, f2 = 1200;
  if (phoneme === "ee") { f1 = 270; f2 = 2290; }
  else if (phoneme === "oo") { f1 = 300; f2 = 870; }
  else if (phoneme === "oh") { f1 = 450; f2 = 800; }
  else if (phoneme === "eh") { f1 = 530; f2 = 1840; }
  else { f1 = 700; f2 = 1200; } // ah

  if (role === "female") { f1 *= 1.12; f2 *= 1.12; }

  const bp1 = ctx.createBiquadFilter();
  const bp2 = ctx.createBiquadFilter();
  bp1.type = "bandpass"; bp2.type = "bandpass";
  bp1.frequency.setValueAtTime(f1, t);
  bp2.frequency.setValueAtTime(f2, t);
  bp1.Q.setValueAtTime(8, t);
  bp2.Q.setValueAtTime(10, t);

  const gn = ctx.createGain();
  gn.gain.setValueAtTime(0, t);
  gn.gain.linearRampToValueAtTime(gAmt, t + 0.04);
  gn.gain.setValueAtTime(gAmt * 0.85, t + Math.max(0.05, dur - 0.05));
  gn.gain.exponentialRampToValueAtTime(0.001, t + Math.max(0.08, dur));

  carrier.connect(bp1);
  carrier.connect(bp2);
  bp1.connect(gn);
  bp2.connect(gn);
  const vocShelf = ctx.createBiquadFilter();
  vocShelf.type = "highshelf";
  vocShelf.frequency.value = 4000;
  vocShelf.gain.value = 3.0;
  gn.connect(vocShelf); vocShelf.connect(dest);

  vib.start(t);
  carrier.start(t);
  vib.stop(t + dur + 0.05);
  carrier.stop(t + dur + 0.05);
  nodes.push(carrier, vib);
}

function stopAll() {
  nodes.forEach(n => { try { n.stop(); } catch (e) {} });
  nodes = [];
  playing = false;
  stopFluxAnalysis();
  const prog = $("prog");
  if (prog) prog.style.width = "0%";
  const btn = $("btnPlay");
  if (btn) btn.textContent = "Play";
}


/** Bounded section edit ops — mutate only the targeted section; preserve others. */
function findSectionById(id) {
  if (!skeleton || !skeleton.structure) return null;
  return skeleton.structure.sections.find(s => s.id === id) || null;
}

function sectionSnapshot(sec) {
  return JSON.parse(JSON.stringify(sec));
}

function applySectionLyrics(sectionId, lyrics) {
  const sec = findSectionById(sectionId);
  if (!sec) return { ok: false, error: "section_not_found" };
  const before = sectionSnapshot(sec);
  sec.lyrics = String(lyrics || "");
  rebuildVocalsFromLyrics();
  return { ok: true, section_id: sectionId, before, after: sectionSnapshot(sec) };
}

function applySectionRole(sectionId, role) {
  const sec = findSectionById(sectionId);
  if (!sec) return { ok: false, error: "section_not_found" };
  const allowed = ["none", "male", "female", "both"];
  if (allowed.indexOf(role) < 0) return { ok: false, error: "invalid_role" };
  const before = sectionSnapshot(sec);
  sec.role = role;
  rebuildVocalsFromLyrics();
  return { ok: true, section_id: sectionId, before, after: sectionSnapshot(sec) };
}

function muteSectionEvents(sectionId, muted) {
  const sec = findSectionById(sectionId);
  if (!sec) return { ok: false, error: "section_not_found" };
  sec.muted = !!muted;
  // Soft-mute: zero velocity of events in tick range without deleting
  const lo = sec.start_tick, hi = sec.end_tick;
  skeleton.tracks.forEach(tr => {
    (tr.events || []).forEach(ev => {
      if (ev.tick >= lo && ev.tick < hi) {
        if (muted) {
          if (ev._vel_backup == null) ev._vel_backup = ev.velocity;
          ev.velocity = 0;
        } else if (ev._vel_backup != null) {
          ev.velocity = ev._vel_backup;
          delete ev._vel_backup;
        }
      }
    });
  });
  return { ok: true, section_id: sectionId, muted: !!muted };
}

function duplicateSection(sectionId) {
  if (!skeleton) return { ok: false, error: "no_project" };
  const secs = skeleton.structure.sections;
  const idx = secs.findIndex(s => s.id === sectionId);
  if (idx < 0) return { ok: false, error: "section_not_found" };
  const src = secs[idx];
  const span = src.end_tick - src.start_tick;
  const lastEnd = secs.reduce((m, s) => Math.max(m, s.end_tick), 0);
  const copy = JSON.parse(JSON.stringify(src));
  copy.id = "sec-" + lastEnd + "-" + Math.floor(Math.random() * 1e5);
  copy.name = src.name + " (copy)";
  copy.start_tick = lastEnd;
  copy.end_tick = lastEnd + span;
  // Shift-copy note events into new tick range
  const delta = copy.start_tick - src.start_tick;
  skeleton.tracks.forEach(tr => {
    const adds = [];
    (tr.events || []).forEach(ev => {
      if (ev.tick >= src.start_tick && ev.tick < src.end_tick) {
        const nev = JSON.parse(JSON.stringify(ev));
        nev.tick = ev.tick + delta;
        adds.push(nev);
      }
    });
    tr.events = (tr.events || []).concat(adds);
  });
  secs.push(copy);
  if (!skeleton.edit_history) skeleton.edit_history = [];
  skeleton.edit_history.push({ op: "duplicate_section", section_id: sectionId, new_id: copy.id, at: new Date().toISOString() });
  return { ok: true, section_id: copy.id, from: sectionId };
}

function serializeProject() {
  if (!skeleton) return null;
  return JSON.stringify(skeleton, null, 2);
}

function loadProjectObject(obj) {
  if (!obj || !obj.structure || !obj.tracks) {
    return { ok: false, error: "invalid_project_schema" };
  }
  if (!obj.$schema) obj.$schema = "pulseforge.songforge.skeleton.v2.8";
  // Ensure section ids
  (obj.structure.sections || []).forEach((s, i) => {
    if (!s.id) s.id = "sec-" + (s.start_tick != null ? s.start_tick : i);
  });
  skeleton = obj;
  if (typeof window !== "undefined") window.skeleton = skeleton;
  return { ok: true, song_id: skeleton.song_id, sections: skeleton.structure.sections.length };
}

function projectFingerprint(sk) {
  if (!sk) return null;
  const secs = (sk.structure && sk.structure.sections || []).map(s => ({
    id: s.id, name: s.name, start: s.start_tick, end: s.end_tick,
    role: s.role, lyrics: s.lyrics || "", muted: !!s.muted
  }));
  const tracks = (sk.tracks || []).map(t => ({
    id: t.track_id, type: t.type, muted: !!t.muted,
    n_events: (t.events || []).length,
    vol: t.volume_db
  }));
  return JSON.stringify({
    song_id: sk.song_id,
    seed: sk.generation_seed,
    bpm: sk.timebase && sk.timebase.initial_bpm,
    key: sk.timebase && sk.timebase.key,
    sections: secs,
    tracks: tracks
  });
}


function playScore() {
  if (!skeleton) compile();
  stopAll();
  const ctx = ensureAudio();
  playing = true;
  const btn = $("btnPlay");
  if (btn) btn.textContent = "Stop";
  startFluxAnalysis();
  setStatus("Playing · shelves + flux + BBD", "ok");
  const t0 = ctx.currentTime + 0.06;
  const total = ticksToSec(totalTicks());

  skeleton.tracks.forEach(track => {
    if (track.muted) return;
    const gScale = Math.pow(10, (track.volume_db || 0) / 20);
    const spatial = track.type === "STRINGS" || track.type === "LEAD" || track.type === "VOCAL" || track.type === "PAD";
    const dest = trackDest(ctx, gScale, track.pan, spatial);

    track.events.forEach(ev => {
      if (ev.type !== "NOTE_ON") return;
      const t = t0 + ticksToSec(ev.tick);
      const dur = ticksToSec(ev.duration_ticks || TPQ / 2);
      const vel = (ev.velocity || 100) / 127;
      if (track.type === "DRUMS") {
        if (ev.note_number === 36) playKick(ctx, t, vel, dest);
        else if (ev.note_number === 38) playSnare(ctx, t, vel, dest);
        else playHat(ctx, t, vel, dest);
      } else if (track.type === "BASS") {
        playBass(ctx, ev.note_number, t, dur, vel, dest);
      } else if (track.type === "STRINGS") {
        playWaveguide(ctx, ev.note_number, t, vel, dest);
      } else if (track.type === "VOCAL") {
        const role = ev.role || "male";
        if (role !== "none") {
          playVocalPhoneme(ctx, ev.note_number, t, dur, vel, role, ev.phoneme || "ah", dest);
        }
      } else if (track.type === "PAD") {
        playFM(ctx, ev.note_number, t, dur, vel, false, dest);
      } else {
        playFM(ctx, ev.note_number, t, dur * 0.75, vel, true, dest);
      }
    });
  });

  const tick = () => {
    if (!playing) return;
    const e = audioCtx.currentTime - t0;
    const prog = $("prog");
    if (prog) prog.style.width = Math.min(100, (e / total) * 100) + "%";
    if (e < total) requestAnimationFrame(tick);
    else {
      stopAll();
      setStatus("Playback complete · Phase 4", "ok");
      if (prog) prog.style.width = "100%";
    }
  };
  requestAnimationFrame(tick);
}


/* ─── Phase 6: Live microphone pitch ingest ───────────────── */
let micStream = null;
let micSource = null;
let micAnalyser = null;
let micRaf = null;
let micActive = false;

function autocorrelationPitch(buf, sampleRate) {
  const size = buf.length;
  let rms = 0;
  for (let i = 0; i < size; i++) rms += buf[i] * buf[i];
  rms = Math.sqrt(rms / size);
  if (rms < 0.01) return 0;

  const maxLag = Math.floor(sampleRate / 50);   // 50 Hz low
  const minLag = Math.floor(sampleRate / 800);  // 800 Hz high for formant guide
  let bestLag = -1;
  let bestCorr = 0;
  for (let lag = minLag; lag < maxLag; lag++) {
    let sum = 0;
    for (let i = 0; i < size - lag; i++) sum += buf[i] * buf[i + lag];
    if (sum > bestCorr) {
      bestCorr = sum;
      bestLag = lag;
    }
  }
  if (bestLag < 0) return 0;
  return sampleRate / bestLag;
}

async function initLiveMicrophoneIngest(onPitch) {
  const ctx = ensureAudio();
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
    });
    micSource = ctx.createMediaStreamSource(micStream);
    micAnalyser = ctx.createAnalyser();
    micAnalyser.fftSize = 2048;
    micSource.connect(micAnalyser);
    // Do NOT connect mic to destination (would feedback)

    const data = new Float32Array(micAnalyser.fftSize);
    micActive = true;

    const tick = () => {
      if (!micActive || !micAnalyser) return;
      micAnalyser.getFloatTimeDomainData(data);
      const hz = autocorrelationPitch(data, ctx.sampleRate);
      if (hz > 50 && hz < 1500 && typeof onPitch === "function") onPitch(hz);
      micRaf = requestAnimationFrame(tick);
    };
    tick();
    return true;
  } catch (err) {
    console.warn("[Mic] denied or unavailable", err);
    micActive = false;
    return false;
  }
}

function disconnectLiveMicrophone() {
  micActive = false;
  if (micRaf) {
    cancelAnimationFrame(micRaf);
    micRaf = null;
  }
  try {
    if (micSource) micSource.disconnect();
  } catch (e) {}
  micSource = null;
  micAnalyser = null;
  if (micStream) {
    micStream.getTracks().forEach(t => t.stop());
    micStream = null;
  }
}


/**
 * Local Neural Vocals Lab router — phoneme map → POST /api/local_neural_vocal_synthesis
 * Falls back to formant Web Audio if server offline.
 */
async function renderLocalNeuralVocalPhrase(noteEvents, lyricsText, roleProfile, quality) {
  const words = String(lyricsText || "la").toLowerCase().split(/\s+/).filter(Boolean);
  const phonemeTimeline = [];
  const events = (noteEvents || []).filter(function (e) { return e.type === "NOTE_ON" || e.note_number != null; });

  events.forEach(function (event, idx) {
    const wordToken = words[idx % Math.max(1, words.length)] || "la";
    let chosenPhoneme = "ah";
    if (/[ie]/.test(wordToken)) chosenPhoneme = "ee";
    if (/[ou]/.test(wordToken)) chosenPhoneme = "oo";
    if (/a/.test(wordToken) && chosenPhoneme === "ah") chosenPhoneme = "ah";
    const midi = event.note_number || event.note || 60;
    phonemeTimeline.push({
      tick_position: event.tick || 0,
      duration_ticks: event.duration_ticks || 480,
      midi_note: midi,
      target_f0_hz: (440 * Math.pow(2, (midi - 69) / 12)).toFixed(2),
      phoneme: chosenPhoneme,
      text_token: wordToken
    });
  });

  const bpm = (skeleton && skeleton.timebase && skeleton.timebase.initial_bpm) || 102;
  const body = {
    task_type: "NEURAL_SINGING_INFERENCE",
    role_profile: roleProfile || "male",
    quality: quality || "production",
    sample_rate: 44100,
    bpm: bpm,
    tpq: typeof TPQ !== "undefined" ? TPQ : 960,
    phoneme_map: phonemeTimeline
  };

  try {
    const res = await fetch("/api/local_neural_vocal_synthesis", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Studio-Capability": window.__STUDIO_CAPABILITY__ || "" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok || data.status !== "SUCCESS") throw new Error(data.error || res.statusText);
    if (typeof setStatus === "function") {
      setStatus("Vocal lab · " + (data.samples_rendered || 0) + " samples", "ok");
    }
    return data;
  } catch (err) {
    console.warn("[Neural-Vocals] local worker absent — formant fallback", err);
    if (typeof setStatus === "function") {
      setStatus("Vocal lab offline — using formant guides on Play", "warn");
    }
    return null;
  }
}
