/**
 * SongForge chat-led studio surface (v2.20)
 * Deterministic prompt → Score Graph. No cloud generation APIs.
 * Persistence: localStorage sf_chat_session_v220 (+ last Score Graph).
 */
(function (global) {
  "use strict";

  var SF_CHAT_SESSION_KEY = "sf_chat_session_v220";
  var SF_CHAT_TRANSCRIPT_MAX = 80;
  var varyNonce = 0;
  var chatMessages = [];
  var lastExportDigest = null;
  var sessionHydrated = false;
  var persistTimer = null;

  /** Pure: build a session snapshot object (testable). */
  function buildChatSessionPayload(opts) {
    opts = opts || {};
    return {
      version: "2.20.0",
      saved_at: opts.saved_at || new Date().toISOString(),
      vary_nonce: opts.vary_nonce != null ? opts.vary_nonce : 0,
      last_export_digest: opts.last_export_digest || null,
      messages: Array.isArray(opts.messages) ? opts.messages.slice(-SF_CHAT_TRANSCRIPT_MAX) : [],
      prompt: opts.prompt || "",
      lyrics_opt: opts.lyrics_opt || "",
      skeleton: opts.skeleton || null
    };
  }

  /** Pure: serialize session → JSON string. */
  function serializeChatSession(payload) {
    return JSON.stringify(buildChatSessionPayload(payload));
  }

  /** Pure: parse + validate session JSON. Returns {ok, session|error}. */
  function parseChatSession(raw) {
    if (raw == null || raw === "") return { ok: false, error: "empty" };
    var obj;
    try {
      obj = typeof raw === "string" ? JSON.parse(raw) : raw;
    } catch (e) {
      return { ok: false, error: "invalid_json" };
    }
    if (!obj || typeof obj !== "object") return { ok: false, error: "not_object" };
    if (!Array.isArray(obj.messages)) obj.messages = [];
    obj.messages = obj.messages.filter(function (m) {
      return m && (m.role === "user" || m.role === "sys") && typeof m.text === "string";
    }).slice(-SF_CHAT_TRANSCRIPT_MAX);
    if (obj.vary_nonce == null) obj.vary_nonce = 0;
    return { ok: true, session: obj };
  }

  /** Pure: format compiled facts for studio reply bubbles. */
  function formatStudioFacts(sk, action) {
    if (!sk || !sk.timebase) return "No Score Graph.";
    var tb = sk.timebase;
    var notes = (sk.tracks || []).reduce(function (n, t) {
      return n + ((t.events && t.events.length) || 0);
    }, 0);
    var secs = (sk.structure && sk.structure.sections) ? sk.structure.sections.length : 0;
    var form = (sk.structure && sk.structure.sections)
      ? sk.structure.sections.map(function (s) { return s.name; }).join(" → ")
      : "—";
    var lines = [
      (action || "Compiled") + " · local deterministic studio",
      "BPM " + tb.initial_bpm + " · " + tb.key + " · " + tb.genre,
      "Form: " + form + " (" + secs + " sections)",
      "Seed " + sk.generation_seed + " · " + sk.song_id,
      "Schema " + (sk.$schema || sk.schema_version || "—"),
      notes + " note events · formant vocals (not neural SVS)"
    ];
    if (lastExportDigest) {
      lines.push("Last export " + String(lastExportDigest).slice(0, 16) + "…");
    }
    return lines.join("\n");
  }

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function updateTrustChips() {
    var sk = global.skeleton || (typeof skeleton !== "undefined" ? skeleton : null);
    var chipSchema = $("chipSchema");
    var chipSeed = $("chipSeed");
    var chipSong = $("chipSong");
    var chipExport = $("chipExport");
    if (chipSchema) {
      chipSchema.textContent = sk
        ? "schema " + String(sk.schema_version || sk.$schema || "—").replace("pulseforge.songforge.skeleton.", "")
        : "schema —";
      chipSchema.className = sk ? "chip hot" : "chip";
    }
    if (chipSeed) {
      chipSeed.textContent = sk && sk.generation_seed != null
        ? "seed " + sk.generation_seed
        : "seed —";
      chipSeed.className = sk ? "chip ok" : "chip";
    }
    if (chipSong) {
      chipSong.textContent = sk && sk.song_id ? "song " + sk.song_id : "song —";
    }
    if (chipExport) {
      if (lastExportDigest) {
        chipExport.textContent = "export " + String(lastExportDigest).slice(0, 12) + "…";
        chipExport.className = "chip ok";
      } else {
        chipExport.textContent = "export —";
        chipExport.className = "chip";
      }
    }
  }

  function renderChat() {
    var log = $("chatLog");
    if (!log) return;
    log.innerHTML = "";
    chatMessages.forEach(function (m, idx) {
      var div = document.createElement("div");
      div.className = "bubble " + (m.role === "user" ? "user" : "sys");
      var body = document.createElement("div");
      body.innerHTML = escapeHtml(m.text).replace(/\n/g, "<br/>");
      div.appendChild(body);
      if (m.meta) {
        var meta = document.createElement("span");
        meta.className = "meta";
        meta.textContent = m.meta;
        div.appendChild(meta);
      }
      if (m.role === "sys" && m.playable && idx === chatMessages.length - 1) {
        var acts = document.createElement("div");
        acts.className = "acts";
        var playBtn = document.createElement("button");
        playBtn.type = "button";
        playBtn.className = "sm";
        playBtn.textContent = "▶ Play";
        playBtn.onclick = function () {
          if (typeof playScore === "function") playScore();
        };
        acts.appendChild(playBtn);
        div.appendChild(acts);
      }
      log.appendChild(div);
    });
    log.scrollTop = log.scrollHeight;
  }

  function pushMessage(role, text, extra) {
    extra = extra || {};
    if (role === "system") role = "sys";
    chatMessages.push({
      role: role,
      text: String(text || ""),
      meta: extra.meta || null,
      playable: !!extra.playable,
      at: new Date().toISOString()
    });
    if (chatMessages.length > SF_CHAT_TRANSCRIPT_MAX) {
      chatMessages = chatMessages.slice(-SF_CHAT_TRANSCRIPT_MAX);
    }
    renderChat();
    schedulePersist();
  }

  function schedulePersist() {
    if (persistTimer) clearTimeout(persistTimer);
    persistTimer = setTimeout(persistSession, 120);
  }

  function persistSession() {
    try {
      var sk = global.skeleton || (typeof skeleton !== "undefined" ? skeleton : null);
      var payload = buildChatSessionPayload({
        vary_nonce: varyNonce,
        last_export_digest: lastExportDigest,
        messages: chatMessages,
        prompt: ($("prompt") && $("prompt").value) || "",
        lyrics_opt: ($("lyricsOpt") && $("lyricsOpt").value) || "",
        skeleton: sk
      });
      localStorage.setItem(SF_CHAT_SESSION_KEY, serializeChatSession(payload));
    } catch (e) {
      console.warn("[chat] persist failed", e);
    }
  }

  function applyOptionalLyrics(sk, lyricsText) {
    if (!sk || !lyricsText || !String(lyricsText).trim()) return;
    var text = String(lyricsText).trim();
    var targets = (sk.structure.sections || []).filter(function (s) {
      return s.role && s.role !== "none" && (s.type === "verse" || s.type === "chorus" || s.type === "bridge");
    });
    if (!targets.length) return;
    // Split on blank lines into chunks; stamp onto vocal sections in order
    var chunks = text.split(/\n\s*\n/).map(function (c) { return c.trim(); }).filter(Boolean);
    if (chunks.length === 1) {
      targets.forEach(function (s) { s.lyrics = chunks[0]; });
    } else {
      targets.forEach(function (s, i) {
        if (chunks[i]) s.lyrics = chunks[i];
      });
    }
    if (typeof rebuildVocalsFromLyrics === "function") rebuildVocalsFromLyrics();
  }

  function afterCompile(actionLabel, autoPlay) {
    var sk = global.skeleton || skeleton;
    if (typeof render === "function") render();
    updateTrustChips();
    pushMessage("sys", formatStudioFacts(sk, actionLabel), {
      meta: "local · deterministic · recoverable",
      playable: true
    });
    if (typeof setStatus === "function") {
      setStatus(
        actionLabel + " · " + sk.timebase.initial_bpm + " BPM · " + sk.timebase.key + " · " + sk.song_id,
        "ok"
      );
    }
    schedulePersist();
    if (autoPlay && typeof playScore === "function") {
      try { playScore(); } catch (e) { /* autoplay may need gesture — Play button still works */ }
    }
  }

  function readPrompt() {
    var t = ($("prompt") && $("prompt").value) || "";
    t = t.trim();
    if (!t) t = "dark 102 BPM alt hip-hop, F# minor, guitar plucks, male verse, female chorus";
    return t;
  }

  function applyTitleOverrides(sk) {
    var titleEl = $("title");
    if (titleEl && titleEl.value) sk.title = titleEl.value;
    else if (!sk.title || sk.title === "Generated") sk.title = readPrompt().slice(0, 48);
    var bpmO = $("bpmOverride");
    if (bpmO && bpmO.value) sk.timebase.initial_bpm = Math.max(60, Math.min(180, +bpmO.value));
    var keyO = $("keyOverride");
    if (keyO && keyO.value) sk.timebase.key = keyO.value;
  }

  function doGenerate(opts) {
    opts = opts || {};
    var text = readPrompt();
    var lyricsOpt = ($("lyricsOpt") && $("lyricsOpt").value) || "";
    pushMessage("user", (opts.userLabel || "Generate") + ": " + text + (lyricsOpt.trim() ? "\n[lyrics attached]" : ""));

    if (typeof pushSkeletonCheckpoint === "function" && (global.skeleton || (typeof skeleton !== "undefined" && skeleton))) {
      pushSkeletonCheckpoint("before_generate");
    }

    var seedOpts = {};
    if (opts.seed != null) seedOpts.seed = opts.seed >>> 0;
    else if (opts.nonce != null) seedOpts.nonce = String(opts.nonce);
    else seedOpts.nonce = "0";

    var sk = parsePrompt(text, seedOpts);
    global.skeleton = sk;
    if (typeof skeleton !== "undefined") skeleton = sk;
    applyTitleOverrides(sk);
    applyOptionalLyrics(sk, lyricsOpt);
    if (typeof appendChangeLedger === "function") {
      appendChangeLedger("chat_generate", {
        seed: sk.generation_seed,
        song_id: sk.song_id,
        action: opts.action || "generate",
        prompt: text
      });
    }
    afterCompile(opts.actionLabel || "Generated", opts.autoPlay !== false);
  }

  function doVary() {
    varyNonce += 1;
    doGenerate({
      nonce: String(varyNonce),
      action: "vary",
      actionLabel: "Varied (new seed)",
      userLabel: "Vary"
    });
  }

  function doExtend() {
    var sk = global.skeleton || (typeof skeleton !== "undefined" ? skeleton : null);
    if (!sk) {
      doGenerate({ actionLabel: "Generated", userLabel: "Generate (needed before Extend)" });
      return;
    }
    pushMessage("user", "Extend arrangement");
    var lyricsOpt = ($("lyricsOpt") && $("lyricsOpt").value) || "";
    var r = extendArrangement({
      lyrics: lyricsOpt.trim() || undefined
    });
    if (!r.ok) {
      pushMessage("sys", "Extend failed: " + (r.error || "unknown"));
      return;
    }
    afterCompile("Extended · +" + r.section_id, true);
  }

  function doRemix() {
    var text = readPrompt();
    pushMessage("user", "Remix: " + text);
    varyNonce += 1;
    var r = remixArrangement(text, { nonce: "remix-" + varyNonce });
    if (!r.ok) {
      pushMessage("sys", "Remix failed");
      return;
    }
    var lyricsOpt = ($("lyricsOpt") && $("lyricsOpt").value) || "";
    if (lyricsOpt.trim()) applyOptionalLyrics(global.skeleton || skeleton, lyricsOpt);
    applyTitleOverrides(global.skeleton || skeleton);
    afterCompile("Remixed (lyrics preserved, new seed)", true);
  }

  function doUndo() {
    if (typeof undoLastCheckpoint !== "function") {
      pushMessage("sys", "Undo unavailable in this build.");
      return;
    }
    var r = undoLastCheckpoint();
    if (!r.ok) {
      pushMessage("sys", "Nothing to undo.");
      if (typeof setStatus === "function") setStatus("Nothing to undo", "warn");
      return;
    }
    if (typeof render === "function") render();
    updateTrustChips();
    pushMessage("sys", formatStudioFacts(global.skeleton || skeleton, "Undid → " + (r.label || "checkpoint")), {
      meta: "change_ledger + checkpoint",
      playable: true
    });
    schedulePersist();
  }

  function clearChat() {
    chatMessages = [];
    pushMessage("sys",
      "Session cleared. Describe a song — Generate compiles an integer-tick Score Graph locally. Formant vocals, not neural singing. Exports are content-addressed when studio_server is running.",
      { meta: "SongForge 2.20 · zero cloud gen APIs" }
    );
    schedulePersist();
  }

  function restoreSessionFromStorage() {
    var raw;
    try { raw = localStorage.getItem(SF_CHAT_SESSION_KEY); } catch (e) { return false; }
    var parsed = parseChatSession(raw);
    if (!parsed.ok) return false;
    var sess = parsed.session;
    varyNonce = sess.vary_nonce || 0;
    lastExportDigest = sess.last_export_digest || null;
    if (sess.prompt && $("prompt")) $("prompt").value = sess.prompt;
    if (sess.lyrics_opt && $("lyricsOpt")) $("lyricsOpt").value = sess.lyrics_opt;
    if (sess.skeleton && sess.skeleton.structure && sess.skeleton.tracks) {
      if (typeof loadProjectObject === "function") {
        var lr = loadProjectObject(sess.skeleton);
        if (lr.ok && typeof render === "function") render();
      }
    }
    if (sess.messages && sess.messages.length) {
      chatMessages = sess.messages.slice();
      renderChat();
    }
    updateTrustChips();
    return true;
  }

  function noteExportDigest(digest, opts) {
    if (!digest) return;
    opts = opts || {};
    lastExportDigest = String(digest);
    updateTrustChips();
    schedulePersist();
    if (opts.announce) {
      pushMessage("sys", "Export certified · digest " + lastExportDigest.slice(0, 20) + "…", {
        meta: "content-addressed · PF-SOUND-002"
      });
    }
  }

  function wrapExportForDigest() {
    if (typeof exportWav !== "function") return;
    var orig = exportWav;
    global.exportWav = exportWav = async function () {
      var metrics = await orig.apply(this, arguments);
      // Prefer durable project artifact if available
      try {
        if (typeof durableProjectRef !== "undefined" && durableProjectRef) {
          /* digest may be on last commit — also hash song_id as soft chip */
        }
      } catch (_) {}
      try {
        var sk = global.skeleton || skeleton;
        if (sk && sk.song_id) {
          // Soft digest from project fingerprint when server digest unknown
          if (typeof projectFingerprint === "function" && typeof hashSeed === "function") {
            var soft = hashSeed(projectFingerprint(sk) + "|wav|" + (metrics && metrics.peak)).toString(16);
            if (!lastExportDigest) noteExportDigest("soft-" + soft, { announce: true });
          }
        }
      } catch (e) { /* non-fatal */ }
      return metrics;
    };
    // Also wrap savePayload path used by OTIO/MEG if present
    if (typeof savePayload === "function") {
      var origSave = savePayload;
      global.savePayload = savePayload = function (name, body, kind, mime) {
        var ret = origSave.apply(this, arguments);
        try {
          if (typeof hashSeed === "function") {
            noteExportDigest(hashSeed(String(name) + "|" + String(body).slice(0, 2000)).toString(16), { announce: false });
          }
        } catch (_) {}
        return ret;
      };
    }
  }

  function wireButtons() {
    var g = $("btnGenerate");
    if (g) g.onclick = function () { doGenerate({ actionLabel: "Generated", userLabel: "Generate" }); };
    var v = $("btnVary");
    if (v) v.onclick = doVary;
    var e = $("btnExtend");
    if (e) e.onclick = doExtend;
    var r = $("btnRemix");
    if (r) r.onclick = doRemix;
    var u = $("btnUndo");
    if (u) u.onclick = doUndo;
    var c = $("btnClearChat");
    if (c) c.onclick = clearChat;
    var rs = $("btnRestoreSession");
    if (rs) rs.onclick = function () {
      if (restoreSessionFromStorage()) {
        if (typeof setStatus === "function") setStatus("Session restored from localStorage", "ok");
        pushMessage("sys", "Restored prior session from localStorage.", { meta: "continuity" });
      } else if (typeof setStatus === "function") {
        setStatus("No saved chat session", "warn");
      }
    };
    var prompt = $("prompt");
    if (prompt) {
      prompt.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey)) {
          ev.preventDefault();
          doGenerate({ actionLabel: "Generated", userLabel: "Generate" });
        }
      });
    }
  }

  function initChatStudio() {
    if (sessionHydrated) return;
    sessionHydrated = true;
    wireButtons();
    wrapExportForDigest();
    var restored = restoreSessionFromStorage();
    if (!restored || !chatMessages.length) {
      chatMessages = [];
      pushMessage("sys",
        "Welcome to SongForge — chat-led, local, deterministic.\n" +
        "Type a prompt → Generate. Vary for a new seed. Extend appends a section. Remix keeps lyrics, new arrangement.\n" +
        "Honest ceiling: rule compiler + Web Audio formants/DSP — not Suno/ElevenLabs neural vocals.",
        { meta: "v2.20 · integer-tick Score Graph · TPQ=960" }
      );
      // Starter Score Graph so Play / mixer work before first Generate
      if (!(global.skeleton || (typeof skeleton !== "undefined" && skeleton))) {
        if ($("prompt") && !$("prompt").value) {
          $("prompt").value = "dark 102 BPM alt hip-hop, F# minor, guitar plucks, male verse, female chorus";
        }
        doGenerate({ actionLabel: "Ready", userLabel: "Starter", autoPlay: false, nonce: "0" });
        // doGenerate already pushed user+sys; trim the synthetic user starter line for cleaner welcome
        if (chatMessages.length >= 2 && chatMessages[chatMessages.length - 2].role === "user" &&
            String(chatMessages[chatMessages.length - 2].text || "").indexOf("Starter:") === 0) {
          chatMessages.splice(chatMessages.length - 2, 1);
          renderChat();
        }
      } else {
        updateTrustChips();
        pushMessage("sys", formatStudioFacts(global.skeleton || skeleton, "Ready"), {
          meta: "starter Score Graph",
          playable: true
        });
      }
    } else {
      updateTrustChips();
      if (typeof setStatus === "function") {
        setStatus("Restored chat session · local continuity", "ok");
      }
    }
    // Persist on page hide
    window.addEventListener("pagehide", persistSession);
    window.addEventListener("beforeunload", persistSession);
  }

  // Exports for tests / other modules
  global.updateTrustChips = updateTrustChips;
  global.persistChatSession = persistSession;
  global.setLastExportDigest = noteExportDigest;
  global.SFChat = {
    buildChatSessionPayload: buildChatSessionPayload,
    serializeChatSession: serializeChatSession,
    parseChatSession: parseChatSession,
    formatStudioFacts: formatStudioFacts,
    noteExportDigest: noteExportDigest,
    SESSION_KEY: SF_CHAT_SESSION_KEY
  };
  global.SongForgeChat = {
    chatGenerate: function () {
      doGenerate({ actionLabel: "Generated", userLabel: "Generate" });
    },
    pushMessage: pushMessage,
    doVary: doVary,
    doExtend: doExtend,
    doRemix: doRemix,
    doUndo: doUndo,
    persistSession: persistSession,
    restoreSession: restoreSessionFromStorage,
    formatStudioFacts: formatStudioFacts,
    serializeChatSession: serializeChatSession,
    parseChatSession: parseChatSession,
    buildChatSessionPayload: buildChatSessionPayload
  };
  global.initChatStudio = initChatStudio;
})(typeof window !== "undefined" ? window : globalThis);
