/* KAN-512 — Look 4 Compact rail + collapsible tray */
(function () {
  "use strict";

  const PREF_SIDE = "charterTraySide";
  const PREF_COLLAPSED = "charterTrayCollapsed";

  const chip = document.getElementById("cf-chip");
  const noteInput = document.getElementById("cf-note-input");
  const noteSheet = document.getElementById("cf-note-sheet");
  const cancelConfirm = document.getElementById("cf-cancel-confirm");
  const rail = document.getElementById("cf-rail");
  const trayToggle = document.getElementById("cf-tray-toggle");
  const trayToggleEdge = document.getElementById("cf-tray-toggle-edge");
  const pauseBtn = document.getElementById("cf-pause");
  const assistBtn = document.getElementById("cf-assist");
  const mistBtn = document.getElementById("cf-mist");

  let sessionId = "";
  let lastStillId = "";
  let saveTimer = null;
  let paused = false;
  let assistOn = false;
  let mistOn = false;
  let noteOpen = false;
  let traySide = "east";
  let collapsed = false;

  function api() {
    return (window.pywebview && window.pywebview.api) || null;
  }

  function setChip(text) {
    if (chip) chip.textContent = text;
  }

  function loadPrefs() {
    try {
      const s = localStorage.getItem(PREF_SIDE);
      traySide = s === "west" ? "west" : "east";
      collapsed = localStorage.getItem(PREF_COLLAPSED) === "1";
    } catch (_err) {
      traySide = "east";
      collapsed = false;
    }
  }

  function savePrefs() {
    try {
      localStorage.setItem(PREF_SIDE, traySide);
      localStorage.setItem(PREF_COLLAPSED, collapsed ? "1" : "0");
    } catch (_err) {
      /* ignore */
    }
  }

  function applyChrome() {
    document.body.setAttribute("data-tray", traySide);
    document.body.setAttribute("data-collapsed", collapsed ? "1" : "0");
    if (rail) rail.hidden = !!collapsed;
    if (trayToggle) {
      trayToggle.setAttribute("aria-pressed", collapsed ? "false" : "true");
      trayToggle.title = collapsed ? "Show tray" : "Hide tray";
    }
    if (trayToggleEdge) {
      trayToggleEdge.hidden = !collapsed;
      trayToggleEdge.setAttribute("aria-pressed", "false");
    }
    if (noteSheet) noteSheet.hidden = !noteOpen || collapsed;
    if (pauseBtn) {
      pauseBtn.setAttribute("aria-pressed", paused ? "true" : "false");
      pauseBtn.classList.toggle("is-on", paused);
      pauseBtn.title = paused ? "Resume" : "Pause";
    }
    if (assistBtn) {
      assistBtn.setAttribute("aria-pressed", assistOn ? "true" : "false");
      assistBtn.classList.toggle("is-on", assistOn);
    }
    if (mistBtn) {
      mistBtn.setAttribute("aria-pressed", mistOn ? "true" : "false");
      mistBtn.classList.toggle("is-on", mistOn);
    }
  }

  async function pushTrayLayout() {
    const bridge = api();
    if (!bridge || !bridge.charter_float_set_tray) return;
    try {
      const res = await bridge.charter_float_set_tray({
        side: traySide,
        collapsed: collapsed,
        note_open: noteOpen && !collapsed,
      });
      if (res && res.side) traySide = res.side === "west" ? "west" : "east";
      applyChrome();
      scheduleFrameSave();
    } catch (_err) {
      /* ignore */
    }
  }

  function showCancel(on) {
    if (cancelConfirm) cancelConfirm.hidden = !on;
  }

  async function notifyMain(event) {
    const bridge = api();
    if (bridge && bridge.charter_float_notify_main) {
      try {
        await bridge.charter_float_notify_main(event, sessionId);
      } catch (_err) {
        /* ignore */
      }
    }
  }

  function applySession(payload) {
    if (!payload) return;
    sessionId = payload.id || sessionId;
    assistOn = !!payload.agent_assist;
    mistOn = !!payload.armed_mist;
    const notes = payload.notes != null ? payload.notes : 0;
    const stills = payload.stills != null ? payload.stills : 0;
    setChip(
      (paused ? "Paused · " : "Recording · ") +
        ((payload.charter || sessionId || "session").slice(0, 36)) +
        " · " +
        notes +
        "n · " +
        stills +
        "s"
    );
    showCancel(false);
    applyChrome();
    scheduleFrameSave();
  }

  window.__charterFloatApply = applySession;

  async function loadOpenSession() {
    try {
      const res = await fetch("/api/manual-sessions/open");
      const data = await res.json();
      if (data && data.open && data.session) {
        applySession({
          id: data.session.id,
          charter: data.session.charter,
          notes: (data.session.notes || []).length,
          stills: (data.session.stills || []).length,
          agent_assist: data.session.agent_assist,
          armed_mist: data.session.armed_mist,
        });
        return true;
      }
    } catch (_err) {
      /* ignore */
    }
    return false;
  }

  async function ensureSession() {
    if (sessionId) return true;
    setChip("Linking session…");
    const ok = await loadOpenSession();
    if (!ok || !sessionId) {
      setChip("No open session — Start again from Manual");
      return false;
    }
    return true;
  }

  async function currentBbox() {
    const bridge = api();
    if (!bridge || !bridge.charter_float_screen_bbox) return null;
    try {
      const res = await bridge.charter_float_screen_bbox();
      return res && res.status === "ok" ? res : null;
    } catch (_err) {
      return null;
    }
  }

  function scheduleFrameSave() {
    if (!sessionId) return;
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(async function () {
      const geom = await currentBbox();
      if (!geom) return;
      try {
        await fetch(
          "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/frame",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(
              Object.assign({}, geom.frame || {}, {
                frame_mode: "float",
                screen_bbox: geom.screen_bbox || null,
              })
            ),
          }
        );
      } catch (_err) {
        /* ignore */
      }
    }, 300);
  }

  async function setCollapsed(next) {
    collapsed = !!next;
    if (collapsed) noteOpen = false;
    savePrefs();
    applyChrome();
    await pushTrayLayout();
  }

  async function toggleNoteSheet() {
    if (collapsed) return;
    noteOpen = !noteOpen;
    applyChrome();
    await pushTrayLayout();
    if (noteOpen && noteInput) {
      try {
        noteInput.focus();
      } catch (_err) {
        /* ignore */
      }
    }
  }

  async function addNote() {
    if (paused) {
      setChip("Paused — resume to add notes");
      return;
    }
    if (!(await ensureSession())) return;
    const text = noteInput ? noteInput.value.trim() : "";
    if (!text) {
      setChip("Type a note first");
      if (!noteOpen) await toggleNoteSheet();
      return;
    }
    try {
      const res = await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/notes",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text }),
        }
      );
      const data = await res.json();
      if (data.status === "ok" && data.session) {
        if (noteInput) noteInput.value = "";
        applySession({
          id: data.session.id,
          charter: data.session.charter,
          notes: (data.session.notes || []).length,
          stills: (data.session.stills || []).length,
          agent_assist: data.session.agent_assist,
          armed_mist: data.session.armed_mist,
        });
        noteOpen = false;
        applyChrome();
        await pushTrayLayout();
        await notifyMain("note");
      } else {
        setChip(data.message || "Note failed");
      }
    } catch (_err) {
      setChip("Note failed");
    }
  }

  async function addStill() {
    if (paused) {
      setChip("Paused — resume to capture stills");
      return;
    }
    if (!(await ensureSession())) return;
    const bridge = api();
    let bbox = null;
    setChip("Capturing still…");
    try {
      if (bridge && bridge.charter_float_prepare_still) {
        const prep = await bridge.charter_float_prepare_still();
        if (prep && prep.screen_bbox) bbox = prep.screen_bbox;
      } else {
        const geom = await currentBbox();
        if (geom) bbox = geom.screen_bbox;
      }
      const res = await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/stills",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ screen_bbox: bbox }),
        }
      );
      const data = await res.json();
      if (data.status === "ok" && data.session) {
        if (data.still && data.still.id) lastStillId = data.still.id;
        applySession({
          id: data.session.id,
          charter: data.session.charter,
          notes: (data.session.notes || []).length,
          stills: (data.session.stills || []).length,
          agent_assist: data.session.agent_assist,
          armed_mist: data.session.armed_mist,
        });
        await notifyMain("still");
      } else {
        setChip((data && data.message) || "Still failed");
      }
    } catch (_err) {
      setChip("Still failed");
    } finally {
      if (bridge && bridge.charter_float_restore) {
        try {
          await bridge.charter_float_restore();
        } catch (_e2) {
          /* ignore */
        }
      }
    }
  }

  async function togglePause() {
    paused = !paused;
    applyChrome();
    setChip(paused ? "Paused" : "Recording");
  }

  async function toggleAssist() {
    if (!(await ensureSession())) return;
    assistOn = !assistOn;
    applyChrome();
    try {
      await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/toggles",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_assist: assistOn }),
        }
      );
    } catch (_err) {
      setChip("Assist toggle failed");
    }
  }

  async function toggleMist() {
    if (!(await ensureSession())) return;
    mistOn = !mistOn;
    applyChrome();
    try {
      await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/toggles",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ armed_mist: mistOn }),
        }
      );
    } catch (_err) {
      setChip("Mist toggle failed");
    }
  }

  async function endSession() {
    if (!(await ensureSession())) return;
    showCancel(false);
    try {
      await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/end",
        { method: "POST" }
      );
    } catch (_err) {
      /* main will refresh */
    }
    await notifyMain("ended");
  }

  async function cancelSession() {
    if (!(await ensureSession())) return;
    try {
      await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/cancel",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ confirm: true }),
        }
      );
    } catch (_err) {
      /* ignore */
    }
    await notifyMain("cancelled");
  }

  document.getElementById("cf-still").addEventListener("click", addStill);
  document.getElementById("cf-note").addEventListener("click", function () {
    toggleNoteSheet();
  });
  document.getElementById("cf-note-add").addEventListener("click", addNote);
  document.getElementById("cf-pause").addEventListener("click", togglePause);
  document.getElementById("cf-assist").addEventListener("click", toggleAssist);
  document.getElementById("cf-mist").addEventListener("click", toggleMist);
  document.getElementById("cf-end").addEventListener("click", endSession);
  document.getElementById("cf-cancel").addEventListener("click", function () {
    showCancel(true);
  });
  document.getElementById("cf-cancel-yes").addEventListener("click", cancelSession);
  document.getElementById("cf-cancel-no").addEventListener("click", function () {
    showCancel(false);
  });
  function onTrayToggle() {
    setCollapsed(!collapsed);
  }
  if (trayToggle) trayToggle.addEventListener("click", onTrayToggle);
  if (trayToggleEdge) trayToggleEdge.addEventListener("click", onTrayToggle);

  if (noteInput) {
    noteInput.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        addNote();
      } else if (ev.key === "Escape") {
        noteOpen = false;
        applyChrome();
        pushTrayLayout();
      }
    });
  }

  /* Drag whole shell via tray rail (moves ring + tray). */
  (function bindRailDrag() {
    const handle = rail;
    if (!handle) return;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    let pending = null;

    async function flush(dx, dy) {
      const bridge = api();
      if (!bridge || !bridge.charter_float_drag_by) return;
      try {
        await bridge.charter_float_drag_by(dx, dy);
        scheduleFrameSave();
      } catch (_err) {
        /* ignore */
      }
    }

    handle.addEventListener("pointerdown", function (ev) {
      if (ev.button != null && ev.button !== 0) return;
      if (ev.target && ev.target.closest && ev.target.closest("button, input")) {
        return;
      }
      dragging = true;
      lastX = ev.screenX;
      lastY = ev.screenY;
      try {
        handle.setPointerCapture(ev.pointerId);
      } catch (_err) {
        /* ignore */
      }
      ev.preventDefault();
    });
    handle.addEventListener("pointermove", function (ev) {
      if (!dragging) return;
      const dx = ev.screenX - lastX;
      const dy = ev.screenY - lastY;
      if (!dx && !dy) return;
      lastX = ev.screenX;
      lastY = ev.screenY;
      if (pending) {
        pending.dx += dx;
        pending.dy += dy;
        return;
      }
      pending = { dx: dx, dy: dy };
      window.requestAnimationFrame(function () {
        const step = pending;
        pending = null;
        if (step && (step.dx || step.dy)) flush(step.dx, step.dy);
      });
    });
    function endDrag(ev) {
      if (!dragging) return;
      dragging = false;
      try {
        handle.releasePointerCapture(ev.pointerId);
      } catch (_err) {
        /* ignore */
      }
    }
    handle.addEventListener("pointerup", endDrag);
    handle.addEventListener("pointercancel", endDrag);
  })();

  loadPrefs();
  applyChrome();
  pushTrayLayout();
  setInterval(scheduleFrameSave, 2500);
  loadOpenSession();
  setInterval(function () {
    if (!sessionId) loadOpenSession();
  }, 800);
})();
