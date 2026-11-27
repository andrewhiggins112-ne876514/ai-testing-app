/* KAN-386 / KAN-502 — snip hollow Charter Frame float controls */
(function () {
  "use strict";

  const chip = document.getElementById("cf-chip");
  const noteInput = document.getElementById("cf-note");
  const pageEl = document.getElementById("cf-page");
  const cancelConfirm = document.getElementById("cf-cancel-confirm");
  const row = document.querySelector(".charter-float-row");

  let sessionId = "";
  let lastStillId = "";
  let saveTimer = null;
  let ringTimer = null;
  let resizing = null;

  function api() {
    return (window.pywebview && window.pywebview.api) || null;
  }

  function setChip(text) {
    if (chip) chip.textContent = text;
  }

  function showCancel(on) {
    if (cancelConfirm) cancelConfirm.hidden = !on;
    if (row) row.hidden = !!on;
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
    const notes = payload.notes != null ? payload.notes : 0;
    const stills = payload.stills != null ? payload.stills : 0;
    setChip(
      "Recording · " +
        ((payload.charter || sessionId || "session").slice(0, 36)) +
        " · " +
        notes +
        " notes · " +
        stills +
        " stills"
    );
    showCancel(false);
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

  function scheduleRing() {
    const bridge = api();
    if (!bridge || !bridge.charter_float_apply_ring) return;
    if (ringTimer) clearTimeout(ringTimer);
    ringTimer = setTimeout(async function () {
      try {
        await bridge.charter_float_apply_ring();
      } catch (_err) {
        /* ignore */
      }
    }, 80);
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

  async function addNote() {
    if (!(await ensureSession())) return;
    const text = noteInput ? noteInput.value.trim() : "";
    if (!text) {
      setChip("Type a note first");
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
        });
        await notifyMain("note");
      } else {
        setChip(data.message || "Note failed");
      }
    } catch (_err) {
      setChip("Note failed");
    }
  }

  async function addStill() {
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

  async function annotateStill() {
    if (!(await ensureSession())) return;
    const text = noteInput ? noteInput.value.trim() : "";
    if (!text) {
      setChip("Type annotation text, then Annotate");
      return;
    }
    if (!lastStillId) {
      setChip("Capture a Still first, then Annotate");
      return;
    }
    try {
      const res = await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(sessionId) +
          "/stills/" +
          encodeURIComponent(lastStillId) +
          "/annotate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ annotation: text }),
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
        });
        setChip((chip && chip.textContent ? chip.textContent : "") + " · annotated");
      } else {
        setChip((data && data.message) || "Annotate failed");
      }
    } catch (_err) {
      setChip("Annotate failed");
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

  function onResizePointerDown(ev) {
    const handle = ev.target.closest("[data-resize]");
    if (!handle) return;
    ev.preventDefault();
    ev.stopPropagation();
    resizing = {
      edge: handle.getAttribute("data-resize") || "se",
      startX: ev.screenX,
      startY: ev.screenY,
      startW: window.outerWidth || window.innerWidth,
      startH: window.outerHeight || window.innerHeight,
    };
    window.addEventListener("pointermove", onResizePointerMove);
    window.addEventListener("pointerup", onResizePointerUp);
  }

  async function onResizePointerMove(ev) {
    if (!resizing) return;
    const bridge = api();
    if (!bridge || !bridge.charter_float_set_size) return;
    const dx = ev.screenX - resizing.startX;
    const dy = ev.screenY - resizing.startY;
    let w = resizing.startW;
    let h = resizing.startH;
    if (resizing.edge.indexOf("e") >= 0 || resizing.edge === "se") w = resizing.startW + dx;
    if (resizing.edge.indexOf("s") >= 0 || resizing.edge === "se") h = resizing.startH + dy;
    if (resizing.edge === "w") w = resizing.startW - dx;
    try {
      await bridge.charter_float_set_size(Math.round(w), Math.round(h));
      scheduleFrameSave();
    } catch (_err) {
      /* ignore */
    }
  }

  function onResizePointerUp() {
    resizing = null;
    window.removeEventListener("pointermove", onResizePointerMove);
    window.removeEventListener("pointerup", onResizePointerUp);
    scheduleRing();
    scheduleFrameSave();
  }

  document.getElementById("cf-note-add").addEventListener("click", addNote);
  document.getElementById("cf-still").addEventListener("click", addStill);
  document.getElementById("cf-annotate").addEventListener("click", annotateStill);
  document.getElementById("cf-end").addEventListener("click", endSession);
  document.getElementById("cf-cancel").addEventListener("click", function () {
    showCancel(true);
  });
  document.getElementById("cf-cancel-yes").addEventListener("click", cancelSession);
  document.getElementById("cf-cancel-no").addEventListener("click", function () {
    showCancel(false);
  });
  if (noteInput) {
    noteInput.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        addNote();
      }
    });
  }
  document.querySelectorAll("[data-resize]").forEach(function (el) {
    el.addEventListener("pointerdown", onResizePointerDown);
  });

  window.addEventListener("resize", function () {
    scheduleRing();
    scheduleFrameSave();
  });
  setInterval(scheduleFrameSave, 2000);
  loadOpenSession();
  setInterval(function () {
    if (!sessionId) loadOpenSession();
  }, 800);
  scheduleRing();

  if (pageEl) {
    pageEl.hidden = false;
    pageEl.textContent = "AUT page: none known (notes/stills still work)";
  }
})();
