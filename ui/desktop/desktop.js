(function () {
  const LAYOUT_KEY = "desktop-shell-layout-v1";
  const ORB_STYLES_KEY = "desktop-orb-styles-v1";
  const WEBGL_STYLES = ["mystic", "aether", "neural", "apex"];
  const EDGE_PAD = 16;
  const DRAG_THRESHOLD = 14;
  const BTN = 42;
  const WIDGET_MIN_W = 220;
  const WIDGET_MIN_H = 160;
  const DRAWER_MIN = 160;
  const DRAWER_MAX_LR = 420;
  const DRAWER_DEFAULT_LR = 220;
  const DRAWER_DEFAULT_TB = 280;
  const DEFAULT_APPEARANCE = {
    transparency: 90,
    border: "#50cdff",
    background: "#000000",
  };

  const STYLE_ACCENTS = {
    mystic: "#50cdff",
    aether: "#ff8a2b",
    neural: "#5ce1ff",
    apex: "#e8d4a0",
  };

  const STYLE_ORB_DEFAULTS = {
    mystic: {
      calm_color: "#50cdff",
      thinking_color: "#b388ff",
      size: 360,
      spin_speed: 1,
      turbulence: 1,
      pulse: 1,
      glow: 1,
    },
    aether: {
      calm_color: "#ff8a2b",
      thinking_color: "#ffb347",
      size: 360,
      spin_speed: 1,
      turbulence: 1,
      pulse: 1,
      glow: 1,
    },
    neural: {
      calm_color: "#50cdff",
      thinking_color: "#b388ff",
      size: 360,
      spin_speed: 1,
      turbulence: 1,
      pulse: 1,
      glow: 1,
    },
    apex: {
      calm_color: "#e8d4a0",
      thinking_color: "#fff4d6",
      size: 360,
      spin_speed: 1,
      turbulence: 1,
      pulse: 1,
      glow: 1,
    },
  };

  const styleConfigs = {};
  let suppressControlLive = false;

  /* KAN-348 — shared scan keyboard: ↑↓ move focus, Enter detail, Space only on checkbox/radio cell.
     Never confirm Jira / heal / delete / restore / remove from these keys. */
  function onScanRowKeydown(ev, ctx) {
    const key = ev.key;
    const target = ev.target;
    const stopSel = (ctx && ctx.checkboxStop) || "";
    const inCheckbox =
      !!target &&
      ((target.matches &&
        target.matches('input[type="checkbox"], input[type="radio"]')) ||
        (stopSel && target.closest && target.closest(stopSel)));

    if (key === " ") {
      if (inCheckbox) return;
      ev.preventDefault();
      return;
    }
    if (key === "Enter") {
      if (inCheckbox) return;
      ev.preventDefault();
      if (ctx && typeof ctx.activate === "function") ctx.activate(ctx.row);
      return;
    }
    if (key === "ArrowDown" || key === "ArrowUp") {
      ev.preventDefault();
      const rows =
        typeof (ctx && ctx.rows) === "function"
          ? ctx.rows()
          : Array.prototype.slice.call((ctx && ctx.rows) || []);
      if (!rows.length || !ctx.row) return;
      const idx = rows.indexOf(ctx.row);
      if (idx < 0) return;
      const nextIdx =
        key === "ArrowDown"
          ? Math.min(rows.length - 1, idx + 1)
          : Math.max(0, idx - 1);
      const next = rows[nextIdx];
      if (!next || next === ctx.row) return;
      if (typeof ctx.activate === "function") ctx.activate(next);
      if (typeof next.focus === "function") next.focus();
      if (typeof next.scrollIntoView === "function") {
        next.scrollIntoView({ block: "nearest" });
      }
    }
  }

  function focusScanFromDetail(evTarget) {
    if (!evTarget || !evTarget.closest) return false;
    const detail = evTarget.closest('[data-scan-scroll="detail"]');
    if (!detail) return false;
    const host =
      detail.closest('[data-scan-no-outer-scroll="1"]') || detail.parentElement;
    if (!host) return false;
    const scanTable = host.querySelector('table[data-scan-kbd="1"]');
    if (!scanTable) return false;
    const focused = host.querySelector(".is-focus");
    if (focused && typeof focused.focus === "function") {
      focused.focus();
    } else if (typeof scanTable.focus === "function") {
      scanTable.focus();
    }
    return true;
  }

  const node = document.getElementById("orb-config");
  const host = document.getElementById("energy-orb-host");
  const chatPanel = document.getElementById("chat-panel");
  const chatLog = document.getElementById("chat-log");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatSend = document.getElementById("chat-send");
  const chatBusy = document.getElementById("chat-busy");
  const chatBusyLabel = document.getElementById("chat-busy-label");
  const chatBusyElapsed = document.getElementById("chat-busy-elapsed");
  const chatCancel = document.getElementById("chat-cancel");
  let chatBusyTimer = null;
  let chatBusyStartedAt = 0;
  let chatAbort = null;
  let chatInFlight = false;
  const screenDrawer = document.getElementById("screen-drawer");
  const screenToggle = document.getElementById("screen-drawer-toggle");
  const appDrawer = document.getElementById("app-drawer");
  const appToggle = document.getElementById("app-drawer-toggle");
  const orbControls = document.getElementById("orb-controls");
  const widgetSettings = document.getElementById("widget-settings");
  const widgetTransparencyCtrl = document.getElementById("ctrl-widget-transparency");
  const widgetBorderCtrl = document.getElementById("ctrl-widget-border");
  const widgetBgCtrl = document.getElementById("ctrl-widget-bg");

  const ctrls = {
    style: document.getElementById("ctrl-style"),
    calm: document.getElementById("ctrl-calm"),
    thinking: document.getElementById("ctrl-thinking"),
    size: document.getElementById("ctrl-size"),
    spin: document.getElementById("ctrl-spin"),
    turbulence: document.getElementById("ctrl-turbulence"),
    pulse: document.getElementById("ctrl-pulse"),
    glow: document.getElementById("ctrl-glow"),
  };

  const toggleDrawerMap = new Map([
    [appToggle, appDrawer],
    [screenToggle, screenDrawer],
  ]);

  function setOrbSizeVar(size) {
    document.documentElement.style.setProperty("--orb-size", String(size || 360));
  }

  let lastAppliedStyle = null;

  function defaultStyleConfig(style) {
    const base = STYLE_ORB_DEFAULTS[style] || STYLE_ORB_DEFAULTS.mystic;
    return {
      style: style,
      calm_color: base.calm_color,
      thinking_color: base.thinking_color,
      size: base.size,
      shape: "sphere",
      spin_speed: base.spin_speed,
      turbulence: base.turbulence,
      pulse: base.pulse,
      glow: base.glow,
    };
  }

  function orbConfigFromApi(raw) {
    if (!raw) return null;
    return {
      style: raw.style,
      calm_color: raw.calm_color,
      thinking_color: raw.thinking_color,
      size: parseInt(raw.size, 10) || 360,
      shape: raw.shape || "sphere",
      spin_speed: parseFloat(raw.spin_speed ?? 1),
      turbulence: parseFloat(raw.turbulence ?? 1),
      pulse: parseFloat(raw.pulse ?? 1),
      glow: parseFloat(raw.glow ?? 1),
    };
  }

  function loadStyleConfigs() {
    WEBGL_STYLES.forEach(function (s) {
      styleConfigs[s] = defaultStyleConfig(s);
    });
    let activeStyle = "mystic";
    try {
      const raw = localStorage.getItem(ORB_STYLES_KEY);
      if (!raw) return activeStyle;
      const parsed = JSON.parse(raw);
      WEBGL_STYLES.forEach(function (s) {
        if (parsed[s] && typeof parsed[s] === "object") {
          styleConfigs[s] = Object.assign(defaultStyleConfig(s), parsed[s], { style: s });
        }
      });
      if (WEBGL_STYLES.includes(parsed.activeStyle)) {
        activeStyle = parsed.activeStyle;
      }
    } catch (err) {
      console.warn("orb style store load failed", err);
    }
    return activeStyle;
  }

  function saveStyleConfigs(activeStyle) {
    try {
      const payload = { activeStyle: activeStyle };
      WEBGL_STYLES.forEach(function (s) {
        payload[s] = styleConfigs[s] || defaultStyleConfig(s);
      });
      localStorage.setItem(ORB_STYLES_KEY, JSON.stringify(payload));
    } catch (err) {
      console.warn("orb style store save failed", err);
    }
  }

  function captureFromControls() {
    return {
      style: ctrls.style.value,
      calm_color: ctrls.calm.value,
      thinking_color: ctrls.thinking.value,
      size: parseInt(ctrls.size.value, 10),
      shape: "sphere",
      spin_speed: parseFloat(ctrls.spin.value),
      turbulence: parseFloat(ctrls.turbulence.value),
      pulse: parseFloat(ctrls.pulse.value),
      glow: parseFloat(ctrls.glow.value),
    };
  }

  function applyControlsFromConfig(cfg) {
    if (!cfg) return;
    suppressControlLive = true;
    ctrls.style.value = cfg.style || "mystic";
    ctrls.calm.value = cfg.calm_color || STYLE_ORB_DEFAULTS.mystic.calm_color;
    ctrls.thinking.value = cfg.thinking_color || STYLE_ORB_DEFAULTS.mystic.thinking_color;
    ctrls.size.value = String(cfg.size ?? 360);
    ctrls.spin.value = String(cfg.spin_speed ?? 1);
    ctrls.turbulence.value = String(cfg.turbulence ?? 1);
    ctrls.pulse.value = String(cfg.pulse ?? 1);
    ctrls.glow.value = String(cfg.glow ?? 1);
    suppressControlLive = false;
  }

  function applyConfigToNode(cfg) {
    if (!node || !cfg) return;
    const style = cfg.style || "mystic";
    node.setAttribute("data-style", style);
    document.documentElement.setAttribute("data-style", style);
    node.setAttribute("data-calm-color", cfg.calm_color || "#50cdff");
    node.setAttribute("data-thinking-color", cfg.thinking_color || "#b388ff");
    node.setAttribute("data-size", String(cfg.size || 360));
    node.setAttribute("data-shape", cfg.shape || "sphere");
    node.setAttribute("data-spin-speed", String(cfg.spin_speed ?? 1));
    node.setAttribute("data-turbulence", String(cfg.turbulence ?? 1));
    node.setAttribute("data-pulse", String(cfg.pulse ?? 1));
    node.setAttribute("data-glow", String(cfg.glow ?? 1));
    setOrbSizeVar(cfg.size || 360);
    if (lastAppliedStyle !== null && style !== lastAppliedStyle) {
      layout.appearance = applyStyleTheme(style, layout.appearance);
      saveLayout(layout);
    }
    lastAppliedStyle = style;
  }

  function syncControlsFromNode() {
    if (!node) return;
    ctrls.style.value = node.getAttribute("data-style") || "mystic";
    ctrls.calm.value = node.getAttribute("data-calm-color") || "#50cdff";
    ctrls.thinking.value = node.getAttribute("data-thinking-color") || "#b388ff";
    ctrls.size.value = node.getAttribute("data-size") || "360";
    ctrls.spin.value = node.getAttribute("data-spin-speed") || "1";
    ctrls.turbulence.value = node.getAttribute("data-turbulence") || "1";
    ctrls.pulse.value = node.getAttribute("data-pulse") || "1";
    ctrls.glow.value = node.getAttribute("data-glow") || "1";
    setOrbSizeVar(parseInt(ctrls.size.value, 10));
  }

  function liveFromControls() {
    if (suppressControlLive) return;
    const curStyle = ctrls.style.value;
    if (lastAppliedStyle !== null && curStyle !== lastAppliedStyle) {
      styleConfigs[lastAppliedStyle] = Object.assign(
        { style: lastAppliedStyle },
        captureFromControls(),
        { style: lastAppliedStyle }
      );
      const next = styleConfigs[curStyle] || defaultStyleConfig(curStyle);
      applyControlsFromConfig(next);
    }
    const cfg = captureFromControls();
    styleConfigs[curStyle] = Object.assign({}, cfg, { style: curStyle });
    saveStyleConfigs(curStyle);
    applyConfigToNode(cfg);
  }

  Object.values(ctrls).forEach(function (el) {
    el.addEventListener("input", liveFromControls);
    el.addEventListener("change", liveFromControls);
  });

  document.getElementById("ctrl-save").addEventListener("click", async function () {
    liveFromControls();
    const body = captureFromControls();
    try {
      await fetch("/api/orb", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (err) {
      console.warn("orb save failed", err);
    }
  });

  function appendMsg(who, text, opts) {
    const row = document.createElement("div");
    const kind = (opts && opts.kind) || who;
    row.className = "msg " + kind;
    const label = document.createElement("span");
    label.className = "who";
    label.textContent =
      kind === "user" ? "You" : kind === "error" ? "Error" : "Agent";
    const body = document.createElement("div");
    body.textContent = text;
    row.appendChild(label);
    row.appendChild(body);
    chatLog.appendChild(row);
    chatLog.scrollTop = chatLog.scrollHeight;
    return row;
  }

  function busyLabelForElapsed(seconds) {
    if (seconds >= 60) return "Long run still going — drawers stay usable";
    if (seconds >= 15) return "Long run in progress…";
    if (seconds >= 5) return "Still working…";
    return "Working…";
  }

  function formatElapsed(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? m + "m " + String(s).padStart(2, "0") + "s" : s + "s";
  }

  function setChatBusy(on) {
    chatInFlight = !!on;
    if (chatBusy) {
      chatBusy.hidden = !on;
      chatBusy.dataset.busy = on ? "true" : "false";
    }
    if (chatForm) chatForm.classList.toggle("is-busy", !!on);
    if (chatSend) chatSend.disabled = !!on;
    if (chatInput) chatInput.disabled = !!on;
    if (chatBusyTimer) {
      clearInterval(chatBusyTimer);
      chatBusyTimer = null;
    }
    if (!on) {
      if (chatBusyLabel) chatBusyLabel.textContent = "Working…";
      if (chatBusyElapsed) chatBusyElapsed.textContent = "";
      window.__energyOrbMode = "calm";
      return;
    }
    chatBusyStartedAt = Date.now();
    window.__energyOrbMode = "thinking";
    const tick = function () {
      const seconds = Math.max(0, Math.floor((Date.now() - chatBusyStartedAt) / 1000));
      if (chatBusyLabel) chatBusyLabel.textContent = busyLabelForElapsed(seconds);
      if (chatBusyElapsed) chatBusyElapsed.textContent = formatElapsed(seconds);
    };
    tick();
    chatBusyTimer = setInterval(tick, 1000);
  }

  function cancelChatRequest() {
    if (!chatInFlight || !chatAbort) return;
    chatAbort.abort();
  }

  if (chatCancel) {
    chatCancel.addEventListener("click", function (ev) {
      ev.preventDefault();
      cancelChatRequest();
    });
  }

  chatForm.addEventListener("submit", async function (ev) {
    ev.preventDefault();
    if (chatInFlight) return;
    const message = (chatInput.value || "").trim();
    if (!message) return;
    chatInput.value = "";
    appendMsg("user", message);
    chatAbort = typeof AbortController !== "undefined" ? new AbortController() : null;
    setChatBusy(true);
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, session_id: "desktop" }),
        signal: chatAbort ? chatAbort.signal : undefined,
      });
      let data = null;
      try {
        data = await res.json();
      } catch (_parseErr) {
        data = null;
      }
      if (!res.ok) {
        const detail =
          (data && (data.reply || data.error || data.detail)) ||
          ("HTTP " + res.status + " from /chat");
        appendMsg("agent", String(detail), { kind: "error" });
        return;
      }
      const reply = (data && data.reply) || "";
      const failed = data && data.ok === false;
      if (failed || !reply) {
        appendMsg(
          "agent",
          reply || (data && data.error) || "Agent returned no reply.",
          { kind: "error" }
        );
        return;
      }
      appendMsg("agent", reply);
    } catch (err) {
      if (err && err.name === "AbortError") {
        appendMsg("agent", "Cancelled — stopped waiting for the agent reply.");
      } else {
        appendMsg(
          "agent",
          "Could not reach the local agent. Is the server running?",
          { kind: "error" }
        );
      }
    } finally {
      chatAbort = null;
      setChatBusy(false);
    }
  });

  function currentDrawerSize(drawer, edge) {
    const raw = drawer.style.getPropertyValue("--drawer-size");
    return parseFloat(raw) || defaultDrawerSize(edge);
  }

  function isCompactAppMenu(drawer) {
    return !!(drawer && drawer === appDrawer && drawer.dataset.compactAppMenu === "1");
  }

  function positionAppMenuPanel() {
    /* Gradio-style ▦ popover — fixed card beside the toggle (KAN-253 / KAN-256). */
    if (!appDrawer || !appToggle) return;
    const edge = appToggle.dataset.edge || "left";
    const tr = appToggle.getBoundingClientRect();
    const W = window.innerWidth;
    const H = window.innerHeight;
    const panelW = Math.min(260, W - 24);
    const gap = 8;
    clearPos(appDrawer);
    appDrawer.style.width = "";
    appDrawer.style.height = "";
    appDrawer.style.bottom = "";
    appDrawer.style.right = "";
    appDrawer.style.setProperty("--drawer-size", "");
    appDrawer.classList.remove("edge-left", "edge-right", "edge-top", "edge-bottom", "side-drawer");
    appDrawer.style.width = panelW + "px";
    appDrawer.style.maxHeight = Math.min(H - 24, 560) + "px";
    /* Prefer drop-down under/ beside the button like Gradio #app-menu-panel. */
    if (edge === "left") {
      appDrawer.style.left = clamp(tr.left, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.bottom + gap, 12, Math.max(12, H - 80)) + "px";
      return;
    }
    if (edge === "right") {
      appDrawer.style.left = clamp(tr.right - panelW, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.bottom + gap, 12, Math.max(12, H - 80)) + "px";
      return;
    }
    if (edge === "top") {
      appDrawer.style.left = clamp(tr.left, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.bottom + gap, 12, Math.max(12, H - 80)) + "px";
      return;
    }
    appDrawer.style.left = clamp(tr.left, 12, Math.max(12, W - panelW - 12)) + "px";
    appDrawer.style.top = clamp(tr.top - gap - 8, 12, Math.max(12, H - 80)) + "px";
  }

  function parkToggleOnOpenDrawer(toggle, drawer) {
    /* Keep the edge toggle as a seam tab so it cannot cover Screen nav (KAN-101 / KAN-113). */
    if (!toggle || !drawer || !drawer.classList.contains("open")) return;
    if (isCompactAppMenu(drawer)) {
      positionAppMenuPanel();
      return;
    }
    const edge = toggle.dataset.edge || "left";
    const size = currentDrawerSize(drawer, edge);
    const W = window.innerWidth;
    const H = window.innerHeight;
    const drawerTop = parseFloat(drawer.style.top);
    const drawerLeft = parseFloat(drawer.style.left);
    clearPos(toggle);
    toggle.dataset.edge = edge;
    toggle.classList.add("edge-snap", "drawer-open-tab");

    if (edge === "left" || edge === "right") {
      const topBase = Number.isFinite(drawerTop) ? drawerTop : 24;
      /* Mid-seam, below the title row, so Settings is never under the tab. */
      const top = clamp(topBase + 72, EDGE_PAD, H - EDGE_PAD - BTN);
      if (edge === "left") {
        toggle.style.left = size + 6 + "px";
        toggle.style.top = top + "px";
      } else {
        toggle.style.right = size + 6 + "px";
        toggle.style.top = top + "px";
      }
      return;
    }
    if (edge === "top") {
      const left = clamp(
        (Number.isFinite(drawerLeft) ? drawerLeft : 72) + 10,
        EDGE_PAD,
        W - EDGE_PAD - BTN
      );
      toggle.style.left = left + "px";
      toggle.style.top = size + 6 + "px";
      return;
    }
    const left = clamp(
      (Number.isFinite(drawerLeft) ? drawerLeft : 72) + 10,
      EDGE_PAD,
      W - EDGE_PAD - BTN
    );
    toggle.style.left = left + "px";
    toggle.style.bottom = size + 6 + "px";
  }

  function restoreTogglePlacement(toggle) {
    if (!toggle) return;
    toggle.classList.remove("drawer-open-tab");
    const saved = layout.toggles && layout.toggles[toggle.id];
    const edge =
      (saved && saved.edge) ||
      toggle.dataset.edge ||
      toggle.getAttribute("data-default-edge") ||
      "left";
    const along = saved && typeof saved.along === "number" ? saved.along : null;
    placeToggle(toggle, edge, along);
  }

  function setDrawer(drawer, toggle, open) {
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (drawer === appDrawer) {
      document.documentElement.classList.toggle("drawer-app-open", open);
    } else if (drawer === screenDrawer) {
      document.documentElement.classList.toggle("drawer-screen-open", open);
    }
    if (isCompactAppMenu(drawer)) {
      if (open) {
        positionAppMenuPanel();
      } else {
        restoreTogglePlacement(toggle);
      }
      return;
    }
    if (open) {
      syncDrawerEdge(toggle, drawer);
      parkToggleOnOpenDrawer(toggle, drawer);
    } else {
      restoreTogglePlacement(toggle);
      syncDrawerEdge(toggle, drawer);
    }
  }

  function closeOther(which) {
    if (which !== "screen") setDrawer(screenDrawer, screenToggle, false);
    if (which !== "app") setDrawer(appDrawer, appToggle, false);
  }

  function toggleDrawerFor(toggle) {
    const drawer = toggleDrawerMap.get(toggle);
    if (!drawer) return;
    const which = toggle === screenToggle ? "screen" : "app";
    const open = !drawer.classList.contains("open");
    if (open) closeOther(which);
    setDrawer(drawer, toggle, open);
  }

  function setPanelVisible(panel, btn, show) {
    if (!panel) return;
    if (show) panel.removeAttribute("hidden");
    else panel.setAttribute("hidden", "");
    if (btn) btn.classList.toggle("active", show);
  }

  screenDrawer.querySelectorAll("[data-action]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const action = btn.getAttribute("data-action");
      if (action === "toggle-chat") {
        chatPanel.classList.toggle("hidden");
        btn.classList.toggle("active", !chatPanel.classList.contains("hidden"));
      } else if (action === "toggle-orb") {
        const show = orbControls.hasAttribute("hidden");
        setPanelVisible(orbControls, btn, show);
        if (show) setPanelVisible(widgetSettings, screenDrawer.querySelector('[data-action="toggle-widget-settings"]'), false);
      } else if (action === "toggle-widget-settings") {
        const show = widgetSettings.hasAttribute("hidden");
        setPanelVisible(widgetSettings, btn, show);
        if (show) setPanelVisible(orbControls, screenDrawer.querySelector('[data-action="toggle-orb"]'), false);
      }
    });
  });

  /* ---- layout persistence ---- */

  function normalizeHex(value, fallback) {
    const raw = String(value || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(raw)) return raw.toLowerCase();
    if (/^[0-9a-fA-F]{6}$/.test(raw)) return "#" + raw.toLowerCase();
    return fallback;
  }

  function hexToRgb(hex) {
    const h = normalizeHex(hex, "#000000").slice(1);
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
    };
  }

  function defaultAppearance() {
    return {
      transparency: DEFAULT_APPEARANCE.transparency,
      border: DEFAULT_APPEARANCE.border,
      background: DEFAULT_APPEARANCE.background,
    };
  }

  function normalizeAppearance(raw) {
    const base = defaultAppearance();
    const src = raw && typeof raw === "object" ? raw : {};
    const transparency = Math.max(
      0,
      Math.min(95, Math.round(Number(src.transparency != null ? src.transparency : base.transparency) || 0))
    );
    return {
      transparency: transparency,
      border: normalizeHex(src.border, base.border),
      background: normalizeHex(src.background, base.background),
    };
  }

  function loadLayout() {
    try {
      const raw = localStorage.getItem(LAYOUT_KEY);
      if (!raw) {
        return { toggles: {}, widgets: {}, drawers: {}, appearance: defaultAppearance() };
      }
      const data = JSON.parse(raw);
      const appearanceSrc = data.appearance || {
        transparency:
          typeof data.widgetTransparency === "number"
            ? data.widgetTransparency
            : DEFAULT_APPEARANCE.transparency,
        border: DEFAULT_APPEARANCE.border,
        background: DEFAULT_APPEARANCE.background,
      };
      return {
        toggles: data.toggles || {},
        widgets: data.widgets || {},
        drawers: data.drawers || {},
        appearance: normalizeAppearance(appearanceSrc),
      };
    } catch (err) {
      return { toggles: {}, widgets: {}, drawers: {}, appearance: defaultAppearance() };
    }
  }

  function accentForStyle(style) {
    return STYLE_ACCENTS[style] || STYLE_ACCENTS.mystic;
  }

  function applyAccentVars(hex) {
    const c = hexToRgb(normalizeHex(hex, DEFAULT_APPEARANCE.border));
    const root = document.documentElement;
    const accent = normalizeHex(hex, DEFAULT_APPEARANCE.border);
    root.style.setProperty("--cyan", accent);
    root.style.setProperty(
      "--cyan-dim",
      "rgba(" + c.r + ", " + c.g + ", " + c.b + ", 0.22)"
    );
    root.style.setProperty(
      "--accent-soft",
      "rgba(" + c.r + ", " + c.g + ", " + c.b + ", 0.12)"
    );
    root.style.setProperty(
      "--accent-soft-2",
      "rgba(" + c.r + ", " + c.g + ", " + c.b + ", 0.18)"
    );
    const tr = Math.round(c.r + (255 - c.r) * 0.86);
    const tg = Math.round(c.g + (255 - c.g) * 0.86);
    const tb = Math.round(c.b + (255 - c.b) * 0.86);
    root.style.setProperty("--text", "rgb(" + tr + ", " + tg + ", " + tb + ")");
    root.style.setProperty(
      "--muted",
      "rgba(" + c.r + ", " + c.g + ", " + c.b + ", 0.62)"
    );
  }

  function applyStyleTheme(style, appearance) {
    const accent = accentForStyle(style);
    const base = normalizeAppearance(appearance || (layout && layout.appearance) || defaultAppearance());
    return applyAppearance({
      transparency: base.transparency,
      border: accent,
      background: base.background,
    });
  }

  function applyAppearance(appearance) {
    const next = normalizeAppearance(appearance);
    const alpha = (100 - next.transparency) / 100;
    const bg = hexToRgb(next.background);
    const border = hexToRgb(next.border);
    const root = document.documentElement;
    applyAccentVars(next.border);
    root.style.setProperty(
      "--shell-fill",
      "rgba(" + bg.r + ", " + bg.g + ", " + bg.b + ", " + alpha + ")"
    );
    root.style.setProperty(
      "--shell-border",
      "rgba(" + border.r + ", " + border.g + ", " + border.b + ", 0.28)"
    );
    root.style.setProperty(
      "--shell-glow",
      "0 0 6px rgba(" +
        border.r +
        ", " +
        border.g +
        ", " +
        border.b +
        ", 0.28), 0 0 18px rgba(" +
        border.r +
        ", " +
        border.g +
        ", " +
        border.b +
        ", 0.1)"
    );
    root.style.setProperty(
      "--cyan-border",
      "rgba(" + border.r + ", " + border.g + ", " + border.b + ", 0.28)"
    );
    root.style.setProperty(
      "--glow",
      "0 0 6px rgba(" +
        border.r +
        ", " +
        border.g +
        ", " +
        border.b +
        ", 0.28), 0 0 18px rgba(" +
        border.r +
        ", " +
        border.g +
        ", " +
        border.b +
        ", 0.1)"
    );
    if (widgetTransparencyCtrl) widgetTransparencyCtrl.value = String(next.transparency);
    if (widgetBorderCtrl) widgetBorderCtrl.value = next.border;
    if (widgetBgCtrl) widgetBgCtrl.value = next.background;
    return next;
  }

  function persistAppearanceFromControls() {
    layout.appearance = applyAppearance({
      transparency: widgetTransparencyCtrl ? widgetTransparencyCtrl.value : DEFAULT_APPEARANCE.transparency,
      border: widgetBorderCtrl ? widgetBorderCtrl.value : DEFAULT_APPEARANCE.border,
      background: widgetBgCtrl ? widgetBgCtrl.value : DEFAULT_APPEARANCE.background,
    });
    saveLayout(layout);
  }

  function saveLayout(layout) {
    try {
      localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout));
    } catch (err) {
      console.warn("layout save failed", err);
    }
  }

  let layout = loadLayout();

  function clearPos(el) {
    el.style.left = "";
    el.style.right = "";
    el.style.top = "";
    el.style.bottom = "";
    el.style.transform = "";
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  function nearestEdge(cx, cy, W, H) {
    const dists = [
      ["left", cx],
      ["right", W - cx],
      ["top", cy],
      ["bottom", H - cy],
    ];
    dists.sort(function (a, b) {
      return a[1] - b[1];
    });
    return dists[0][0];
  }

  function placeToggle(el, edge, along) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    clearPos(el);
    el.dataset.edge = edge;
    el.classList.add("edge-snap");

    if (edge === "left" || edge === "right") {
      const y = clamp(
        along != null ? along : (H - BTN) / 2,
        EDGE_PAD,
        H - EDGE_PAD - BTN
      );
      el.style.top = y + "px";
      if (edge === "left") el.style.left = EDGE_PAD + "px";
      else el.style.right = EDGE_PAD + "px";
      return { edge: edge, along: y };
    }

    const x = clamp(
      along != null ? along : (W - BTN) / 2,
      EDGE_PAD,
      W - EDGE_PAD - BTN
    );
    el.style.left = x + "px";
    if (edge === "top") el.style.top = EDGE_PAD + "px";
    else el.style.bottom = EDGE_PAD + "px";
    return { edge: edge, along: x };
  }

  function syncDrawerEdge(toggle, drawer) {
    if (isCompactAppMenu(drawer)) {
      if (drawer.classList.contains("open")) positionAppMenuPanel();
      return;
    }
    const edge = toggle.dataset.edge || "left";
    drawer.classList.remove("edge-left", "edge-right", "edge-top", "edge-bottom");
    drawer.classList.add("edge-" + edge);
    clearPos(drawer);

    const tr = toggle.getBoundingClientRect();
    const W = window.innerWidth;
    const H = window.innerHeight;
    const saved = layout.drawers && layout.drawers[drawer.id];
    const size =
      saved && typeof saved.size === "number" ? saved.size : defaultDrawerSize(edge);
    applyDrawerSize(drawer, edge, size);

    if (edge === "left" || edge === "right") {
      const idealTop = clamp(tr.top - 40, 24, Math.max(24, H - 88 - 200));
      drawer.style.top = idealTop + "px";
      drawer.style.bottom = "88px";
      if (edge === "left") drawer.style.left = "0";
      else drawer.style.right = "0";
    } else if (edge === "top") {
      drawer.style.top = "0";
      drawer.style.left = clamp(tr.left - 40, 24, Math.max(24, W - 280)) + "px";
      drawer.style.right = "72px";
    } else {
      drawer.style.bottom = "80px";
      drawer.style.left = clamp(tr.left - 40, 24, Math.max(24, W - 280)) + "px";
      drawer.style.right = "72px";
    }
  }

  function persistToggle(el) {
    const along =
      el.dataset.edge === "left" || el.dataset.edge === "right"
        ? parseFloat(el.style.top) || 0
        : parseFloat(el.style.left) || 0;
    layout.toggles[el.id] = { edge: el.dataset.edge, along: along };
    saveLayout(layout);
  }

  function placeWidget(el, left, top, width, height) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const rect = el.getBoundingClientRect();
    const maxW = Math.max(WIDGET_MIN_W, W - 16);
    const maxH = Math.max(WIDGET_MIN_H, H - 16);
    const w =
      width != null
        ? clamp(width, WIDGET_MIN_W, maxW)
        : rect.width || Math.min(360, Math.floor(W * 0.32));
    const h =
      height != null
        ? clamp(height, WIDGET_MIN_H, maxH)
        : rect.height || Math.min(420, Math.floor(H * 0.55));
    if (width != null) el.style.width = w + "px";
    if (height != null) el.style.height = h + "px";
    const useW = width != null ? w : rect.width || w;
    const useH = height != null ? h : rect.height || h;
    let x = clamp(left, 8, Math.max(8, W - useW - 8));
    const y = clamp(top, 8, Math.max(8, H - useH - 8));
    if (el.id === "chat-panel" || el.dataset.widget === "chat-panel") {
      /* Keep a clear column for the left-edge App toggle (KAN-101 / KAN-113). */
      x = Math.max(x, 64);
    }
    el.style.left = x + "px";
    el.style.top = y + "px";
    el.style.right = "auto";
    el.style.bottom = "auto";
    return { left: x, top: y, width: useW, height: useH };
  }

  function persistWidget(el) {
    const rect = el.getBoundingClientRect();
    layout.widgets[el.dataset.widget || el.id] = {
      left: parseFloat(el.style.left) || rect.left || 0,
      top: parseFloat(el.style.top) || rect.top || 0,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
    };
    saveLayout(layout);
  }

  function defaultDrawerSize(edge) {
    if (edge === "top" || edge === "bottom") {
      return Math.min(DRAWER_DEFAULT_TB, Math.floor(window.innerHeight * 0.42));
    }
    return DRAWER_DEFAULT_LR;
  }

  function applyDrawerSize(drawer, edge, size) {
    const isTB = edge === "top" || edge === "bottom";
    const max = isTB
      ? Math.max(DRAWER_MIN, window.innerHeight - 120)
      : Math.min(DRAWER_MAX_LR, Math.max(DRAWER_MIN, window.innerWidth - 80));
    const next = clamp(
      size != null ? size : defaultDrawerSize(edge),
      DRAWER_MIN,
      max
    );
    drawer.style.setProperty("--drawer-size", next + "px");
    return next;
  }

  function persistDrawer(drawer) {
    if (!drawer || !drawer.id) return;
    const edge = (drawer.className.match(/edge-(left|right|top|bottom)/) || [])[1] || "left";
    const raw = drawer.style.getPropertyValue("--drawer-size");
    const size = parseFloat(raw) || defaultDrawerSize(edge);
    if (!layout.drawers) layout.drawers = {};
    layout.drawers[drawer.id] = { size: size };
    saveLayout(layout);
  }

  function ensureResizeHandles(el) {
    if (el.querySelector(".resize-handle")) return;
    ["e", "s", "se"].forEach(function (dir) {
      const handle = document.createElement("div");
      handle.className = "resize-handle resize-handle-" + dir;
      handle.dataset.resize = dir;
      handle.setAttribute("aria-hidden", "true");
      el.appendChild(handle);
    });
  }

  function ensureDrawerResizeHandle(drawer) {
    if (drawer.querySelector(".drawer-resize-handle")) return;
    const handle = document.createElement("div");
    handle.className = "drawer-resize-handle";
    handle.setAttribute("aria-hidden", "true");
    drawer.appendChild(handle);
  }

  function defaultAlongForToggle(el, edge) {
    const raw = el.getAttribute("data-default-along");
    if (raw != null && raw !== "" && !Number.isNaN(Number(raw))) {
      return Number(raw);
    }
    /* App ▦ defaults near the top (Gradio chrome), Screen stays mid-edge. */
    if (el === appToggle && (edge === "left" || edge === "right")) {
      return 16;
    }
    return null;
  }

  function restoreLayout() {
    /* One-time migrate: old mid-seam App toggle made the menu feel like a tall rail. */
    if (!layout.appMenuCompactV2 && appToggle) {
      layout.appMenuCompactV2 = true;
      const t = layout.toggles && layout.toggles[appToggle.id];
      if (t && typeof t.along === "number" && t.along > 80) {
        t.along = 16;
        t.edge = t.edge || "left";
      }
      if (layout.drawers && layout.drawers["app-drawer"]) {
        delete layout.drawers["app-drawer"];
      }
      saveLayout(layout);
    }
    [appToggle, screenToggle].forEach(function (el) {
      const saved = layout.toggles[el.id];
      const edge = (saved && saved.edge) || el.getAttribute("data-default-edge") || "left";
      const along =
        saved && typeof saved.along === "number"
          ? saved.along
          : defaultAlongForToggle(el, edge);
      placeToggle(el, edge, along);
      const drawer = toggleDrawerMap.get(el);
      if (isCompactAppMenu(drawer)) {
        if (drawer.classList.contains("open")) positionAppMenuPanel();
        return;
      }
      syncDrawerEdge(el, drawer);
      const drawerSaved = layout.drawers && layout.drawers[drawer.id];
      applyDrawerSize(
        drawer,
        edge,
        drawerSaved && typeof drawerSaved.size === "number" ? drawerSaved.size : null
      );
    });

    document.querySelectorAll("[data-widget]").forEach(function (el) {
      ensureResizeHandles(el);
      const key = el.dataset.widget || el.id;
      const saved = layout.widgets[key];
      if (saved && typeof saved.left === "number" && typeof saved.top === "number") {
        placeWidget(
          el,
          saved.left,
          saved.top,
          typeof saved.width === "number" ? saved.width : null,
          typeof saved.height === "number" ? saved.height : null
        );
      }
    });

    const style = (node && node.getAttribute("data-style")) || "mystic";
    lastAppliedStyle = style;
    // Style accent wins on load so shell matches the active orb style.
    layout.appearance = applyStyleTheme(style, layout.appearance || defaultAppearance());
    saveLayout(layout);
  }

  [widgetTransparencyCtrl, widgetBorderCtrl, widgetBgCtrl].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", persistAppearanceFromControls);
    el.addEventListener("change", persistAppearanceFromControls);
  });

  /* ---- edge-snap drag for drawer toggles ---- */

  function bindEdgeSnapToggle(el) {
    let pointerId = null;
    let startX = 0;
    let startY = 0;
    let originLeft = 0;
    let originTop = 0;
    let dragging = false;
    let moved = false;

    el.addEventListener("pointerdown", function (ev) {
      if (ev.button != null && ev.button !== 0) return;
      pointerId = ev.pointerId;
      startX = ev.clientX;
      startY = ev.clientY;
      const rect = el.getBoundingClientRect();
      originLeft = rect.left;
      originTop = rect.top;
      dragging = false;
      moved = false;
      el.classList.remove("edge-snap");
      try {
        el.setPointerCapture(pointerId);
      } catch (err) { /* ignore */ }
      ev.preventDefault();
    });

    el.addEventListener("pointermove", function (ev) {
      if (pointerId == null || ev.pointerId !== pointerId) return;
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (!dragging && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      if (!dragging) {
        dragging = true;
        moved = true;
        el.classList.add("dragging");
        clearPos(el);
        el.style.left = originLeft + "px";
        el.style.top = originTop + "px";
        el.style.right = "auto";
        el.style.bottom = "auto";
      }
      el.style.left = originLeft + dx + "px";
      el.style.top = originTop + dy + "px";
    });

    function endDrag(ev) {
      if (pointerId == null || (ev && ev.pointerId !== pointerId)) return;
      const wasDrag = moved;
      const cx = ev ? ev.clientX : startX;
      const cy = ev ? ev.clientY : startY;
      const dist = Math.hypot(cx - startX, cy - startY);
      pointerId = null;
      el.classList.remove("dragging");

      /* Tiny pointer jitter (incl. Computer Use) should still toggle, not edge-snap. */
      if (wasDrag && dist >= DRAG_THRESHOLD) {
        const W = window.innerWidth;
        const H = window.innerHeight;
        const edge = nearestEdge(cx, cy, W, H);
        let along;
        if (edge === "left" || edge === "right") {
          along = cy - BTN / 2;
        } else {
          along = cx - BTN / 2;
        }
        placeToggle(el, edge, along);
        persistToggle(el);
        const drawer = toggleDrawerMap.get(el);
        syncDrawerEdge(el, drawer);
        if (drawer && drawer.classList.contains("open")) {
          parkToggleOnOpenDrawer(el, drawer);
        }
      } else {
        if (wasDrag) restoreTogglePlacement(el);
        else el.classList.add("edge-snap");
        const drawer = toggleDrawerMap.get(el);
        if (drawer && drawer.classList.contains("open")) {
          parkToggleOnOpenDrawer(el, drawer);
        }
        toggleDrawerFor(el);
      }
    }

    el.addEventListener("pointerup", endDrag);
    el.addEventListener("pointercancel", endDrag);
  }

  /* ---- free drag for widgets (entire surface) ---- */

  function bindWidgetDrag(el) {
    let pointerId = null;
    let startX = 0;
    let startY = 0;
    let originLeft = 0;
    let originTop = 0;
    let dragging = false;

    el.addEventListener("pointerdown", function (ev) {
      if (ev.button != null && ev.button !== 0) return;
      if (el.id === "area-surface" && document.documentElement.getAttribute("data-area-chrome") !== "floating") {
        return;
      }
      if (
        ev.target.closest &&
        ev.target.closest("button, a, input, textarea, select, .resize-handle, .layout-choice")
      ) {
        return;
      }
      pointerId = ev.pointerId;
      startX = ev.clientX;
      startY = ev.clientY;
      const rect = el.getBoundingClientRect();
      originLeft = rect.left;
      originTop = rect.top;
      dragging = false;
    });

    el.addEventListener("pointermove", function (ev) {
      if (pointerId == null || ev.pointerId !== pointerId) return;
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (!dragging && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      if (!dragging) {
        dragging = true;
        el.classList.add("dragging");
        try {
          el.setPointerCapture(pointerId);
        } catch (err) { /* ignore */ }
        window.getSelection && window.getSelection().removeAllRanges();
      }
      placeWidget(el, originLeft + dx, originTop + dy);
      ev.preventDefault();
    });

    function endDrag(ev) {
      if (pointerId == null || (ev && ev.pointerId !== pointerId)) return;
      pointerId = null;
      if (dragging) {
        el.classList.remove("dragging");
        persistWidget(el);
      }
      dragging = false;
    }

    el.addEventListener("pointerup", endDrag);
    el.addEventListener("pointercancel", endDrag);
  }

  /* ---- resize handles for movable widgets ---- */

  function bindWidgetResize(el) {
    ensureResizeHandles(el);
    el.querySelectorAll(".resize-handle").forEach(function (handle) {
      let pointerId = null;
      let startX = 0;
      let startY = 0;
      let originW = 0;
      let originH = 0;
      let originLeft = 0;
      let originTop = 0;
      let dir = "se";

      handle.addEventListener("pointerdown", function (ev) {
        if (ev.button != null && ev.button !== 0) return;
        if (el.id === "area-surface" && document.documentElement.getAttribute("data-area-chrome") !== "floating") {
          return;
        }
        pointerId = ev.pointerId;
        dir = handle.dataset.resize || "se";
        startX = ev.clientX;
        startY = ev.clientY;
        const rect = el.getBoundingClientRect();
        originW = rect.width;
        originH = rect.height;
        originLeft = rect.left;
        originTop = rect.top;
        el.classList.add("resizing");
        try {
          handle.setPointerCapture(pointerId);
        } catch (err) { /* ignore */ }
        ev.preventDefault();
        ev.stopPropagation();
      });

      handle.addEventListener("pointermove", function (ev) {
        if (pointerId == null || ev.pointerId !== pointerId) return;
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;
        let nextW = originW;
        let nextH = originH;
        if (dir.indexOf("e") !== -1) nextW = originW + dx;
        if (dir.indexOf("s") !== -1) nextH = originH + dy;
        placeWidget(el, originLeft, originTop, nextW, nextH);
        ev.preventDefault();
      });

      function endResize(ev) {
        if (pointerId == null || (ev && ev.pointerId !== pointerId)) return;
        pointerId = null;
        el.classList.remove("resizing");
        persistWidget(el);
      }

      handle.addEventListener("pointerup", endResize);
      handle.addEventListener("pointercancel", endResize);
    });
  }

  /* ---- drawer edge resize ---- */

  function bindDrawerResize(drawer) {
    ensureDrawerResizeHandle(drawer);
    const handle = drawer.querySelector(".drawer-resize-handle");
    if (!handle) return;

    let pointerId = null;
    let startPos = 0;
    let originSize = 0;

    handle.addEventListener("pointerdown", function (ev) {
      if (ev.button != null && ev.button !== 0) return;
      if (!drawer.classList.contains("open")) return;
      const edge = (drawer.className.match(/edge-(left|right|top|bottom)/) || [])[1] || "left";
      pointerId = ev.pointerId;
      startPos = edge === "left" || edge === "right" ? ev.clientX : ev.clientY;
      const raw = drawer.style.getPropertyValue("--drawer-size");
      originSize = parseFloat(raw) || defaultDrawerSize(edge);
      drawer.classList.add("resizing");
      try {
        handle.setPointerCapture(pointerId);
      } catch (err) { /* ignore */ }
      ev.preventDefault();
      ev.stopPropagation();
    });

    handle.addEventListener("pointermove", function (ev) {
      if (pointerId == null || ev.pointerId !== pointerId) return;
      const edge = (drawer.className.match(/edge-(left|right|top|bottom)/) || [])[1] || "left";
      let delta = 0;
      if (edge === "left") delta = ev.clientX - startPos;
      else if (edge === "right") delta = startPos - ev.clientX;
      else if (edge === "top") delta = ev.clientY - startPos;
      else delta = startPos - ev.clientY;
      applyDrawerSize(drawer, edge, originSize + delta);
      const toggle =
        drawer === appDrawer ? appToggle : drawer === screenDrawer ? screenToggle : null;
      if (toggle) parkToggleOnOpenDrawer(toggle, drawer);
      ev.preventDefault();
    });

    function endResize(ev) {
      if (pointerId == null || (ev && ev.pointerId !== pointerId)) return;
      pointerId = null;
      drawer.classList.remove("resizing");
      persistDrawer(drawer);
      const toggle =
        drawer === appDrawer ? appToggle : drawer === screenDrawer ? screenToggle : null;
      if (toggle) parkToggleOnOpenDrawer(toggle, drawer);
    }

    handle.addEventListener("pointerup", endResize);
    handle.addEventListener("pointercancel", endResize);
  }

  bindEdgeSnapToggle(appToggle);
  bindEdgeSnapToggle(screenToggle);
  document.querySelectorAll("[data-widget]").forEach(function (el) {
    bindWidgetDrag(el);
    bindWidgetResize(el);
  });
  /* Screen drawer stays resizable; App is a compact menu panel (KAN-253). */
  if (screenDrawer) bindDrawerResize(screenDrawer);

  const settingsSection = document.getElementById("app-section-settings");
  const securitySection = document.getElementById("app-section-security");
  const reportsSection = document.getElementById("app-section-reports");
  const documentsSection = document.getElementById("app-section-documents");
  const healSection = document.getElementById("app-section-heal");
  const desktopSection = document.getElementById("app-section-desktop");
  const suitesSection = document.getElementById("app-section-suites");
  const plansSection = document.getElementById("app-section-plans");
  const manualSection = document.getElementById("app-section-manual");
  const settingsNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="settings"]')
    : null;
  const securityNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="security"]')
    : null;
  const reportsNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="reports"]')
    : null;
  const documentsNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="documents"]')
    : null;
  const healNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="heal"]')
    : null;
  const desktopNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="desktop"]')
    : null;
  const suitesNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="suites"]')
    : null;
  const plansNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="plans"]')
    : null;
  const manualNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="manual"]')
    : null;
  const sandboxesNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="sandboxes"]')
    : null;
  const manualCharter = document.getElementById("manual-charter");
  const manualPlanId = document.getElementById("manual-plan-id");
  const manualCaseId = document.getElementById("manual-case-id");
  const manualStoryKey = document.getElementById("manual-story-key");
  const manualTestKey = document.getElementById("manual-test-key");
  const manualTicketBound = document.getElementById("manual-ticket-bound");
  const manualAssist = document.getElementById("manual-assist");
  const manualMist = document.getElementById("manual-mist");
  const manualStatus = document.getElementById("manual-status");
  const manualClearContext = document.getElementById("manual-clear-context");
  const manualOpenPlans = document.getElementById("manual-open-plans");
  const manualRefreshSessions = document.getElementById("manual-refresh-sessions");
  const manualStart = document.getElementById("manual-start");
  const manualReview = document.getElementById("manual-review");
  const manualReviewOut = document.getElementById("manual-review-out");
  const manualProposeOut = document.getElementById("manual-propose-out");
  const manualConfirmRow = document.getElementById("manual-confirm-row");
  const manualFailureClass = document.getElementById("manual-failure-class");
  const manualExplicitBug = document.getElementById("manual-explicit-bug");
  const manualProposeBug = document.getElementById("manual-propose-bug");
  const manualProposeComment = document.getElementById("manual-propose-comment");
  const manualProposeNote = document.getElementById("manual-propose-note");
  const manualProposeSteps = document.getElementById("manual-propose-steps");
  const manualConfirmYes = document.getElementById("manual-confirm-yes");
  const manualConfirmNo = document.getElementById("manual-confirm-no");
  const manualSessionList = document.getElementById("manual-session-list");
  const manualSessionEmpty = document.getElementById("manual-session-empty");
  const manualLibraryLevel = document.getElementById("manual-library-level");
  const manualLoopStageLabel = document.getElementById("manual-loop-stage-label");
  const manualDetailTitle = document.getElementById("manual-detail-title");
  const manualDetailHint = document.getElementById("manual-detail-hint");
  const manualDetailCharter = document.getElementById("manual-detail-charter");
  const planStartManual = document.getElementById("plan-start-manual");
  const charterFrameRoot = document.getElementById("charter-frame-root");
  const charterFrameRect = document.getElementById("charter-frame-rect");
  const charterFrameMist = charterFrameRoot
    ? charterFrameRoot.querySelector("[data-charter-mist]")
    : null;
  const charterFrameChip = document.getElementById("charter-frame-chip");
  const charterFrameDrag = document.getElementById("charter-frame-drag");
  const charterAssistLive = document.getElementById("charter-assist-live");
  const charterMistLive = document.getElementById("charter-mist-live");
  const charterSnapMonitor = document.getElementById("charter-snap-monitor");
  const charterSnapWindow = document.getElementById("charter-snap-window");
  const charterSnapPicker = document.getElementById("charter-snap-picker");
  const charterSnapPickerTitle = document.getElementById("charter-snap-picker-title");
  const charterSnapPickerList = document.getElementById("charter-snap-picker-list");
  const charterSnapPickerCancel = document.getElementById("charter-snap-picker-cancel");
  const charterNoteInput = document.getElementById("charter-note-input");
  const charterNoteAdd = document.getElementById("charter-note-add");
  const charterStillAdd = document.getElementById("charter-still-add");
  const charterAnnotateStill = document.getElementById("charter-annotate-still");
  const charterPageRefresh = document.getElementById("charter-page-refresh");
  const charterPageContext = document.getElementById("charter-page-context");
  const charterEnd = document.getElementById("charter-end");
  const charterCancel = document.getElementById("charter-cancel");
  const charterDockControls = document.getElementById("charter-dock-controls");
  const charterCancelConfirm = document.getElementById("charter-cancel-confirm");
  const charterCancelYes = document.getElementById("charter-cancel-yes");
  const charterCancelNo = document.getElementById("charter-cancel-no");
  let charterSnapModePending = "";
  let charterSnapLabel = "";
  let manualOpenSessionId = "";
  let manualFocusedSessionId = "";
  let manualLastStillId = "";
  let manualPendingProposalId = "";
  let charterFrameState = { x: 0.18, y: 0.16, w: 0.64, h: 0.58 };
  let charterDragMode = null;
  let charterDragOrigin = null;
  let charterFrameSaveTimer = null;
  let charterOsFloatActive = false;
  const healList = document.getElementById("heal-list");
  const healScanBody = document.getElementById("heal-scan-body");
  const healListEmpty = document.getElementById("heal-list-empty");
  const healStatus = document.getElementById("heal-status");
  const healRefresh = document.getElementById("heal-refresh");
  const healBulkWrap = document.querySelector("[data-heal-bulk]");
  const healBulkApprove = document.getElementById("heal-bulk-approve");
  const healApproveBtn = document.getElementById("heal-approve");
  const healRejectBtn = document.getElementById("heal-reject");
  const healDetailTitle = document.getElementById("heal-detail-title");
  const healDetailHint = document.getElementById("heal-detail-hint");
  const healDetailId = document.getElementById("heal-detail-id");
  const healDetailDiff = document.getElementById("heal-detail-diff");
  let healFocusedId = "";
  let healById = {};
  let healBulkAwaitingConfirm = false;
  const setJiraUrl = document.getElementById("set-jira-url");
  const setJiraProject = document.getElementById("set-jira-project");
  const setOllamaModel = document.getElementById("set-ollama-model");
  const ollamaRefreshBtn = document.getElementById("ollama-refresh-btn");
  const ollamaModelStatus = document.getElementById("ollama-model-status");
  const planIssueKey = document.getElementById("plan-issue-key");
  const planDocName = document.getElementById("plan-doc-name");
  const planDocText = document.getElementById("plan-doc-text");
  const planBatchSize = document.getElementById("plan-batch-size");
  const planDraftBtn = document.getElementById("plan-draft-btn");
  const planDraftProjectBtn = document.getElementById("plan-draft-project-btn");
  const planImportPwBtn = document.getElementById("plan-import-pw-btn");
  const planImportPwAddBtn = document.getElementById("plan-import-pw-add-btn");
  const planAddDesktopBtn = document.getElementById("plan-add-desktop-btn");
  const planAddApiBtn = document.getElementById("plan-add-api-btn");
  const planAddContractBtn = document.getElementById("plan-add-contract-btn");
  const planAddSeedBtn = document.getElementById("plan-add-seed-btn");
  const planAddVisualBtn = document.getElementById("plan-add-visual-btn");
  const planUpdateBaselineBtn = document.getElementById("plan-update-baseline-btn");
  const planAddA11yBtn = document.getElementById("plan-add-a11y-btn");
  const planAddPerfBtn = document.getElementById("plan-add-perf-btn");
  const planFrameworkSelect = document.getElementById("plan-framework-select");
  const planAddFrameworkBtn = document.getElementById("plan-add-framework-btn");
  const planFrameworkRunHint = document.getElementById("plan-framework-run-hint");
  let activeSettingsFramework = "playwright";
  const planPwPath = document.getElementById("plan-pw-path");
  const planRefreshBtn = document.getElementById("plan-refresh-btn");
  const planList = document.getElementById("plan-list");
  const planLoadBtn = document.getElementById("plan-load-btn");
  const planDocAddBtn = document.getElementById("plan-doc-add-btn");
  const planSearchQ = document.getElementById("plan-search-q");
  const planSearchBtn = document.getElementById("plan-search-btn");
  const planSearchResults = document.getElementById("plan-search-results");
  const planIntent = document.getElementById("plan-intent");
  const planCases = document.getElementById("plan-cases");
  const planCasesScanBody = document.getElementById("plan-cases-scan-body");
  const planCasesEmpty = document.getElementById("plan-cases-empty");
  const planCaseDetailTitle = document.getElementById("plan-case-detail-title");
  const planCaseDetailHint = document.getElementById("plan-case-detail-hint");
  const planCaseDetailPane = document.getElementById("plan-case-detail-pane");
  const planCaseDetailLive = document.getElementById("plan-case-detail-live");
  const planCaseUnfocused = document.getElementById("plan-case-unfocused");
  const planCaseDetailPin = document.getElementById("plan-case-detail-pin");
  const planCoverageFilter = document.getElementById("plan-coverage-filter");
  const planCoverageBtn = document.getElementById("plan-coverage-btn");
  const planCoverageNoCase = document.getElementById("plan-coverage-no-case");
  const planCoverageDisabled = document.getElementById("plan-coverage-disabled");
  const planCoverageScanBody = document.getElementById("plan-coverage-scan-body");
  const planCoverageEmpty = document.getElementById("plan-coverage-empty");
  const planCoverageDetailKey = document.getElementById("plan-coverage-detail-key");
  const planCoverageDetailGap = document.getElementById("plan-coverage-detail-gap");
  const planCoverageDetailSummary = document.getElementById(
    "plan-coverage-detail-summary"
  );
  const planDriftCheckBtn = document.getElementById("plan-drift-check-btn");
  const planDriftKeepBtn = document.getElementById("plan-drift-keep-btn");
  const planDriftRefreshBtn = document.getElementById("plan-drift-refresh-btn");
  const planDriftOut = document.getElementById("plan-drift-out");
  const planTraceFilter = document.getElementById("plan-trace-filter");
  const planTraceBtn = document.getElementById("plan-trace-btn");
  const planTraceMatrix = document.getElementById("plan-trace-matrix");
  const planTraceScanBody = document.getElementById("plan-trace-scan-body");
  const planTraceEmpty = document.getElementById("plan-trace-empty");
  const planTraceDetailKey = document.getElementById("plan-trace-detail-key");
  const planTraceDetailCase = document.getElementById("plan-trace-detail-case");
  const planTraceDetailFetch = document.getElementById("plan-trace-detail-fetch");
  const planTraceOpenCase = document.getElementById("plan-trace-open-case");
  const planHistoryBtn = document.getElementById("plan-history-btn");
  const planHistoryList = document.getElementById("plan-history-list");
  const planHistoryScanBody = document.getElementById("plan-history-scan-body");
  const planHistoryEmpty = document.getElementById("plan-history-empty");
  const planHistoryDetailId = document.getElementById("plan-history-detail-id");
  const planHistoryDetailWhen = document.getElementById("plan-history-detail-when");
  const planHistoryDetailMeta = document.getElementById("plan-history-detail-meta");
  const planHistoryA = document.getElementById("plan-history-a");
  const planHistoryB = document.getElementById("plan-history-b");
  const planCompareBtn = document.getElementById("plan-compare-btn");
  const planCompareOut = document.getElementById("plan-compare-out");
  let focusedCoverageKey = "";
  let focusedTraceRow = null;
  let focusedHistoryRunId = "";
  const planCaseId = document.getElementById("plan-case-id");
  const planCaseName = document.getElementById("plan-case-name");
  const planCaseNote = document.getElementById("plan-case-note");
  const planCaseTags = document.getElementById("plan-case-tags");
  const planCasePriority = document.getElementById("plan-case-priority");
  const planCaseStepTimeout = document.getElementById("plan-case-step-timeout");
  const planRunNote = document.getElementById("plan-run-note");
  const planNotesSave = document.getElementById("plan-notes-save");
  const planCaseEnabled = document.getElementById("plan-case-enabled");
  const planCaseArchived = document.getElementById("plan-case-archived");
  const planShowArchived = document.getElementById("plan-show-archived");
  const planFlakeSummary = document.getElementById("plan-flake-summary");
  const planQuarantineReason = document.getElementById("plan-quarantine-reason");
  const planQuarantineExpires = document.getElementById("plan-quarantine-expires");
  const planQuarantineSet = document.getElementById("plan-quarantine-set");
  const planQuarantineClear = document.getElementById("plan-quarantine-clear");
  const planFlakeRefresh = document.getElementById("plan-flake-refresh");
  let openPlanFlakeById = {};
  const planCaseSave = document.getElementById("plan-case-save");
  const planCaseUp = document.getElementById("plan-case-up");
  const planCaseDown = document.getElementById("plan-case-down");
  const planParallelCount = document.getElementById("plan-parallel-count");
  const planEnvActive = document.getElementById("plan-env-active");
  const planEnvActivate = document.getElementById("plan-env-activate");
  const planEnvRefresh = document.getElementById("plan-env-refresh");
  const planEnvStatus = document.getElementById("plan-env-status");
  const planSandboxSelect = document.getElementById("plan-sandbox-select");
  const planSandboxRefresh = document.getElementById("plan-sandbox-refresh");
  const planSandboxStatus = document.getElementById("plan-sandbox-status");
  const planRunTag = document.getElementById("plan-run-tag");
  const planRunByTag = document.getElementById("plan-run-by-tag");
  const planRunTagSmoke = document.getElementById("plan-run-tag-smoke");
  const planRunTagRegression = document.getElementById("plan-run-tag-regression");
  const planTagRunOut = document.getElementById("plan-tag-run-out");
  const planScheduleTag = document.getElementById("plan-schedule-tag");
  const planScheduleTime = document.getElementById("plan-schedule-time");
  const planScheduleSave = document.getElementById("plan-schedule-save");
  const planScheduleClear = document.getElementById("plan-schedule-clear");
  const planScheduleTick = document.getElementById("plan-schedule-tick");
  const planScheduleStatus = document.getElementById("plan-schedule-status");
  const planScheduleOut = document.getElementById("plan-schedule-out");
  const planCaseRun = document.getElementById("plan-case-run");
  const planRerunFailed = document.getElementById("plan-rerun-failed");
  const planRerunOut = document.getElementById("plan-rerun-out");
  const planPauseOnFail = document.getElementById("plan-pause-on-fail");
  const planPauseActions = document.getElementById("plan-pause-actions");
  const planPauseContinue = document.getElementById("plan-pause-continue");
  const planPauseStop = document.getElementById("plan-pause-stop");
  let activePauseId = "";
  const planDefectPreview = document.getElementById("plan-defect-preview");
  const planRunFailureClass = document.getElementById("plan-run-failure-class");
  const planCaseTriageStrip = document.getElementById("plan-case-triage-strip");
  const planTriageHealBadge = document.getElementById("plan-triage-heal-badge");
  const planTriageOpenHeal = document.getElementById("plan-triage-open-heal");
  const planTriageOpenReports = document.getElementById("plan-triage-open-reports");
  const planKnownNote = document.getElementById("plan-known-note");
  const planKnownJira = document.getElementById("plan-known-jira");
  const planKnownSave = document.getElementById("plan-known-save");
  const planKnownClear = document.getElementById("plan-known-clear");
  const planRunFailureSave = document.getElementById("plan-run-failure-save");
  const planCaseDetail = document.getElementById("plan-case-detail");
  const planDefectOut = document.getElementById("plan-defect-out");
  const planDegradedHint = document.getElementById("plan-degraded-hint");
  const planOfflineBanner = document.getElementById("plan-offline-banner");
  const planStatus = document.getElementById("plan-status");
  const planAddCaseToggle = document.getElementById("plan-add-case-toggle");
  const planAddCaseMenu = document.getElementById("plan-add-case-menu");
  const planSectionTabs = document.getElementById("plan-section-tabs");
  let openPlanId = "";
  let openPlanCases = [];
  let lastCaseRunId = "";
  let lastSuiteRunId = "";
  let planOfflineState = null;
  let activePlanPanel = "cases";
  let planDeepViewState = null;

  function closePlanAddCaseMenu() {
    if (planAddCaseMenu) planAddCaseMenu.hidden = true;
    if (planAddCaseToggle) planAddCaseToggle.setAttribute("aria-expanded", "false");
  }

  function showPlanPanel(name) {
    const panelName = name || "cases";
    activePlanPanel = panelName;
    document.querySelectorAll(".plan-panel[data-plan-panel]").forEach(function (panel) {
      const on = panel.getAttribute("data-plan-panel") === panelName;
      panel.hidden = !on;
    });
    document.querySelectorAll(".plan-tab[data-plan-panel]").forEach(function (tab) {
      const on = tab.getAttribute("data-plan-panel") === panelName;
      tab.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (panelName !== "cases") {
      closePlanAddCaseMenu();
      closePlanRunEvidenceDeep();
    }
  }

  if (planSectionTabs) {
    planSectionTabs.addEventListener("click", function (ev) {
      const tab = ev.target && ev.target.closest ? ev.target.closest(".plan-tab[data-plan-panel]") : null;
      if (!tab || !planSectionTabs.contains(tab)) return;
      showPlanPanel(tab.getAttribute("data-plan-panel") || "cases");
    });
  }
  if (planAddCaseToggle && planAddCaseMenu) {
    planAddCaseToggle.addEventListener("click", function () {
      const open = planAddCaseMenu.hidden;
      planAddCaseMenu.hidden = !open;
      planAddCaseToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    planAddCaseMenu.addEventListener("click", function (ev) {
      const item = ev.target && ev.target.closest ? ev.target.closest("[role='menuitem']") : null;
      if (item) closePlanAddCaseMenu();
    });
  }
  showPlanPanel("cases");
  const jiraReadKey = document.getElementById("jira-read-key");
  const jiraReadBtn = document.getElementById("jira-read-btn");
  const jiraReadOut = document.getElementById("jira-read-out");
  const jiraReadStatus = document.getElementById("jira-read-status");
  const setTargetUrl = document.getElementById("set-target-url");
  const setTargetExe = document.getElementById("set-target-exe");
  const setApiEndpoint = document.getElementById("set-api-endpoint");
  const setEnvActive = document.getElementById("set-env-active");
  const setEnvName = document.getElementById("set-env-name");
  const setEnvSave = document.getElementById("set-env-save");
  const setEnvActivate = document.getElementById("set-env-activate");
  const setEnvDelete = document.getElementById("set-env-delete");
  const setEnvDeleteConfirm = document.getElementById("set-env-delete-confirm");
  const setEnvNew = document.getElementById("set-env-new");
  const setEnvScanBody = document.getElementById("set-env-scan-body");
  const setEnvDetailTitle = document.getElementById("set-env-detail-title");
  const setEnvDetail = document.getElementById("set-env-detail");
  const rptDetailTitle = document.getElementById("rpt-detail-title");
  const rptDetailHint = document.getElementById("rpt-detail-hint");
  const envStatus = document.getElementById("env-status");
  const setTestFramework = document.getElementById("set-test-framework");
  const setPlaywrightMode = document.getElementById("set-playwright-mode");
  const setRunFinishNotify = document.getElementById("set-run-finish-notify");
  const setRunNotifyStatus = document.getElementById("set-run-notify-status");
  const runFinishToast = document.getElementById("run-finish-toast");
  let runFinishToastTimer = null;
  const setStorePath = document.getElementById("set-store-path");
  const setCreds = document.getElementById("set-creds");
  const credStatusList = document.getElementById("cred-status-list");
  const credStatusSummary = document.getElementById("cred-status-summary");
  const setTargetSecret = document.getElementById("set-target-secret");
  const credSaveTargetBtn = document.getElementById("cred-save-target-btn");
  const credTestBtn = document.getElementById("cred-test-btn");
  const credTestOut = document.getElementById("cred-test-out");
  const credClearEmailBtn = document.getElementById("cred-clear-email-btn");
  const credClearTokenBtn = document.getElementById("cred-clear-token-btn");
  const credClearTargetBtn = document.getElementById("cred-clear-target-btn");
  const credClearConfirmBtn = document.getElementById("cred-clear-confirm-btn");
  const credStatus = document.getElementById("cred-status");
  let pendingClearKey = "";
  const setSummary = document.getElementById("set-summary");
  const setSave = document.getElementById("set-save");
  const setStatus = document.getElementById("set-status");
  const setSecondPcPack = document.getElementById("set-second-pc-pack");
  const setSecondPcStatus = document.getElementById("set-second-pc-status");
  const connLevel = document.getElementById("conn-level");
  const connHealthBtn = document.getElementById("conn-health-btn");
  const connHealthOut = document.getElementById("conn-health-out");
  const connHealthStatus = document.getElementById("conn-health-status");
  const deskEnabled = document.getElementById("desk-enabled");
  const deskPath = document.getElementById("desk-path");
  const deskExe = document.getElementById("desk-exe");
  const deskSave = document.getElementById("desk-save");
  const deskSmoke = document.getElementById("desk-smoke");
  const deskSteps = document.getElementById("desk-steps");
  const deskStatus = document.getElementById("desk-status");
  const deskScanRow = document.querySelector("#app-section-desktop .desk-scan-row");
  const deskScanStatus = document.getElementById("desk-scan-status");
  const deskLastSmoke = document.getElementById("desk-last-smoke");
  const deskDetail = document.getElementById("desk-detail");
  let deskLastSmokeText = "—";
  const suitePath = document.getElementById("suite-path");
  const suiteDiscover = document.getElementById("suite-discover");
  const suiteListBtn = document.getElementById("suite-list-btn");
  const suiteImport = document.getElementById("suite-import");
  const suiteRun = document.getElementById("suite-run");
  const suiteRunAll = document.getElementById("suite-run-all");
  const suiteStatus = document.getElementById("suite-status");
  let suiteSavedPath = "";
  const suiteList = document.getElementById("suite-list");
  const suiteScanBody = document.getElementById("suite-scan-body");
  const suiteListEmpty = document.getElementById("suite-list-empty");
  const suiteDetailTitle = document.getElementById("suite-detail-title");
  const suiteDetailHint = document.getElementById("suite-detail-hint");
  const suiteDetailName = document.getElementById("suite-detail-name");
  const suiteDetailFile = document.getElementById("suite-detail-file");
  const suiteDetailGrep = document.getElementById("suite-detail-grep");
  const suiteDetailLast = document.getElementById("suite-detail-last");
  const suiteRunFocused = document.getElementById("suite-run-focused");
  const suiteCopyPath = document.getElementById("suite-copy-path");
  let suiteSelected = { test_file: "", grep: "", title: "" };
  const suiteLastByKey = Object.create(null);
  const msEnabled = document.getElementById("ms-enabled");
  const msPlugins = document.getElementById("ms-plugins");
  const msScan = document.getElementById("ms-scan");
  const msScanBody = document.getElementById("ms-scan-body");
  const msDetail = document.getElementById("ms-detail");
  const msDetailTitle = document.getElementById("ms-detail-title");
  const msAction = document.getElementById("ms-action");
  const msId = document.getElementById("ms-id");
  const msLabel = document.getElementById("ms-label");
  const msUrl = document.getElementById("ms-url");
  const msSave = document.getElementById("ms-save");
  const msRun = document.getElementById("ms-run");
  const msUpsert = document.getElementById("ms-upsert");
  const msRemove = document.getElementById("ms-remove");
  const msRemoveConfirm = document.getElementById("ms-remove-confirm");
  const msStatus = document.getElementById("ms-status");
  const sandboxesSection = document.getElementById("app-section-sandboxes");
  let msFocusedId = "";
  let msSandboxCache = [];
  const rptStatus = document.getElementById("rpt-status");
  const rptSectionsStatus = document.getElementById("rpt-sections-status");
  const rptChecks = {
    summary: document.getElementById("rpt-summary"),
    stories: document.getElementById("rpt-stories"),
    bugs: document.getElementById("rpt-bugs"),
    evidence: document.getElementById("rpt-evidence"),
    known_issues: document.getElementById("rpt-known-issues"),
    traceability: document.getElementById("rpt-traceability"),
    documents: document.getElementById("rpt-documents"),
  };
  const rptSave = document.getElementById("rpt-save");
  const rptScanBody = document.getElementById("rpt-scan-body");
  const rptLibraryRefresh = document.getElementById("rpt-library-refresh");
  const rptOpenSettings = document.getElementById("rpt-open-settings");
  const rptEmpty = document.getElementById("rpt-empty");
  const rptViewerTitle = document.getElementById("rpt-viewer-title");
  const rptCharts = document.getElementById("rpt-charts");
  const rptChartsEmpty = document.getElementById("rpt-charts-empty");
  const rptChartsGrid = document.getElementById("rpt-charts-grid");
  const rptChartPassFail = document.getElementById("rpt-chart-pass-fail");
  const rptChartPassFailBody = document.getElementById("rpt-chart-pass-fail-body");
  const rptChartCoverage = document.getElementById("rpt-chart-coverage");
  const rptChartCoverageBody = document.getElementById("rpt-chart-coverage-body");
  const rptChartDuration = document.getElementById("rpt-chart-duration");
  const rptChartDurationBody = document.getElementById("rpt-chart-duration-body");
  const rptChartFailureClasses = document.getElementById("rpt-chart-failure-classes");
  const rptChartFailureClassesBody = document.getElementById(
    "rpt-chart-failure-classes-body"
  );
  const rptChartBugsByStory = document.getElementById("rpt-chart-bugs-by-story");
  const rptChartBugsByStoryBody = document.getElementById("rpt-chart-bugs-by-story-body");
  const rptMarkdown = document.getElementById("rpt-markdown");
  const rptScreenshot = document.getElementById("rpt-screenshot");
  const rptJson = document.getElementById("rpt-json");
  const reportSettingsHeading = document.getElementById("report-settings-heading");
  const rptRunSelect = document.getElementById("rpt-run-select");
  const rptRunRefresh = document.getElementById("rpt-run-refresh");
  const rptExportRun = document.getElementById("rpt-export-run");
  const rptExportPack = document.getElementById("rpt-export-pack");
  let rptSelectedId = "";
  const healRunFilter = document.getElementById("heal-run-filter");
  const appDrawerHint = document.getElementById("app-drawer-hint");
  const secLevel = document.getElementById("sec-level");
  const secProfile = document.getElementById("sec-profile");
  const secPropose = document.getElementById("sec-propose");
  const secConfirm = document.getElementById("sec-confirm");
  const secStatus = document.getElementById("sec-status");
  let pendingSecurityLevel = "";
  const privTelemetry = document.getElementById("priv-telemetry");
  const privInventory = document.getElementById("priv-inventory");
  const privChecks = {
    reports: document.getElementById("priv-reports"),
    screenshots: document.getElementById("priv-screenshots"),
    heal_audit: document.getElementById("priv-heal"),
    sessions: document.getElementById("priv-sessions"),
    uploads: document.getElementById("priv-uploads"),
    local_side_effects_audit: document.getElementById("priv-local-audit"),
    browser_profiles: document.getElementById("priv-profiles"),
  };
  const privPropose = document.getElementById("priv-propose");
  const privConfirm = document.getElementById("priv-confirm");
  const privStatus = document.getElementById("priv-status");
  const localAuditRefresh = document.getElementById("local-audit-refresh");
  const localAuditList = document.getElementById("local-audit-list");
  const localAuditStatus = document.getElementById("local-audit-status");
  const redactionStatusEl = document.getElementById("redaction-status");
  const redactionShotWarn = document.getElementById("redaction-screenshot-warn");
  const backupSummary = document.getElementById("backup-summary");
  const backupIncludeSettings = document.getElementById("backup-include-settings");
  const backupIncludeSecrets = document.getElementById("backup-include-secrets");
  const backupCreate = document.getElementById("backup-create");
  const backupRefresh = document.getElementById("backup-refresh");
  const backupSelect = document.getElementById("backup-select");
  const backupRestorePropose = document.getElementById("backup-restore-propose");
  const backupRestoreConfirm = document.getElementById("backup-restore-confirm");
  const backupStatus = document.getElementById("backup-status");
  let pendingBackupPath = "";
  let pendingPrivacyCategories = null;
  const secPrivacyScanBody = document.getElementById("sec-privacy-scan-body");
  const secBackupScanBody = document.getElementById("sec-backup-scan-body");
  const privDetailTitle = document.getElementById("priv-detail-title");
  const privDetailHint = document.getElementById("priv-detail-hint");
  const secAuditDetailTitle = document.getElementById("sec-audit-detail-title");
  const secAuditDetailHint = document.getElementById("sec-audit-detail-hint");
  const secBackupDetailTitle = document.getElementById("sec-backup-detail-title");
  const secBackupDetailHint = document.getElementById("sec-backup-detail-hint");
  const PRIV_ARTIFACT_LABELS = {
    reports: "Reports",
    screenshots: "Screenshots",
    heal: "Heal audit",
    sessions: "Sessions (chat + Manual this level)",
    uploads: "Uploaded documents",
    "local-audit": "Local side-effects audit",
    profiles: "Browser profiles",
  };

  function setSecuritySection(sectionId) {
    const chosen = sectionId || "privacy";
    document.querySelectorAll(".sec-section-btn[data-sec-section]").forEach(function (btn) {
      if (btn.getAttribute("data-sec-section") === chosen) {
        btn.setAttribute("aria-current", "true");
      } else {
        btn.removeAttribute("aria-current");
      }
    });
    document.querySelectorAll(".sec-section-panel[data-sec-section-panel]").forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-sec-section-panel") !== chosen;
    });
  }

  function focusPrivArtifact(artifactId) {
    const id = artifactId || "reports";
    document.querySelectorAll("#sec-privacy-scan .sec-scan-row").forEach(function (row) {
      if (row.getAttribute("data-priv-artifact") === id) {
        row.classList.add("is-focus");
      } else {
        row.classList.remove("is-focus");
      }
    });
    if (privDetailTitle) {
      privDetailTitle.textContent = PRIV_ARTIFACT_LABELS[id] || id;
    }
    if (privDetailHint) {
      privDetailHint.textContent =
        "Focused artifact. Include cell toggles wipe membership; row click only focuses. Credentials and settings are not deleted here.";
    }
  }

  function focusAuditEntry(summary) {
    if (secAuditDetailTitle) {
      secAuditDetailTitle.textContent = "Entry";
    }
    if (secAuditDetailHint) {
      secAuditDetailHint.textContent =
        summary || "Select a row. Time, action, id, level only — no document bodies.";
    }
  }

  function focusBackupRow(path, label) {
    document.querySelectorAll("#sec-backup-scan .sec-scan-row").forEach(function (row) {
      if (row.getAttribute("data-backup-path") === path) {
        row.classList.add("is-focus");
      } else {
        row.classList.remove("is-focus");
      }
    });
    if (backupSelect && path !== undefined) {
      backupSelect.value = path || "";
    }
    if (secBackupDetailTitle) {
      secBackupDetailTitle.textContent = label || "Restore";
    }
    if (secBackupDetailHint) {
      secBackupDetailHint.textContent = path
        ? "Focused backup. Secrets option stays off by default."
        : "Select a backup row, then Restore… Confirm stays disabled until propose.";
    }
  }
  const docText = document.getElementById("doc-text");
  const docParse = document.getElementById("doc-parse");
  const docProposal = document.getElementById("doc-proposal");
  const docDiff = document.getElementById("doc-diff");
  const docIdeas = document.getElementById("doc-ideas");
  const docConfirm = document.getElementById("doc-confirm");
  const docDecline = document.getElementById("doc-decline");
  const docStatus = document.getElementById("doc-status");
  const docUploadsRefresh = document.getElementById("doc-uploads-refresh");
  const docUploadsBody = document.getElementById("doc-uploads-body");
  const docDetailKey = document.getElementById("doc-detail-key");
  const docDetailHint = document.getElementById("doc-detail-hint");
  const docUploadDetailName = document.getElementById("doc-upload-detail-name");
  const docUploadDetailHint = document.getElementById("doc-upload-detail-hint");
  let docProposalId = "";
  let docFocusedKey = "";
  let docFocusedUpload = "";

  function showDocPanel(name) {
    const panel = name || "propose";
    document.querySelectorAll(".doc-tab").forEach(function (btn) {
      const on = btn.getAttribute("data-doc-panel") === panel;
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    document.querySelectorAll(".doc-panel").forEach(function (el) {
      el.hidden = el.getAttribute("data-doc-panel") !== panel;
    });
    // KAN-352: Propose = Parse; Uploads = Refresh (toolbar follows the tab).
    document.querySelectorAll("#doc-chrome-toolbar [data-show]").forEach(function (el) {
      el.hidden = el.getAttribute("data-show") !== panel;
    });
  }

  document.querySelectorAll(".doc-tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      showDocPanel(btn.getAttribute("data-doc-panel") || "propose");
    });
  });

  function focusDocDiffKey(key, entry) {
    docFocusedKey = key || "";
    if (docDetailKey) docDetailKey.value = key || "";
    if (docDetailHint) {
      if (!key) {
        docDetailHint.textContent =
          "Keep is a dedicated checkbox cell. Row click focuses the change. Confirm writes only checked keys after the existing confirm step. Decline writes nothing.";
      } else {
        const from = (entry && entry.from) || "(empty)";
        const to = (entry && entry.to) || "";
        docDetailHint.textContent = from + " → " + to;
      }
    }
    if (docDiff) {
      docDiff.querySelectorAll(".doc-scan-row").forEach(function (tr) {
        tr.classList.toggle("is-focus", tr.getAttribute("data-key") === key);
      });
    }
  }

  function focusDocUpload(row) {
    const name = (row && row.filename) || "";
    docFocusedUpload = name;
    if (docUploadDetailName) docUploadDetailName.value = name || "";
    if (docUploadDetailHint) {
      if (!row) {
        docUploadDetailHint.textContent =
          "Name, time, level, consent only. No document body in the list. Delete stays on Security → Privacy.";
      } else {
        docUploadDetailHint.textContent =
          (row.uploaded_at || "") +
          " · " +
          (row.security_level || "?") +
          " · consent " +
          (row.consent ? "yes" : "no");
      }
    }
    if (docUploadsBody) {
      docUploadsBody.querySelectorAll(".doc-scan-row").forEach(function (tr) {
        tr.classList.toggle(
          "is-focus",
          tr.getAttribute("data-filename") === name
        );
      });
    }
  }

  async function loadDocUploads() {
    if (!docUploadsBody) return;
    try {
      const res = await fetch("/api/doc-uploads");
      const data = await res.json();
      docUploadsBody.innerHTML = "";
      const rows = (data && data.uploads) || [];
      if (!rows.length) {
        focusDocUpload(null);
        return;
      }
      let first = null;
      rows.forEach(function (row) {
        const tr = document.createElement("tr");
        tr.className = "doc-scan-row";
        tr.setAttribute("data-filename", row.filename || "");
        tr.tabIndex = 0;
        const tdName = document.createElement("td");
        tdName.textContent = row.filename || "upload";
        const tdTime = document.createElement("td");
        tdTime.textContent = row.uploaded_at || "";
        const tdLevel = document.createElement("td");
        tdLevel.textContent = row.security_level || "?";
        const tdConsent = document.createElement("td");
        tdConsent.textContent = row.consent ? "Yes" : "No";
        tr.appendChild(tdName);
        tr.appendChild(tdTime);
        tr.appendChild(tdLevel);
        tr.appendChild(tdConsent);
        tr.addEventListener("click", function () {
          focusDocUpload(row);
        });
        tr.addEventListener("keydown", function (ev) {
          onScanRowKeydown(ev, {
            row: tr,
            rows: function () {
              return Array.prototype.slice.call(
                docUploadsBody.querySelectorAll(".doc-scan-row")
              );
            },
            activate: function (rowEl) {
              const name = rowEl.getAttribute("data-filename") || "";
              const match = rows.find(function (x) {
                return (x.filename || "") === name;
              });
              focusDocUpload(match || null);
            },
          });
        });
        docUploadsBody.appendChild(tr);
        if (!first) first = row;
      });
      const keep =
        rows.find(function (r) {
          return (r.filename || "") === docFocusedUpload;
        }) || first;
      focusDocUpload(keep);
    } catch (err) {
      docUploadsBody.innerHTML = "";
      focusDocUpload(null);
      if (docUploadDetailHint) {
        docUploadDetailHint.textContent = "Could not load uploads.";
      }
    }
  }

  function applyReportSections(flags) {
    Object.keys(rptChecks).forEach(function (key) {
      if (rptChecks[key]) rptChecks[key].checked = !!flags[key];
    });
    syncReportBlockPills();
  }

  async function loadReportSections() {
    try {
      const res = await fetch("/api/report-sections");
      if (!res.ok) return;
      applyReportSections(await res.json());
    } catch (err) {
      /* keep checkbox defaults */
    }
  }

  function reportSectionBody() {
    return {
      summary: !!(rptChecks.summary && rptChecks.summary.checked),
      stories: !!(rptChecks.stories && rptChecks.stories.checked),
      bugs: !!(rptChecks.bugs && rptChecks.bugs.checked),
      evidence: !!(rptChecks.evidence && rptChecks.evidence.checked),
      known_issues: !!(rptChecks.known_issues && rptChecks.known_issues.checked),
      traceability: !!(rptChecks.traceability && rptChecks.traceability.checked),
      documents: !!(rptChecks.documents && rptChecks.documents.checked),
    };
  }

  function fillRunSelect(selectEl, runs, emptyLabel) {
    if (!selectEl) return;
    const previous = selectEl.value || "";
    selectEl.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = emptyLabel || "— select a run —";
    selectEl.appendChild(blank);
    (runs || []).forEach(function (row) {
      const opt = document.createElement("option");
      opt.value = [row.plan_id, row.case_id, row.run_id].join("|");
      opt.textContent = row.label || row.run_id;
      opt.dataset.planId = row.plan_id || "";
      opt.dataset.caseId = row.case_id || "";
      opt.dataset.runId = row.run_id || "";
      selectEl.appendChild(opt);
    });
    if (previous) {
      selectEl.value = previous;
      if (selectEl.value !== previous) selectEl.value = "";
    }
  }

  async function loadExportableRuns() {
    try {
      const res = await fetch("/api/plans/exportable-runs?limit=50");
      if (!res.ok) return;
      const data = await res.json();
      const runs = (data && data.runs) || [];
      fillRunSelect(rptRunSelect, runs, "— select a run —");
      fillRunSelect(healRunFilter, runs, "All pending");
    } catch (err) {
      /* keep prior options */
    }
  }

  const EVIDENCE_TRACE_NONE =
    "Trace: no Playwright trace for this run.";
  const EVIDENCE_TRACE_CAPTURED =
    "Trace: Playwright trace.zip captured.";
  const EVIDENCE_SHOT_WARN =
    "Screenshot present: pixels are not OCR-redacted automatically. Review the image before sharing.";

  function evidenceFirstRoot(id) {
    return document.getElementById(id);
  }

  function ensureEvidenceTraceActions(root) {
    if (!root) return null;
    let actions = root.querySelector("[data-evidence-trace-actions]");
    if (actions) return actions;
    actions = document.createElement("div");
    actions.className = "evidence-first-trace-actions";
    actions.setAttribute("data-evidence-trace-actions", "1");
    actions.hidden = true;
    const openBtn = document.createElement("button");
    openBtn.type = "button";
    openBtn.className = "save-btn secondary";
    openBtn.setAttribute("data-trace-action", "show_trace");
    openBtn.textContent = "Open Playwright Trace";
    const revealBtn = document.createElement("button");
    revealBtn.type = "button";
    revealBtn.className = "save-btn secondary";
    revealBtn.setAttribute("data-trace-action", "reveal");
    revealBtn.textContent = "Reveal in Explorer";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "save-btn secondary";
    copyBtn.setAttribute("data-trace-action", "copy");
    copyBtn.textContent = "Copy path";
    const status = document.createElement("p");
    status.className = "evidence-first-trace-status";
    status.setAttribute("data-evidence-trace-status", "1");
    status.setAttribute("aria-live", "polite");
    status.hidden = true;
    actions.appendChild(openBtn);
    actions.appendChild(revealBtn);
    actions.appendChild(copyBtn);
    actions.appendChild(status);
    const trace = root.querySelector("[data-evidence-trace]");
    if (trace && trace.parentNode) {
      trace.parentNode.insertBefore(actions, trace.nextSibling);
    } else {
      root.appendChild(actions);
    }
    actions.addEventListener("click", async function (ev) {
      const btn = ev.target && ev.target.closest
        ? ev.target.closest("[data-trace-action]")
        : null;
      if (!btn || !actions.contains(btn)) return;
      const action = btn.getAttribute("data-trace-action") || "";
      const path = String(actions.getAttribute("data-trace-path") || "").trim();
      const statusEl = actions.querySelector("[data-evidence-trace-status]");
      if (!path) {
        if (statusEl) {
          statusEl.hidden = false;
          statusEl.textContent = "No trace path available.";
        }
        return;
      }
      if (action === "copy") {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(path);
          } else {
            const ta = document.createElement("textarea");
            ta.value = path;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
          }
          if (statusEl) {
            statusEl.hidden = false;
            statusEl.textContent = "Copied path.";
          }
        } catch (err) {
          if (statusEl) {
            statusEl.hidden = false;
            statusEl.textContent = "Could not copy path.";
          }
        }
        return;
      }
      if (statusEl) {
        statusEl.hidden = false;
        statusEl.textContent =
          action === "reveal" ? "Revealing…" : "Opening Playwright Trace…";
      }
      try {
        const res = await fetch("/api/playwright-trace/open", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: path, action: action, launch: true }),
        });
        const payload = await res.json().catch(function () {
          return {};
        });
        if (!res.ok) {
          const detail =
            (payload && payload.detail) ||
            "Could not open trace.";
          if (statusEl) {
            statusEl.hidden = false;
            statusEl.textContent = String(detail);
          }
          return;
        }
        if (statusEl) {
          statusEl.hidden = false;
          statusEl.textContent =
            (payload && payload.message) ||
            (action === "reveal"
              ? "Revealed in Explorer."
              : "Opened Playwright Trace.");
        }
      } catch (err) {
        if (statusEl) {
          statusEl.hidden = false;
          statusEl.textContent = "Could not reach open-trace API.";
        }
      }
    });
    return actions;
  }

  function setEvidenceTraceActions(root, tracePath, hasTrace) {
    const actions = ensureEvidenceTraceActions(root);
    if (!actions) return;
    const path = String(tracePath || "").trim();
    const show = !!hasTrace && !!path;
    actions.hidden = !show;
    if (show) {
      actions.setAttribute("data-trace-path", path);
    } else {
      actions.removeAttribute("data-trace-path");
    }
    const statusEl = actions.querySelector("[data-evidence-trace-status]");
    if (statusEl) {
      statusEl.hidden = true;
      statusEl.textContent = "";
    }
    const buttons = actions.querySelectorAll("[data-trace-action]");
    for (let i = 0; i < buttons.length; i++) {
      buttons[i].disabled = !show;
    }
  }

  function hideRunStory(root) {
    if (!root || root.getAttribute("data-run-story") !== "1") return;
    const status = root.querySelector("[data-run-story-status]");
    if (status) {
      status.textContent = "—";
      status.className = "run-story-pill";
    }
    const meta = root.querySelector("[data-run-story-meta]");
    if (meta) meta.textContent = "";
    const steps = root.querySelector("[data-run-story-steps]");
    if (steps) {
      steps.hidden = true;
      steps.innerHTML = "";
    }
    const noSteps = root.querySelector("[data-run-story-no-steps]");
    if (noSteps) noSteps.hidden = true;
    const thumb = root.querySelector("[data-run-story-thumb]");
    if (thumb) {
      thumb.hidden = true;
      thumb.removeAttribute("data-shot-path");
      thumb.removeAttribute("data-focus-step");
    }
    const thumbImg = root.querySelector("[data-run-story-thumb-img]");
    if (thumbImg) {
      thumbImg.removeAttribute("src");
      thumbImg.alt = "Captured page screenshot";
    }
    const noneBox = root.querySelector("[data-run-story-none]");
    if (noneBox) noneBox.hidden = true;
    const entry = root.querySelector("[data-run-story-entry]");
    if (entry) entry.hidden = true;
  }

  function hideEvidenceFirst(root) {
    if (!root) return;
    root.hidden = true;
    hideRunStory(root);
    const summary = root.querySelector("[data-evidence-summary]");
    if (summary) {
      summary.textContent = "—";
      if (root.getAttribute("data-run-story") === "1") summary.hidden = true;
    }
    const links = root.querySelector("[data-evidence-links]");
    if (links) {
      links.hidden = true;
      links.textContent = "";
    }
    const warn = root.querySelector("[data-evidence-shot-warn]");
    if (warn) warn.hidden = true;
    const trace = root.querySelector("[data-evidence-trace]");
    if (trace) trace.textContent = EVIDENCE_TRACE_NONE;
    setEvidenceTraceActions(root, "", false);
  }

  function formatRunStoryStatus(result) {
    const raw = String(result || "pending").toLowerCase();
    if (raw === "pass") return { text: "Pass", kind: "pass" };
    if (raw === "fail") return { text: "Fail", kind: "fail" };
    if (raw === "error") return { text: "Error", kind: "error" };
    return { text: raw || "—", kind: "idle" };
  }

  function formatRunStoryDuration(ms) {
    if (ms == null || ms === "") return "";
    const n = Number(ms);
    if (!Number.isFinite(n)) return "";
    if (n >= 1000) return (Math.round(n / 100) / 10) + "s";
    return Math.round(n) + " ms";
  }

  function ensureRunStoryDeepHandlers(root) {
    if (!root || root.getAttribute("data-run-story-deep-bound") === "1") return;
    root.setAttribute("data-run-story-deep-bound", "1");
    root.addEventListener("click", function (ev) {
      const btn = ev.target && ev.target.closest
        ? ev.target.closest("[data-run-story-open-deep]")
        : null;
      if (!btn || !root.contains(btn) || btn.hidden) return;
      const focusPath = String(btn.getAttribute("data-shot-path") || "").trim();
      const focusStep = Number(btn.getAttribute("data-focus-step") || 0) || null;
      openPlanRunEvidenceDeep({
        focusPath: focusPath,
        focusStep: focusStep,
      });
    });
  }

  function planDeepSurface() {
    return document.getElementById("plan-run-evidence-deep");
  }

  function planCasesPanel() {
    return document.getElementById("plan-panel-cases");
  }

  function closePlanRunEvidenceDeep() {
    const deep = planDeepSurface();
    const panel = planCasesPanel();
    if (deep) deep.hidden = true;
    if (panel) panel.removeAttribute("data-run-evidence-deep-open");
  }

  function shotUrlForDeep(planId, caseId, runId, path) {
    let url =
      "/api/plans/" +
      encodeURIComponent(planId) +
      "/cases/" +
      encodeURIComponent(caseId) +
      "/runs/" +
      encodeURIComponent(runId) +
      "/screenshot?t=" +
      Date.now();
    if (path) url += "&path=" + encodeURIComponent(path);
    return url;
  }

  function focusPlanDeepView(opts) {
    const options = opts || {};
    const state = planDeepViewState;
    const deep = planDeepSurface();
    if (!state || !deep) return;
    const pages = state.pages || [];
    const outcomes = state.outcomes || [];
    let stepIndex = options.stepIndex != null ? Number(options.stepIndex) : null;
    let path = String(options.path || "").trim();

    if (path) {
      const match = pages.find(function (p) {
        return String((p && p.path) || "") === path;
      });
      if (match && match.step_index != null && stepIndex == null) {
        stepIndex = Number(match.step_index) || null;
      }
    } else if (stepIndex != null) {
      const forStep = pages.find(function (p) {
        return Number((p && p.step_index) || 0) === stepIndex;
      });
      path = forStep ? String(forStep.path || "") : "";
    }

    if (stepIndex == null && path) {
      const only = pages[0];
      if (only && only.step_index != null) stepIndex = Number(only.step_index) || null;
    }
    if (stepIndex == null && outcomes.length) {
      const fail = outcomes.find(function (s) {
        const st = String((s && s.status) || "").toLowerCase();
        return st === "fail" || st === "error";
      });
      stepIndex = fail
        ? Number(fail.index) || null
        : Number((outcomes[outcomes.length - 1] || {}).index) || null;
    }

    state.focusStep = stepIndex;
    state.focusPath = path;

    const stepsEl = deep.querySelector("[data-run-deep-steps]");
    if (stepsEl) {
      const buttons = stepsEl.querySelectorAll("[data-run-deep-step]");
      for (let i = 0; i < buttons.length; i++) {
        const btn = buttons[i];
        const idx = Number(btn.getAttribute("data-step-index") || 0) || null;
        const on = stepIndex != null && idx === stepIndex;
        btn.classList.toggle("is-select", on);
        btn.setAttribute("aria-current", on ? "true" : "false");
      }
    }

    const strip = deep.querySelector("[data-run-deep-strip]");
    if (strip) {
      const chips = strip.querySelectorAll("[data-run-deep-chip]");
      for (let i = 0; i < chips.length; i++) {
        const chip = chips[i];
        const chipPath = String(chip.getAttribute("data-shot-path") || "");
        const on = !!path && chipPath === path;
        chip.classList.toggle("is-select", on);
        chip.setAttribute("aria-current", on ? "true" : "false");
      }
    }

    const stageLabel = deep.querySelector("[data-run-deep-stage-label]");
    if (stageLabel) {
      stageLabel.textContent =
        stepIndex != null ? "Evidence · step " + stepIndex : "Evidence";
    }

    const pageBox = deep.querySelector("[data-run-deep-page]");
    const pageImg = deep.querySelector("[data-run-deep-page-img]");
    const noneBox = deep.querySelector("[data-run-deep-none]");
    const noneReason = deep.querySelector("[data-run-deep-none-reason]");
    if (path && pageBox && pageImg && state.planId && state.caseId && state.runId) {
      pageBox.hidden = false;
      if (noneBox) noneBox.hidden = true;
      pageImg.src = shotUrlForDeep(state.planId, state.caseId, state.runId, path);
      pageImg.alt =
        stepIndex != null
          ? "Captured page for step " + stepIndex
          : "Captured page screenshot";
    } else {
      if (pageBox) pageBox.hidden = true;
      if (pageImg) pageImg.removeAttribute("src");
      if (noneBox) {
        noneBox.hidden = false;
        if (noneReason) {
          noneReason.textContent =
            state.emptyReason ||
            "None captured. A green stand-in is not substituted.";
        }
      }
    }
  }

  function fillPlanDeepView(state) {
    const deep = planDeepSurface();
    if (!deep || !state) return;
    const nameEl = deep.querySelector("[data-run-deep-case-name]");
    if (nameEl) nameEl.textContent = state.caseName || "Case";
    const st = formatRunStoryStatus(state.result);
    const statusEl = deep.querySelector("[data-run-deep-status]");
    if (statusEl) {
      statusEl.textContent = st.text;
      statusEl.className =
        "run-story-pill" + (st.kind !== "idle" ? " is-" + st.kind : "");
    }
    const metaEl = deep.querySelector("[data-run-deep-meta]");
    if (metaEl) metaEl.textContent = state.meta || "";

    const traceBtn = deep.querySelector("[data-run-deep-open-trace]");
    if (traceBtn) {
      const hasTrace = !!state.tracePath;
      traceBtn.disabled = !hasTrace;
      if (hasTrace) traceBtn.setAttribute("data-trace-path", state.tracePath);
      else traceBtn.removeAttribute("data-trace-path");
    }

    const stepsEl = deep.querySelector("[data-run-deep-steps]");
    if (stepsEl) {
      stepsEl.innerHTML = "";
      (state.outcomes || []).forEach(function (step) {
        const btn = document.createElement("button");
        btn.type = "button";
        const stepStatus = String((step && step.status) || "").toLowerCase();
        btn.className =
          "plan-deep-step" +
          (stepStatus === "fail" || stepStatus === "error" ? " is-fail" : "");
        btn.setAttribute("data-run-deep-step", "1");
        btn.setAttribute("data-step-index", String((step && step.index) || ""));
        const n = document.createElement("span");
        n.className = "run-story-n";
        n.textContent = String((step && step.index) || "");
        const verb = document.createElement("span");
        verb.className = "run-story-verb";
        verb.textContent = String((step && step.label) || (step && step.action) || "Step");
        const pill = document.createElement("span");
        const ok = stepStatus === "pass";
        const bad = stepStatus === "fail" || stepStatus === "error";
        pill.className =
          "run-story-step-pill" + (ok ? " is-pass" : bad ? " is-fail" : "");
        pill.textContent = ok ? "Pass" : bad ? "Fail" : stepStatus || "—";
        btn.appendChild(n);
        btn.appendChild(verb);
        btn.appendChild(pill);
        const hasShot = (state.pages || []).some(function (p) {
          return Number((p && p.step_index) || 0) === Number(step.index);
        });
        if (step && step.duration_ms != null) {
          const ms = document.createElement("span");
          ms.className = "run-story-ms";
          ms.textContent =
            formatRunStoryDuration(step.duration_ms) + (hasShot ? " · shot" : "");
          btn.appendChild(ms);
        } else if (hasShot) {
          const ms = document.createElement("span");
          ms.className = "run-story-ms";
          ms.textContent = "shot";
          btn.appendChild(ms);
        }
        if (step && step.error) {
          const err = document.createElement("p");
          err.className = "run-story-err";
          err.textContent = String(step.error);
          btn.appendChild(err);
        }
        stepsEl.appendChild(btn);
      });
      if (!(state.outcomes || []).length) {
        const empty = document.createElement("p");
        empty.className = "plan-deep-hint";
        empty.textContent = "No step outcomes on this run yet.";
        stepsEl.appendChild(empty);
      }
    }

    const strip = deep.querySelector("[data-run-deep-strip]");
    const stripEmpty = deep.querySelector("[data-run-deep-strip-empty]");
    if (strip) {
      strip.innerHTML = "";
      const pages = state.pages || [];
      pages.forEach(function (page) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "plan-deep-thumb-chip";
        chip.setAttribute("data-run-deep-chip", "1");
        chip.setAttribute("data-shot-path", String(page.path || ""));
        if (page.step_index != null) {
          chip.setAttribute("data-step-index", String(page.step_index));
        }
        chip.setAttribute(
          "aria-label",
          page.step_index != null
            ? "Step " + page.step_index + " captured page"
            : "Captured page"
        );
        const img = document.createElement("img");
        img.alt = "";
        img.src = shotUrlForDeep(
          state.planId,
          state.caseId,
          state.runId,
          page.path
        );
        const cap = document.createElement("span");
        cap.className = "chip-cap";
        cap.textContent =
          page.step_index != null
            ? page.step_index + " · " + String(page.label || "shot").slice(0, 28)
            : String(page.label || "Captured page").slice(0, 32);
        chip.appendChild(img);
        chip.appendChild(cap);
        strip.appendChild(chip);
      });
      if (stripEmpty) stripEmpty.hidden = pages.length > 0;
    }
  }

  function openPlanRunEvidenceDeep(opts) {
    const options = opts || {};
    const state = planDeepViewState;
    const deep = planDeepSurface();
    const panel = planCasesPanel();
    if (!state || !state.lastRun || !deep || !panel) return;
    showPlanPanel("cases");
    fillPlanDeepView(state);
    deep.hidden = false;
    panel.setAttribute("data-run-evidence-deep-open", "1");
    focusPlanDeepView({
      path: options.focusPath || state.shotPath || "",
      stepIndex: options.focusStep || null,
    });
  }

  function ensurePlanDeepViewHandlers() {
    const deep = planDeepSurface();
    if (!deep || deep.getAttribute("data-run-deep-bound") === "1") return;
    deep.setAttribute("data-run-deep-bound", "1");
    deep.addEventListener("click", async function (ev) {
      const back = ev.target && ev.target.closest
        ? ev.target.closest("[data-run-deep-back]")
        : null;
      if (back && deep.contains(back)) {
        closePlanRunEvidenceDeep();
        return;
      }
      const stepBtn = ev.target && ev.target.closest
        ? ev.target.closest("[data-run-deep-step]")
        : null;
      if (stepBtn && deep.contains(stepBtn)) {
        const idx = Number(stepBtn.getAttribute("data-step-index") || 0) || null;
        focusPlanDeepView({ stepIndex: idx, path: "" });
        return;
      }
      const chip = ev.target && ev.target.closest
        ? ev.target.closest("[data-run-deep-chip]")
        : null;
      if (chip && deep.contains(chip)) {
        focusPlanDeepView({
          path: String(chip.getAttribute("data-shot-path") || ""),
          stepIndex: Number(chip.getAttribute("data-step-index") || 0) || null,
        });
        return;
      }
      const traceBtn = ev.target && ev.target.closest
        ? ev.target.closest("[data-run-deep-open-trace]")
        : null;
      if (traceBtn && deep.contains(traceBtn) && !traceBtn.disabled) {
        const path = String(
          traceBtn.getAttribute("data-trace-path") ||
            (planDeepViewState && planDeepViewState.tracePath) ||
            ""
        ).trim();
        if (!path) return;
        try {
          await fetch("/api/playwright-trace/open", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              path: path,
              action: "show_trace",
              launch: true,
            }),
          });
        } catch (err) {
          /* status stays in aside Open Trace row */
        }
      }
    });
  }

  function fillPlanRunStory(root, opts) {
    const options = opts || {};
    if (!root || root.getAttribute("data-run-story") !== "1") return;
    ensureRunStoryDeepHandlers(root);
    ensurePlanDeepViewHandlers();
    const last = options.lastRun || null;
    const statusEl = root.querySelector("[data-run-story-status]");
    const metaEl = root.querySelector("[data-run-story-meta]");
    const stepsEl = root.querySelector("[data-run-story-steps]");
    const noStepsEl = root.querySelector("[data-run-story-no-steps]");
    const thumb = root.querySelector("[data-run-story-thumb]");
    const thumbImg = root.querySelector("[data-run-story-thumb-img]");
    const thumbCap = root.querySelector("[data-run-story-thumb-cap]");
    const noneBox = root.querySelector("[data-run-story-none]");
    const noneReason = root.querySelector("[data-run-story-none-reason]");
    const entry = root.querySelector("[data-run-story-entry]");
    const summary = root.querySelector("[data-evidence-summary]");
    if (summary) summary.hidden = true;

    if (!last) {
      if (statusEl) {
        statusEl.textContent = "No run";
        statusEl.className = "run-story-pill";
      }
      if (metaEl) metaEl.textContent = "Run a case to see steps and evidence.";
      if (stepsEl) {
        stepsEl.hidden = true;
        stepsEl.innerHTML = "";
      }
      if (noStepsEl) noStepsEl.hidden = true;
      if (thumb) thumb.hidden = true;
      if (entry) entry.hidden = true;
      if (noneBox) {
        noneBox.hidden = false;
        if (noneReason) {
          noneReason.textContent =
            options.emptyReason ||
            "No run yet. This slot stays empty until a run writes evidence.";
        }
      }
      return;
    }

    const st = formatRunStoryStatus(last.result);
    if (statusEl) {
      statusEl.textContent = st.text;
      statusEl.className =
        "run-story-pill" + (st.kind !== "idle" ? " is-" + st.kind : "");
    }
    const metaParts = [];
    const dur = formatRunStoryDuration(last.duration_ms);
    if (dur) metaParts.push(dur);
    if (last.failure_class) metaParts.push(String(last.failure_class));
    else if (options.tags && options.tags.length) {
      metaParts.push(String(options.tags[0]));
    }
    if (last.sandbox) metaParts.push(String(last.sandbox));
    else if (last.environment_name) metaParts.push(String(last.environment_name));
    const when = last.finished_at || last.started_at || "";
    if (when) metaParts.push(String(when).slice(11, 16) || String(when).slice(0, 19));
    if (metaEl) metaEl.textContent = metaParts.join(" · ");

    const outcomes = Array.isArray(last.step_outcomes) ? last.step_outcomes : [];
    if (stepsEl) {
      stepsEl.innerHTML = "";
      if (outcomes.length) {
        stepsEl.hidden = false;
        if (noStepsEl) noStepsEl.hidden = true;
        outcomes.forEach(function (step) {
          const li = document.createElement("li");
          const stepStatus = String((step && step.status) || "").toLowerCase();
          li.className =
            "run-story-step" + (stepStatus === "fail" || stepStatus === "error" ? " is-fail" : "");
          const n = document.createElement("span");
          n.className = "run-story-n";
          n.textContent = String((step && step.index) || "");
          const verb = document.createElement("span");
          verb.className = "run-story-verb";
          verb.textContent = String((step && step.label) || (step && step.action) || "Step");
          const pill = document.createElement("span");
          const ok = stepStatus === "pass";
          const bad = stepStatus === "fail" || stepStatus === "error";
          pill.className =
            "run-story-step-pill" + (ok ? " is-pass" : bad ? " is-fail" : "");
          pill.textContent = ok ? "Pass" : bad ? "Fail" : stepStatus || "—";
          li.appendChild(n);
          li.appendChild(verb);
          li.appendChild(pill);
          if (step && step.duration_ms != null) {
            const ms = document.createElement("span");
            ms.className = "run-story-ms";
            ms.textContent = formatRunStoryDuration(step.duration_ms);
            li.appendChild(ms);
          }
          if (step && step.error) {
            const err = document.createElement("p");
            err.className = "run-story-err";
            err.textContent = String(step.error);
            li.appendChild(err);
          }
          stepsEl.appendChild(li);
        });
      } else {
        stepsEl.hidden = true;
        if (noStepsEl) {
          noStepsEl.hidden = false;
          noStepsEl.textContent =
            "No step outcomes on this run yet (older runs may lack a narrative).";
        }
      }
    }

    const shotPath = String(options.shotPath || "").trim();
    const runId = String((last && last.id) || "").trim();
    const planId = String(options.planId || "").trim();
    const caseId = String(options.caseId || "").trim();
    const failStep = outcomes.find(function (s) {
      return s && (s.status === "fail" || s.status === "error");
    });
    if (shotPath && thumb && thumbImg) {
      thumb.hidden = false;
      if (noneBox) noneBox.hidden = true;
      thumb.setAttribute("data-shot-path", shotPath);
      if (failStep && failStep.index != null) {
        thumb.setAttribute("data-focus-step", String(failStep.index));
      } else {
        thumb.removeAttribute("data-focus-step");
      }
      if (planId && caseId && runId) {
        thumbImg.src = shotUrlForDeep(planId, caseId, runId, shotPath);
      } else {
        thumbImg.removeAttribute("src");
      }
      thumbImg.alt = "Captured page screenshot";
      if (thumbCap) {
        thumbCap.textContent = failStep
          ? "1 shot · step " + failStep.index + " · open deep view"
          : "1 shot · open deep view";
      }
    } else {
      if (thumb) {
        thumb.hidden = true;
        thumb.removeAttribute("data-shot-path");
        thumb.removeAttribute("data-focus-step");
      }
      if (thumbImg) thumbImg.removeAttribute("src");
      if (noneBox) {
        noneBox.hidden = false;
        if (noneReason) {
          noneReason.textContent =
            options.emptyReason ||
            "None captured. A green stand-in is not substituted.";
        }
      }
    }
    if (entry) entry.hidden = false;
  }

  function fillEvidenceFirst(root, opts) {
    const options = opts || {};
    if (!root) return;
    const optional = root.getAttribute("data-evidence-first-optional") === "1";
    const summaryText = String(options.summary || "").trim();
    const linkText = String(options.link || "").trim();
    const hasShot = !!options.hasScreenshot;
    const tracePath = String(options.tracePath || "").trim();
    const hasTrace = !!options.hasTrace || /\.zip$/i.test(tracePath);
    const show =
      !!options.force ||
      !!summaryText ||
      !!linkText ||
      hasShot ||
      hasTrace ||
      !optional;
    if (
      !show ||
      (optional && !summaryText && !linkText && !hasShot && !hasTrace)
    ) {
      hideEvidenceFirst(root);
      return;
    }
    root.hidden = false;
    const summary = root.querySelector("[data-evidence-summary]");
    if (summary) {
      summary.textContent = summaryText || "—";
    }
    const links = root.querySelector("[data-evidence-links]");
    if (links) {
      if (linkText) {
        links.hidden = false;
        links.textContent = linkText;
      } else {
        links.hidden = true;
        links.textContent = "";
      }
    }
    const warn = root.querySelector("[data-evidence-shot-warn]");
    if (warn) {
      warn.hidden = !hasShot;
      if (hasShot) warn.textContent = EVIDENCE_SHOT_WARN;
    }
    const trace = root.querySelector("[data-evidence-trace]");
    if (trace) {
      if (hasTrace) {
        trace.textContent = tracePath
          ? EVIDENCE_TRACE_CAPTURED + " " + tracePath
          : EVIDENCE_TRACE_CAPTURED;
      } else {
        trace.textContent = EVIDENCE_TRACE_NONE;
      }
    }
    setEvidenceTraceActions(root, tracePath, hasTrace);
  }

  function clearReportCharts() {
    if (rptCharts) rptCharts.hidden = true;
    if (rptChartsEmpty) {
      rptChartsEmpty.hidden = true;
      rptChartsEmpty.textContent = "No chart metrics in this report.";
    }
    if (rptChartsGrid) rptChartsGrid.hidden = true;
    [
      rptChartPassFail,
      rptChartCoverage,
      rptChartDuration,
      rptChartFailureClasses,
      rptChartBugsByStory,
    ].forEach(function (panel) {
      if (panel) panel.hidden = true;
    });
    [
      rptChartPassFailBody,
      rptChartCoverageBody,
      rptChartDurationBody,
      rptChartFailureClassesBody,
      rptChartBugsByStoryBody,
    ].forEach(function (body) {
      if (body) body.innerHTML = "";
    });
  }

  function rptChartBarRow(label, value, maxValue, tone) {
    const safeMax = maxValue > 0 ? maxValue : 1;
    const count = Number(value) || 0;
    const pct = Math.max(0, Math.min(100, Math.round((100 * count) / safeMax)));
    const row = document.createElement("div");
    row.className = "rpt-chart-bar-row";
    const name = document.createElement("span");
    name.className = "rpt-chart-bar-label";
    name.textContent = label;
    const track = document.createElement("div");
    track.className = "rpt-chart-bar-track";
    track.setAttribute("role", "img");
    track.setAttribute("aria-label", label + ": " + count);
    const fill = document.createElement("div");
    fill.className = "rpt-chart-bar-fill" + (tone ? " is-" + tone : "");
    fill.style.width = pct + "%";
    track.appendChild(fill);
    const num = document.createElement("span");
    num.className = "rpt-chart-bar-value";
    num.textContent = String(count);
    row.appendChild(name);
    row.appendChild(track);
    row.appendChild(num);
    return row;
  }

  function renderReportCharts(analytics) {
    clearReportCharts();
    if (!rptCharts) return;
    rptCharts.hidden = false;
    const data = analytics && typeof analytics === "object" ? analytics : null;
    const hasMetrics = !!(data && data.has_metrics);
    if (!hasMetrics) {
      if (rptChartsEmpty) {
        rptChartsEmpty.hidden = false;
        rptChartsEmpty.textContent =
          (data && data.empty_hint) || "No chart metrics in this report.";
      }
      if (rptChartsGrid) rptChartsGrid.hidden = true;
      return;
    }
    if (rptChartsEmpty) rptChartsEmpty.hidden = true;
    if (rptChartsGrid) rptChartsGrid.hidden = false;

    const passFail = data.pass_fail;
    if (passFail && rptChartPassFail && rptChartPassFailBody) {
      rptChartPassFail.hidden = false;
      const maxVal = Math.max(
        Number(passFail.passed) || 0,
        Number(passFail.failed) || 0,
        1
      );
      rptChartPassFailBody.appendChild(
        rptChartBarRow("Passed", passFail.passed, maxVal, "pass")
      );
      rptChartPassFailBody.appendChild(
        rptChartBarRow("Failed", passFail.failed, maxVal, "fail")
      );
      if (passFail.pass_rate_percent != null) {
        const rate = document.createElement("p");
        rate.className = "rpt-chart-meta";
        rate.textContent = "Pass rate " + passFail.pass_rate_percent + "%";
        rptChartPassFailBody.appendChild(rate);
      }
    }

    const coverage = data.coverage;
    if (coverage && rptChartCoverage && rptChartCoverageBody) {
      rptChartCoverage.hidden = false;
      const covered = Number(coverage.stories_covered) || 0;
      rptChartCoverageBody.appendChild(
        rptChartBarRow("Stories covered", covered, Math.max(covered, 1), "accent")
      );
      const keys = Array.isArray(coverage.stories) ? coverage.stories : [];
      if (keys.length) {
        const list = document.createElement("p");
        list.className = "rpt-chart-meta";
        list.textContent = keys.slice(0, 8).join(", ") + (keys.length > 8 ? "…" : "");
        rptChartCoverageBody.appendChild(list);
      }
    }

    const duration = data.duration;
    if (duration && rptChartDuration && rptChartDurationBody) {
      rptChartDuration.hidden = false;
      const label = document.createElement("p");
      label.className = "rpt-chart-duration-value";
      label.textContent = duration.label || String(duration.seconds || "—") + "s";
      rptChartDurationBody.appendChild(label);
    }

    const classes = Array.isArray(data.failure_classes) ? data.failure_classes : [];
    if (classes.length && rptChartFailureClasses && rptChartFailureClassesBody) {
      rptChartFailureClasses.hidden = false;
      const maxClass = classes.reduce(function (m, row) {
        return Math.max(m, Number(row.count) || 0);
      }, 1);
      classes.slice(0, 8).forEach(function (row) {
        rptChartFailureClassesBody.appendChild(
          rptChartBarRow(row.label || "unclassified", row.count, maxClass, "fail")
        );
      });
    }

    const bugs = Array.isArray(data.bugs_by_story) ? data.bugs_by_story : [];
    if (bugs.length && rptChartBugsByStory && rptChartBugsByStoryBody) {
      rptChartBugsByStory.hidden = false;
      const maxBugs = bugs.reduce(function (m, row) {
        return Math.max(m, Number(row.count) || 0);
      }, 1);
      bugs.slice(0, 8).forEach(function (row) {
        rptChartBugsByStoryBody.appendChild(
          rptChartBarRow(row.story || "unlinked", row.count, maxBugs, "warn")
        );
      });
    }
  }

  function clearReportViewer(message) {
    if (rptMarkdown) rptMarkdown.textContent = message || "Select a report to read its markdown.";
    if (rptJson) rptJson.textContent = "No JSON found";
    if (rptScreenshot) {
      rptScreenshot.hidden = true;
      rptScreenshot.removeAttribute("src");
    }
    clearReportCharts();
    hideEvidenceFirst(evidenceFirstRoot("rpt-evidence-first"));
  }

  function formatReportWhen(stamp) {
    const raw = String(stamp || "").trim();
    if (!raw) return "—";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return raw;
    try {
      return d.toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (err) {
      return raw;
    }
  }

  function syncReportListSelection(reportId) {
    rptSelectedId = reportId || "";
    if (!rptScanBody) return;
    rptScanBody.querySelectorAll(".rpt-scan-row").forEach(function (row) {
      const on = row.getAttribute("data-report-id") === rptSelectedId;
      row.classList.toggle("is-focus", on);
      row.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function renderReportLibraryList(rows) {
    if (!rptScanBody) return;
    rptScanBody.innerHTML = "";
    (rows || []).forEach(function (row) {
      const id = row.id || "";
      if (!id) return;
      const tr = document.createElement("tr");
      tr.className = "rpt-scan-row" + (id === rptSelectedId ? " is-focus" : "");
      tr.setAttribute("role", "row");
      tr.setAttribute("data-report-id", id);
      tr.setAttribute("aria-selected", id === rptSelectedId ? "true" : "false");
      const whenTd = document.createElement("td");
      whenTd.textContent = formatReportWhen(row.timestamp || row.when || "");
      const titleTd = document.createElement("td");
      titleTd.textContent = row.title || row.label || id;
      const levelTd = document.createElement("td");
      levelTd.textContent = row.level || row.security_level || "—";
      const kindTd = document.createElement("td");
      kindTd.textContent = row.kind || "Run";
      tr.appendChild(whenTd);
      tr.appendChild(titleTd);
      tr.appendChild(levelTd);
      tr.appendChild(kindTd);
      tr.tabIndex = 0;
      tr.addEventListener("click", function () {
        syncReportListSelection(id);
        loadReportDetail(id);
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              rptScanBody.querySelectorAll(".rpt-scan-row")
            );
          },
          activate: function (row) {
            const rid = row.getAttribute("data-report-id") || "";
            syncReportListSelection(rid);
            loadReportDetail(rid);
          },
        });
      });
      rptScanBody.appendChild(tr);
    });
  }

  async function loadReportDetail(reportId) {
    syncReportListSelection(reportId || "");
    if (!reportId) {
      if (rptViewerTitle) rptViewerTitle.textContent = "Report";
      clearReportViewer("No reports yet. Export a run or wait for a plan case export.");
      return;
    }
    try {
      const res = await fetch("/api/reports/" + encodeURIComponent(reportId));
      if (!res.ok) {
        clearReportViewer("Could not load that report.");
        return;
      }
      const data = await res.json();
      if (rptViewerTitle) {
        rptViewerTitle.textContent = data.label || data.title || reportId;
      }
      if (rptMarkdown) rptMarkdown.textContent = data.markdown || "No markdown for this report.";
      if (rptJson) {
        try {
          rptJson.textContent = JSON.stringify(data.json || {}, null, 2);
        } catch (err) {
          rptJson.textContent = "No JSON found";
        }
      }
      if (rptScreenshot) {
        if (data.has_screenshot) {
          rptScreenshot.src =
            "/api/reports/" + encodeURIComponent(reportId) + "/screenshot?t=" + Date.now();
          rptScreenshot.hidden = false;
        } else {
          rptScreenshot.hidden = true;
          rptScreenshot.removeAttribute("src");
        }
      }
      fillEvidenceFirst(evidenceFirstRoot("rpt-evidence-first"), {
        force: true,
        summary:
          (data.label || data.title || reportId) +
          (data.timestamp || data.when
            ? " · " + formatReportWhen(data.timestamp || data.when)
            : ""),
        link: data.has_screenshot ? "Screenshot linked in detail" : "",
        hasScreenshot: !!data.has_screenshot,
      });
      renderReportCharts(data.analytics || null);
      if (rptStatus) rptStatus.textContent = "Opened " + (data.label || reportId);
    } catch (err) {
      clearReportViewer("Could not load that report.");
    }
  }

  async function loadReportLibrary() {
    try {
      const res = await fetch("/api/reports?limit=50");
      if (!res.ok) return;
      const data = await res.json();
      const rows = (data && data.reports) || [];
      const previous = rptSelectedId || "";
      const stillThere =
        previous &&
        rows.some(function (row) {
          return (row.id || "") === previous;
        });
      rptSelectedId = stillThere ? previous : rows.length ? rows[0].id || "" : "";
      renderReportLibraryList(rows);
      syncReportListSelection(rptSelectedId);
      if (rptEmpty) rptEmpty.hidden = rows.length > 0;
      if (rptScanBody) rptScanBody.hidden = rows.length === 0;
      if (rptSelectedId) {
        await loadReportDetail(rptSelectedId);
      } else {
        if (rptViewerTitle) rptViewerTitle.textContent = "Report";
        clearReportViewer(
          (data && data.empty_hint) ||
            "No saved reports yet. Run a plan case or export a run."
        );
        if (rptStatus) rptStatus.textContent = "No saved reports";
      }
    } catch (err) {
      if (rptEmpty) rptEmpty.hidden = false;
      clearReportViewer("Could not load the report library.");
      if (rptStatus) rptStatus.textContent = "Could not load library";
    }
  }

  let settingsCategoryPending = null;
  const SETTINGS_SECTIONS = [
    "layout",
    "connections",
    "environments",
    "model",
    "report",
    "credentials",
  ];
  const REPORT_BLOCK_LABELS = {
    summary: "Summary",
    stories: "Stories",
    bugs: "Bugs",
    evidence: "Evidence",
    known_issues: "Known issues",
    traceability: "Traceability matrix",
    documents: "Documents",
  };

  function normalizeSettingsSection(cat) {
    if (SETTINGS_SECTIONS.indexOf(cat) >= 0) return cat;
    if (cat === "app") return "layout";
    if (cat === "report") return "report";
    return "layout";
  }

  function setSettingsSection(section) {
    const chosen = normalizeSettingsSection(section);
    document.querySelectorAll(".settings-section-btn[data-settings-section]").forEach(function (btn) {
      const on = btn.getAttribute("data-settings-section") === chosen;
      btn.setAttribute("aria-current", on ? "true" : "false");
    });
    document.querySelectorAll(".settings-section-panel[data-settings-section-panel]").forEach(function (panel) {
      // Only the selected section is visible — others stay hidden.
      panel.hidden = panel.getAttribute("data-settings-section-panel") !== chosen;
    });
    // Do not scrollIntoView report heading — that scrolled .area-work and moved the
    // section rail out from under clicks (KAN-324 rail intermittency).
    const main = document.querySelector(
      "#app-section-settings .settings-grammar-main"
    );
    if (main) main.scrollTop = 0;
  }

  function setSettingsCategory(cat) {
    // Back-compat alias: App/Report deep-links → FR-UI-11 section rail.
    setSettingsSection(cat === "report" ? "report" : cat === "app" ? "layout" : cat);
  }

  function openReportSettings() {
    settingsCategoryPending = "report";
    if (openAreaName === "settings") {
      setSettingsCategory("report");
      settingsCategoryPending = null;
      return;
    }
    openArea("settings");
  }

  function resetEnvDeleteConfirm() {
    if (setEnvDeleteConfirm) setEnvDeleteConfirm.disabled = true;
  }

  function focusEnvironmentDetail(env, opts) {
    const options = opts || {};
    const id = env && env.id ? env.id : "";
    if (setEnvActive) setEnvActive.value = id;
    if (setEnvName) setEnvName.value = (env && env.name) || "";
    if (setTargetUrl) setTargetUrl.value = (env && env.target_url) || "";
    if (setTargetExe) setTargetExe.value = (env && env.target_app_path) || "";
    if (setApiEndpoint) setApiEndpoint.value = (env && env.api_endpoint) || "";
    if (setEnvDetailTitle) {
      setEnvDetailTitle.textContent = (env && env.name) || (options.isNew ? "New environment" : "Environment");
    }
    if (setEnvScanBody) {
      setEnvScanBody.querySelectorAll(".settings-scan-row").forEach(function (row) {
        row.classList.toggle("is-focus", row.getAttribute("data-env-id") === id && !!id);
      });
    }
    resetEnvDeleteConfirm();
    if (options.focusField && setEnvName && typeof setEnvName.focus === "function") {
      window.setTimeout(function () {
        setEnvName.focus();
      }, 20);
    } else if (setEnvDetail && typeof setEnvDetail.focus === "function") {
      setEnvDetail.setAttribute("tabindex", "-1");
      window.setTimeout(function () {
        setEnvDetail.focus();
      }, 20);
    }
  }

  function renderEnvironmentScan(payload) {
    if (!setEnvScanBody) return;
    const envs = payload.environments || payload.named_environments || [];
    const activeId = payload.active_environment_id || "";
    const selectedId = (setEnvActive && setEnvActive.value) || activeId || "";
    setEnvScanBody.innerHTML = "";
    if (!envs.length) {
      const empty = document.createElement("tr");
      empty.className = "settings-scan-empty";
      empty.setAttribute("data-scan-quiet-empty", "1");
      empty.innerHTML = '<td colspan="3">No named environments yet</td>';
      setEnvScanBody.appendChild(empty);
      return;
    }
    envs.forEach(function (env) {
      const tr = document.createElement("tr");
      tr.className = "settings-scan-row";
      tr.setAttribute("data-env-id", env.id || "");
      tr.tabIndex = 0;
      if ((env.id || "") === selectedId) tr.classList.add("is-focus");
      const status = document.createElement("td");
      const pill = document.createElement("span");
      const isActive = (env.id || "") === activeId;
      pill.className = "settings-pill " + (isActive ? "ok" : "idle");
      pill.textContent = isActive ? "Active" : "Idle";
      status.appendChild(pill);
      const name = document.createElement("td");
      name.textContent = env.name || env.id || "env";
      const target = document.createElement("td");
      target.className = "mono";
      target.textContent = env.target_url || "—";
      tr.appendChild(status);
      tr.appendChild(name);
      tr.appendChild(target);
      tr.addEventListener("click", function () {
        focusEnvironmentDetail(env, { focusField: true });
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              setEnvScanBody.querySelectorAll(".settings-scan-row")
            );
          },
          activate: function (row) {
            const eid = row.getAttribute("data-env-id") || "";
            const match = envs.find(function (e) {
              return (e.id || "") === eid;
            });
            if (match) focusEnvironmentDetail(match, { focusField: false });
          },
        });
      });
      setEnvScanBody.appendChild(tr);
    });
  }

  function focusReportBlock(key) {
    const label = REPORT_BLOCK_LABELS[key] || key;
    document.querySelectorAll("#set-rpt-scan .settings-scan-row").forEach(function (row) {
      row.classList.toggle("is-focus", row.getAttribute("data-report-block") === key);
    });
    if (rptDetailTitle) rptDetailTitle.textContent = label;
    if (rptDetailHint) {
      rptDetailHint.textContent =
        key === "documents"
          ? "Documents bodies are off by default. The checkbox cell is the only include toggle."
          : "Include " + label + " in the next export. The checkbox cell is the only include toggle.";
    }
    const pane = document.getElementById("set-rpt-detail");
    if (pane) {
      pane.setAttribute("tabindex", "-1");
      window.setTimeout(function () {
        pane.focus();
      }, 20);
    }
  }

  function syncReportBlockPills() {
    document.querySelectorAll("#set-rpt-scan .settings-scan-row").forEach(function (row) {
      const key = row.getAttribute("data-report-block");
      const input = row.querySelector('input[type="checkbox"]');
      const pill = row.querySelector(".settings-pill");
      if (!input || !pill) return;
      if (key === "documents") {
        pill.className = "settings-pill " + (input.checked ? "ok" : "warn");
        pill.textContent = input.checked ? "On" : "Bodies off";
      } else {
        pill.className = "settings-pill " + (input.checked ? "ok" : "idle");
        pill.textContent = input.checked ? "On" : "Off";
      }
    });
  }

  async function exportChosenRun() {
    if (!rptRunSelect || !rptRunSelect.value) {
      if (rptStatus) rptStatus.textContent = "Choose a run to export.";
      return;
    }
    const parts = rptRunSelect.value.split("|");
    const planId = parts[0] || "";
    const caseId = parts[1] || "";
    const runId = parts[2] || "";
    if (!planId || !caseId || !runId) {
      if (rptStatus) rptStatus.textContent = "Chosen run is incomplete.";
      return;
    }
    if (rptStatus) rptStatus.textContent = "Exporting…";
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(planId) +
          "/cases/" +
          encodeURIComponent(caseId) +
          "/runs/" +
          encodeURIComponent(runId) +
          "/export",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(reportSectionBody()),
        }
      );
      const data = await res.json();
      if (!data || data.status !== "ok") {
        if (rptStatus) {
          rptStatus.textContent =
            (data && (data.message || data.error)) || "Export failed.";
        }
        return;
      }
      if (rptStatus) {
        const n = data.heal_pending_count || 0;
        const hits = data.redaction_hits || 0;
        let text =
          "Exported run " +
          runId +
          ". Redaction hits: " +
          hits +
          ". " +
          n +
          " pending heal(s) for this run — open Heal review to approve/reject (no auto-commit).";
        if (data.screenshot_redaction_warning) {
          text += " " + data.screenshot_redaction_warning;
        }
        rptStatus.textContent = text;
      }
      if (healRunFilter) {
        healRunFilter.value = [planId, caseId, runId].join("|");
      }
      loadReportLibrary();
    } catch (err) {
      if (rptStatus) rptStatus.textContent = "Could not export chosen run.";
    }
  }

  async function exportChosenPack() {
    if (!rptRunSelect || !rptRunSelect.value) {
      if (rptStatus) rptStatus.textContent = "Choose a run to export as a pack.";
      return;
    }
    const parts = rptRunSelect.value.split("|");
    const planId = parts[0] || "";
    const caseId = parts[1] || "";
    const runId = parts[2] || "";
    if (!planId || !caseId || !runId) {
      if (rptStatus) rptStatus.textContent = "Chosen run is incomplete.";
      return;
    }
    if (rptStatus) rptStatus.textContent = "Writing read-only pack…";
    try {
      const body = Object.assign({}, reportSectionBody(), {
        plan_id: planId,
        case_id: caseId,
        run_id: runId,
      });
      const res = await fetch("/api/export-pack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!data || data.status !== "ok") {
        if (rptStatus) {
          rptStatus.textContent =
            (data && (data.message || data.error)) || "Pack export failed.";
        }
        return;
      }
      if (rptStatus) {
        let text =
          "Read-only pack " +
          (data.folder_name || data.pack_id || "") +
          " · level " +
          (data.security_level || "") +
          " · " +
          (data.exported_at || "") +
          ". Open README.md without this app. Redaction hits: " +
          (data.redaction_hits || 0) +
          ".";
        if (data.screenshot_redaction_warning) {
          text += " " + data.screenshot_redaction_warning;
        }
        rptStatus.textContent = text;
      }
      loadExportPackHud();
    } catch (err) {
      if (rptStatus) rptStatus.textContent = "Could not write read-only pack.";
    }
  }

  function fillEnvironmentSelect(selectEl, payload) {
    if (!selectEl) return;
    const envs = payload.environments || payload.named_environments || [];
    const activeId = payload.active_environment_id || "";
    const previous = selectEl.value;
    selectEl.innerHTML = "";
    if (!envs.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "(none yet)";
      selectEl.appendChild(opt);
      return;
    }
    envs.forEach(function (env) {
      const opt = document.createElement("option");
      opt.value = env.id || "";
      const label = (env.name || env.id || "env") +
        (env.target_url ? " — " + env.target_url : "");
      opt.textContent = label;
      selectEl.appendChild(opt);
    });
    const prefer = activeId || previous;
    if (prefer) {
      selectEl.value = prefer;
    }
  }

  function applyEnvironments(payload) {
    if (!payload) return;
    fillEnvironmentSelect(setEnvActive, payload);
    fillEnvironmentSelect(planEnvActive, payload);
    renderEnvironmentScan(payload);
    const activeName =
      payload.active_environment_name ||
      (payload.environment && payload.environment.name) ||
      "—";
    const level = payload.security_level || "—";
    const count = (payload.environments || payload.named_environments || []).length;
    const line =
      "Active: " +
      activeName +
      " · " +
      count +
      " named · level " +
      level +
      " (unchanged on switch)";
    if (envStatus) envStatus.textContent = line;
    if (planEnvStatus) planEnvStatus.textContent = "Environment: " + activeName;
    const envs = payload.environments || payload.named_environments || [];
    const selectedId = (setEnvActive && setEnvActive.value) || "";
    const focused =
      envs.find(function (e) {
        return e.id === selectedId;
      }) ||
      envs.find(function (e) {
        return e.id === payload.active_environment_id;
      });
    if (focused) {
      focusEnvironmentDetail(focused);
    } else {
      resetEnvDeleteConfirm();
    }
  }

  async function loadEnvironments() {
    try {
      const res = await fetch("/api/environments");
      const payload = await res.json();
      applyEnvironments(payload);
      return payload;
    } catch (err) {
      if (envStatus) envStatus.textContent = "Could not load environments.";
      if (planEnvStatus) planEnvStatus.textContent = "Environment: unavailable";
      return null;
    }
  }

  function showLocalRunNotice(notice) {
    if (!notice || typeof notice !== "object") return;
    const title = notice.title || "Run finished";
    const body =
      notice.body ||
      (notice.pass != null && notice.fail != null
        ? notice.pass + " passed, " + notice.fail + " failed"
        : "");
    const text = body ? title + " — " + body : title;
    if (runFinishToast) {
      runFinishToast.hidden = false;
      runFinishToast.textContent = text;
      if (runFinishToastTimer) clearTimeout(runFinishToastTimer);
      runFinishToastTimer = setTimeout(function () {
        runFinishToast.hidden = true;
      }, 6000);
    }
    try {
      if (typeof Notification !== "undefined" && Notification.permission === "granted") {
        new Notification(title, { body: body || undefined });
      } else if (
        typeof Notification !== "undefined" &&
        Notification.permission !== "denied"
      ) {
        Notification.requestPermission().then(function (perm) {
          if (perm === "granted") {
            new Notification(title, { body: body || undefined });
          }
        });
      }
    } catch (_err) {
      /* local notice only — ignore Notification API failures */
    }
  }

  function applyAppSettings(payload) {
    if (!payload) return;
    if (setJiraUrl) {
      setJiraUrl.value = payload.jira_url || "";
    }
    if (setJiraProject) {
      setJiraProject.value = payload.jira_project || "";
    }
    if (setOllamaModel && payload.ollama_model) {
      const wanted = payload.ollama_model;
      let found = false;
      Array.prototype.forEach.call(setOllamaModel.options || [], function (opt) {
        if (opt.value === wanted) found = true;
      });
      if (!found && wanted) {
        const opt = document.createElement("option");
        opt.value = wanted;
        opt.textContent = wanted + " (saved)";
        setOllamaModel.appendChild(opt);
      }
      setOllamaModel.value = wanted;
    }
    applyEnvironments(payload);
    if (setTargetUrl && !(payload.named_environments || []).length) {
      setTargetUrl.value = payload.target_url || "";
    }
    if (setTargetExe && !(payload.named_environments || []).length) {
      setTargetExe.value = payload.target_app_path || "";
    }
    if (setApiEndpoint && !(payload.named_environments || []).length) {
      setApiEndpoint.value = payload.api_endpoint || "";
    }
    if (setTargetUrl && payload.target_url && !setTargetUrl.value) {
      setTargetUrl.value = payload.target_url || "";
    }
    if (setTargetExe && payload.target_app_path && !setTargetExe.value) {
      setTargetExe.value = payload.target_app_path || "";
    }
    if (setApiEndpoint && payload.api_endpoint && !setApiEndpoint.value) {
      setApiEndpoint.value = payload.api_endpoint || "";
    }
    if (setTestFramework) {
      const fw = (payload.test_framework || "playwright").toLowerCase();
      setTestFramework.value =
        fw === "selenium" || fw === "cypress" ? fw : "playwright";
      activeSettingsFramework = setTestFramework.value || "playwright";
      syncFrameworkStubHonestyUi();
    }
    if (setPlaywrightMode) {
      const mode = (payload.playwright_mode || "").toLowerCase();
      setPlaywrightMode.value =
        mode === "headless" || payload.playwright_headless ? "headless" : "headed";
    }
    if (setRunFinishNotify) {
      setRunFinishNotify.checked = payload.run_finish_notify_enabled !== false;
    }
    if (setRunNotifyStatus) {
      setRunNotifyStatus.textContent =
        "Notices: " +
        (payload.run_finish_notify_enabled === false ? "off" : "on") +
        " (local only; no email or cloud push)";
    }
    if (connLevel) {
      connLevel.textContent =
        "Security level: " +
        (payload.security_level || "—") +
        " (switch requires confirm in Security)";
    }
    if (setStorePath) {
      setStorePath.textContent =
        "Local store: " + (payload.settings_path || "—");
    }
    if (setCreds) {
      setCreds.textContent =
        payload.jira_credentials_label ||
        "Jira credentials: " + (payload.jira_credentials_status || "—");
    }
    applyCredentialStatus(payload);
    if (setSummary) {
      const lines = (payload.summary || "")
        .split("\n")
        .filter(function (line) {
          return line && line.indexOf("Local store:") !== 0;
        });
      setSummary.textContent = lines.length
        ? lines.join(" · ")
        : "Summary: —";
    }
  }

  function applyConnectionHealth(payload) {
    if (!payload) return;
    if (payload.checklist && connLevel) {
      connLevel.textContent =
        "Security level: " +
        (payload.checklist.security_level || "—") +
        " (switch requires confirm in Security)";
    }
    const checks = payload.checks || [];
    const lines = checks.map(function (c) {
      const mark = c.up ? "UP" : String(c.state || "down").toUpperCase();
      return mark + "  " + (c.label || c.id) + " — " + (c.message || "");
    });
    if (connHealthOut) {
      connHealthOut.hidden = false;
      connHealthOut.textContent = lines.length
        ? lines.join("\n")
        : payload.summary || "";
    }
    if (connHealthStatus) {
      connHealthStatus.textContent =
        payload.message ||
        "Health: " + (payload.overall || "unknown");
    }
  }

  async function loadOllamaModels() {
    if (!setOllamaModel) return;
    if (ollamaModelStatus) ollamaModelStatus.textContent = "Loading models…";
    try {
      const res = await fetch("/api/ollama-models");
      const payload = await res.json();
      const models = payload.models || [];
      const selected = payload.selected || "";
      setOllamaModel.innerHTML = "";
      if (!models.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = payload.status === "ok" ? "(no models)" : "(Ollama unreachable)";
        setOllamaModel.appendChild(opt);
      } else {
        models.forEach(function (name) {
          const opt = document.createElement("option");
          opt.value = name;
          opt.textContent = name;
          setOllamaModel.appendChild(opt);
        });
      }
      if (selected) {
        let found = false;
        Array.prototype.forEach.call(setOllamaModel.options, function (opt) {
          if (opt.value === selected) found = true;
        });
        if (!found) {
          const opt = document.createElement("option");
          opt.value = selected;
          opt.textContent = selected + " (missing)";
          setOllamaModel.appendChild(opt);
        }
        setOllamaModel.value = selected;
      }
      if (ollamaModelStatus) {
        ollamaModelStatus.textContent =
          payload.message ||
          (payload.status === "ok"
            ? "Model: " + (selected || "not set")
            : "Could not list models");
      }
    } catch (err) {
      if (ollamaModelStatus) {
        ollamaModelStatus.textContent =
          "Could not list models: " + (err && err.message ? err.message : err);
      }
    }
  }

  function applyCredentialStatus(payload) {
    if (!payload) return;
    const fields =
      payload.fields ||
      payload.credential_fields ||
      [
        {
          label: "Jira email",
          state: payload.jira_email || payload.jira_email_status || "—",
        },
        {
          label: "Jira API token",
          state: payload.jira_api_token || payload.jira_api_token_status || "—",
        },
        {
          label: "Target secret",
          state: payload.target_secret || payload.target_secret_status || "—",
        },
      ];
    if (credStatusList) {
      credStatusList.innerHTML = "";
      fields.forEach(function (row) {
        const li = document.createElement("li");
        li.textContent =
          (row.label || row.key || "Field") + ": " + (row.state || "—");
        credStatusList.appendChild(li);
      });
    }
    if (credStatusSummary) {
      credStatusSummary.textContent =
        payload.summary ||
        payload.credential_summary ||
        "Credential status: —";
    }
    if (setTargetSecret) {
      setTargetSecret.value = "";
    }
  }

  function resetClearSecretPending() {
    pendingClearKey = "";
    if (credClearConfirmBtn) credClearConfirmBtn.disabled = true;
  }

  async function proposeClearSecret(key) {
    if (!key) return;
    if (credStatus) credStatus.textContent = "Proposing clear…";
    try {
      const res = await fetch("/api/credentials/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: key, confirm: false }),
      });
      const payload = await res.json();
      if (payload.status === "confirmation_required") {
        pendingClearKey = key;
        if (credClearConfirmBtn) credClearConfirmBtn.disabled = false;
        if (credStatus) {
          credStatus.textContent =
            payload.message ||
            "Confirm clear (value never shown). Press Confirm clear.";
        }
        return;
      }
      if (credStatus) {
        credStatus.textContent = payload.message || "Clear propose failed.";
      }
    } catch (err) {
      if (credStatus) credStatus.textContent = "Could not propose clear.";
    }
  }

  async function confirmClearSecret() {
    if (!pendingClearKey) {
      if (credStatus) credStatus.textContent = "Propose a clear first.";
      return;
    }
    if (credStatus) credStatus.textContent = "Clearing…";
    try {
      const res = await fetch("/api/credentials/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: pendingClearKey, confirm: true }),
      });
      const payload = await res.json();
      applyCredentialStatus(payload);
      resetClearSecretPending();
      if (credStatus) {
        credStatus.textContent =
          payload.message ||
          (payload.status === "cleared" ? "Cleared." : "Clear failed.");
      }
      await loadAppSettings();
    } catch (err) {
      if (credStatus) credStatus.textContent = "Could not clear secret.";
    }
  }

  async function loadAppSettings() {
    try {
      const res = await fetch("/api/app-settings");
      if (!res.ok) return;
      applyAppSettings(await res.json());
      await loadOllamaModels();
      await loadSecondPcStatus();
      if (setStatus) setStatus.textContent = "Ready";
    } catch (err) {
      if (setStatus) setStatus.textContent = "Could not load app settings.";
    }
  }

  async function loadSecondPcStatus() {
    if (!setSecondPcStatus) return;
    try {
      const res = await fetch("/api/installer/second-pc");
      if (!res.ok) return;
      const data = await res.json();
      const last = data && data.last ? data.last : null;
      if (last && last.exported_at) {
        setSecondPcStatus.textContent =
          "Last pack: " +
          (last.folder_name || "") +
          " · " +
          last.exported_at +
          " · secrets: none · cloud account: no · telemetry default: off";
      } else {
        setSecondPcStatus.textContent =
          "Install pack: not built yet · secrets never included · no shared cloud account";
      }
    } catch (err) {
      setSecondPcStatus.textContent = "Could not load install-pack status.";
    }
  }

  function isKnownLabel(obj) {
    if (!obj) return false;
    if (obj.failure_class === "known_issue") return true;
    return !!(obj.known_issue && obj.known_issue.linked);
  }

  function lastRunLine(caseObj) {
    const runs = (caseObj && caseObj.runs) || [];
    if (!runs.length) return "";
    const last = runs[runs.length - 1];
    const parts = [last.result || "pending"];
    if (last.duration_ms != null) parts.push(last.duration_ms + "ms");
    if (isKnownLabel(last) || isKnownLabel(caseObj)) {
      parts.push("known");
    } else if (last.failure_class) {
      parts.push(last.failure_class);
    }
    const ev = last.evidence || [];
    for (let i = 0; i < ev.length; i++) {
      if (String(ev[i]).toLowerCase().indexOf(".png") >= 0) {
        parts.push("screenshot");
        break;
      }
    }
    return "\n   last run: " + parts.join(" · ");
  }

  function planCaseStatusLabel(caseObj) {
    if (!caseObj) return { text: "—", kind: "idle" };
    if (caseObj.archived) return { text: "Arch", kind: "idle" };
    if (isQuarantinedCase(caseObj)) return { text: "Quar", kind: "warn" };
    if (caseObj.enabled === false) return { text: "Off", kind: "idle" };
    return { text: "On", kind: "ok" };
  }

  function planCaseLastLabel(caseObj) {
    const runs = (caseObj && caseObj.runs) || [];
    if (!runs.length) return { text: "—", kind: "idle" };
    const last = runs[runs.length - 1];
    const result = String((last && last.result) || "").toLowerCase();
    if (result === "pass" || result === "passed" || result === "ok") {
      return { text: "Pass", kind: "ok" };
    }
    if (result === "fail" || result === "failed" || result === "error") {
      return { text: "Fail", kind: "warn" };
    }
    if (result) {
      return { text: last.result, kind: "idle" };
    }
    return { text: "—", kind: "idle" };
  }

  function syncPlanCaseDetailFocusChrome() {
    const cid =
      planCaseId && planCaseId.value ? String(planCaseId.value).trim() : "";
    const focused = !!cid;
    if (planCaseDetailPane) {
      planCaseDetailPane.setAttribute(
        "data-plan-case-focused",
        focused ? "1" : "0"
      );
    }
    if (planCaseUnfocused) {
      planCaseUnfocused.hidden = focused;
    }
    if (planCaseDetailLive) {
      planCaseDetailLive.hidden = !focused;
    }
    if (planCaseDetailPin) {
      planCaseDetailPin.hidden = !focused;
    }
    if (planCaseDetailHint) {
      planCaseDetailHint.hidden = focused;
      if (!focused) {
        planCaseDetailHint.textContent =
          "Select a row. Row click does not toggle Enabled or Archived.";
      }
    }
    if (!focused) {
      hideEvidenceFirst(evidenceFirstRoot("plan-case-evidence-first"));
      if (planCaseTriageStrip) planCaseTriageStrip.hidden = true;
      if (planTriageHealBadge) planTriageHealBadge.hidden = true;
    }
  }

  function syncPlanCaseTriageStrip(lastRun) {
    if (!planCaseTriageStrip) return;
    const hasRun = !!(lastRun && lastRun.id);
    planCaseTriageStrip.hidden = !hasRun;
    if (!planTriageHealBadge) return;
    const result = lastRun && lastRun.result
      ? String(lastRun.result).toLowerCase()
      : "";
    const failed =
      result === "fail" || result === "failed" || result === "error";
    planTriageHealBadge.hidden = !failed;
  }

  function syncPlanCaseRowFocus() {
    if (!planCasesScanBody) return;
    const cid =
      planCaseId && planCaseId.value ? String(planCaseId.value).trim() : "";
    planCasesScanBody.querySelectorAll(".plan-cases-scan-row").forEach(function (el) {
      if (cid && el.dataset.caseId === cid) {
        el.classList.add("is-focus");
      } else {
        el.classList.remove("is-focus");
      }
    });
    if (planCaseDetailTitle) {
      if (!cid) {
        planCaseDetailTitle.textContent = "Case detail";
      } else {
        const hit = openPlanCases.find(function (c) {
          return c && c.id === cid;
        });
        planCaseDetailTitle.textContent = hit
          ? (hit.id || cid) + " · " + (hit.name || "Case")
          : "Case detail";
      }
    }
    syncPlanCaseDetailFocusChrome();
  }

  function focusPlanCaseDetail(caseObj, opts) {
    if (!caseObj) return;
    if (planCaseId) planCaseId.value = caseObj.id || "";
    if (planCaseName) planCaseName.value = caseObj.name || "";
    syncPlanCaseRowFocus();
    if (planCaseDetailHint) {
      planCaseDetailHint.textContent =
        "Focused case. Enabled / Archived / Quarantine stay in this pane — row click does not toggle them.";
      planCaseDetailHint.hidden = true;
    }
    refreshCaseDetail();
    if (opts && opts.focusField && planCaseName) {
      try {
        planCaseName.focus();
      } catch (err) {
        /* ignore */
      }
    }
  }

  function flakeLine(caseObj) {
    const cid = caseObj && caseObj.id;
    const row = cid && openPlanFlakeById[cid];
    if (row && row.flake_label) {
      return "\n   flake: " + row.flake_label + " fails in last " + (row.window || 10);
    }
    const runs = (caseObj && caseObj.runs) || [];
    if (!runs.length) return "\n   flake: 0/0";
    const windowN = 10;
    const recent = runs.slice(-windowN);
    let fails = 0;
    for (let i = 0; i < recent.length; i++) {
      const r = String((recent[i] && recent[i].result) || "").toLowerCase();
      if (r === "fail" || r === "error") fails += 1;
    }
    return "\n   flake: " + fails + "/" + recent.length + " fails in last " + windowN;
  }

  function isQuarantinedCase(caseObj) {
    if (!caseObj) return false;
    const cid = caseObj.id;
    if (cid && openPlanFlakeById[cid] && openPlanFlakeById[cid].quarantined) {
      return true;
    }
    if (caseObj.quarantined === true) return true;
    const q = caseObj.quarantine;
    return !!(q && q.active);
  }

  async function refreshFlakeReport() {
    if (!openPlanId) {
      openPlanFlakeById = {};
      if (planFlakeSummary) planFlakeSummary.textContent = "Flake: —";
      return;
    }
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/flake"
      );
      const payload = await res.json();
      openPlanFlakeById = {};
      if (payload.status === "ok" && Array.isArray(payload.cases)) {
        payload.cases.forEach(function (row) {
          if (row && row.case_id) openPlanFlakeById[row.case_id] = row;
        });
        if (planFlakeSummary) {
          planFlakeSummary.textContent =
            "Flake window " +
            (payload.window || 10) +
            " · quarantined " +
            (payload.quarantined_count || 0) +
            " (skip-only, not a pass)";
        }
      } else if (planFlakeSummary) {
        planFlakeSummary.textContent =
          payload.message || "Could not load flake scores.";
      }
    } catch (err) {
      if (planFlakeSummary) planFlakeSummary.textContent = "Flake request failed.";
    }
  }

  function renderPlanCases(plan) {
    openPlanCases = (plan && plan.suite && plan.suite.cases) || [];
    if (planIntent) {
      const intent = (plan && plan.intent) || "";
      planIntent.hidden = !intent;
      planIntent.textContent = intent || "";
    }
    const body = planCasesScanBody || planCases;
    if (!body) {
      syncFrameworkStubHonestyUi();
      return;
    }
    if (planCasesScanBody) {
      planCasesScanBody.innerHTML = "";
    } else {
      planCases.textContent = "";
    }
    if (!openPlanCases.length) {
      if (planCasesEmpty) {
        planCasesEmpty.hidden = false;
        planCasesEmpty.textContent = "Cases: (none). Add a case or open another plan.";
      }
      syncPlanCaseRowFocus();
      syncFrameworkStubHonestyUi();
      return;
    }
    const showArchived = !!(planShowArchived && planShowArchived.checked);
    const archivedCount = openPlanCases.filter(function (c) {
      return !!c.archived;
    }).length;
    const visible = openPlanCases.filter(function (c) {
      return showArchived || !c.archived;
    });
    if (!visible.length) {
      if (planCasesEmpty) {
        planCasesEmpty.hidden = false;
        planCasesEmpty.textContent =
          "Cases: (none visible — " +
          archivedCount +
          " archived; tick Show archived to list them)";
      }
      syncPlanCaseRowFocus();
      syncFrameworkStubHonestyUi();
      return;
    }
    if (planCasesEmpty) {
      planCasesEmpty.hidden = false;
      planCasesEmpty.textContent =
        archivedCount && !showArchived
          ? visible.length +
            " active · " +
            archivedCount +
            " archived hidden. Row click loads detail."
          : visible.length +
            " case(s). Row click loads detail; Enabled/Archived stay in the pane.";
    }
    if (!planCasesScanBody) {
      // Legacy fallback if scan tbody is missing.
      planCases.textContent =
        "Cases:\n" +
        visible
          .map(function (c, idx) {
            return (
              idx +
              1 +
              ". " +
              (c.id || "?") +
              " — " +
              (c.name || "") +
              flakeLine(c) +
              lastRunLine(c)
            );
          })
          .join("\n");
      syncFrameworkStubHonestyUi();
      return;
    }
    visible.forEach(function (c) {
      const tr = document.createElement("tr");
      tr.className = "plan-cases-scan-row";
      tr.tabIndex = 0;
      tr.dataset.caseId = c.id || "";
      tr.setAttribute("role", "row");
      tr.setAttribute("aria-label", (c.name || c.id || "case") + " — click to edit");

      const status = planCaseStatusLabel(c);
      const tdStatus = document.createElement("td");
      const statusPill = document.createElement("span");
      statusPill.className = "plan-case-pill " + status.kind;
      statusPill.textContent = status.text;
      tdStatus.appendChild(statusPill);

      const tdId = document.createElement("td");
      tdId.className = "mono";
      tdId.textContent = c.id || "?";

      const tdName = document.createElement("td");
      tdName.textContent = c.name || "—";

      const tdTags = document.createElement("td");
      const tags = (c.tags || []).join(", ");
      tdTags.textContent = tags || "—";

      const last = planCaseLastLabel(c);
      const tdLast = document.createElement("td");
      const lastPill = document.createElement("span");
      lastPill.className = "plan-case-pill " + last.kind;
      lastPill.textContent = last.text;
      tdLast.appendChild(lastPill);

      tr.appendChild(tdStatus);
      tr.appendChild(tdId);
      tr.appendChild(tdName);
      tr.appendChild(tdTags);
      tr.appendChild(tdLast);

      tr.addEventListener("click", function () {
        focusPlanCaseDetail(c, { focusField: false });
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              planCasesScanBody.querySelectorAll(".plan-cases-scan-row")
            );
          },
          activate: function (row) {
            const cid = row.getAttribute("data-case-id") || "";
            const match = openPlanCases.find(function (x) {
              return String(x.id || "") === cid;
            });
            if (match) focusPlanCaseDetail(match, { focusField: false });
            else focusPlanCaseDetail(c, { focusField: false });
          },
        });
      });

      planCasesScanBody.appendChild(tr);
    });
    syncPlanCaseRowFocus();
    syncFrameworkStubHonestyUi();
  }

  function focusCoverageGapDetail(row) {
    if (!row) return;
    focusedCoverageKey = row.key || "";
    if (planCoverageDetailKey) planCoverageDetailKey.value = row.key || "";
    if (planCoverageDetailGap) planCoverageDetailGap.value = row.gap || "";
    if (planCoverageDetailSummary) {
      planCoverageDetailSummary.value = row.summary || "";
    }
    if (planCoverageScanBody) {
      planCoverageScanBody.querySelectorAll(".plan-coverage-scan-row").forEach(
        function (tr) {
          tr.classList.toggle(
            "is-focus",
            (tr.dataset.storyKey || "") === focusedCoverageKey
          );
        }
      );
    }
  }

  function renderCoverageGaps(payload) {
    const noCase = (payload && payload.no_case) || [];
    const disabled = (payload && payload.all_disabled) || [];
    const rows = [];
    noCase.forEach(function (r) {
      rows.push({
        key: r.key || "",
        summary: r.summary || "",
        gap: "No case",
        case_count: r.case_count,
      });
    });
    disabled.forEach(function (r) {
      rows.push({
        key: r.key || "",
        summary: r.summary || "",
        gap: "All disabled",
        case_count: r.case_count,
      });
    });
    if (planCoverageNoCase) {
      planCoverageNoCase.textContent = String(noCase.length);
    }
    if (planCoverageDisabled) {
      planCoverageDisabled.textContent = String(disabled.length);
    }
    if (!planCoverageScanBody) return;
    planCoverageScanBody.innerHTML = "";
    if (planCoverageEmpty) {
      planCoverageEmpty.hidden = rows.length > 0;
      planCoverageEmpty.textContent = rows.length
        ? ""
        : "No coverage gaps for this filter.";
    }
    rows.forEach(function (r) {
      const tr = document.createElement("tr");
      tr.className = "plan-coverage-scan-row plan-tabs-scan-row";
      tr.dataset.storyKey = r.key || "";
      tr.setAttribute("role", "row");
      const tdStory = document.createElement("td");
      tdStory.textContent = r.key || "—";
      const tdGap = document.createElement("td");
      const pill = document.createElement("span");
      pill.className =
        "plan-tabs-pill " + (r.gap === "No case" ? "warn" : "idle");
      pill.textContent = r.gap;
      tdGap.appendChild(pill);
      const tdSummary = document.createElement("td");
      tdSummary.textContent = r.summary || "—";
      tr.appendChild(tdStory);
      tr.appendChild(tdGap);
      tr.appendChild(tdSummary);
      tr.tabIndex = 0;
      tr.addEventListener("click", function () {
        focusCoverageGapDetail(r);
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              planCoverageScanBody.querySelectorAll(".plan-coverage-scan-row")
            );
          },
          activate: function (row) {
            const key = row.dataset.storyKey || "";
            const match = rows.find(function (x) {
              return (x.key || "") === key;
            });
            if (match) focusCoverageGapDetail(match);
          },
        });
      });
      planCoverageScanBody.appendChild(tr);
    });
    if (rows.length) {
      const keep =
        rows.find(function (r) {
          return r.key === focusedCoverageKey;
        }) || rows[0];
      focusCoverageGapDetail(keep);
    } else {
      focusedCoverageKey = "";
      if (planCoverageDetailKey) planCoverageDetailKey.value = "";
      if (planCoverageDetailGap) planCoverageDetailGap.value = "";
      if (planCoverageDetailSummary) planCoverageDetailSummary.value = "";
    }
  }

  async function refreshCoverageGaps() {
    if (!openPlanId) {
      renderCoverageGaps({ no_case: [], all_disabled: [] });
      if (planCoverageEmpty) {
        planCoverageEmpty.hidden = false;
        planCoverageEmpty.textContent = "Open a plan and refresh to list gaps.";
      }
      return;
    }
    const q =
      planCoverageFilter && planCoverageFilter.value
        ? planCoverageFilter.value.trim()
        : "";
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/coverage-gaps?q=" +
          encodeURIComponent(q)
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        renderCoverageGaps({ no_case: [], all_disabled: [] });
        if (planCoverageEmpty) {
          planCoverageEmpty.hidden = false;
          planCoverageEmpty.textContent =
            payload.message || "Coverage gaps unavailable.";
        }
        return;
      }
      renderCoverageGaps(payload);
    } catch (err) {
      renderCoverageGaps({ no_case: [], all_disabled: [] });
      if (planCoverageEmpty) {
        planCoverageEmpty.hidden = false;
        planCoverageEmpty.textContent = "Could not load coverage gaps.";
      }
    }
  }

  function syncTraceDetail(row) {
    focusedTraceRow = row || null;
    if (planTraceDetailKey) {
      planTraceDetailKey.value = (row && row.story_key) || "";
    }
    if (planTraceDetailCase) {
      planTraceDetailCase.value = (row && row.primary_case_id) || "";
    }
    if (planTraceDetailFetch) {
      planTraceDetailFetch.value =
        (row && row.fetch_time_label) || "fetch time unknown";
    }
    if (planTraceOpenCase) {
      planTraceOpenCase.disabled = !(row && row.primary_case_id);
    }
    if (planTraceScanBody) {
      planTraceScanBody.querySelectorAll(".plan-trace-scan-row").forEach(
        function (tr) {
          const match =
            row &&
            (tr.dataset.storyKey || "") === (row.story_key || "") &&
            (tr.dataset.caseId || "") === (row.primary_case_id || "");
          tr.classList.toggle("is-focus", !!match);
        }
      );
    }
  }

  function renderTraceabilityMatrix(payload) {
    const rows = (payload && payload.rows) || [];
    if (planTraceMatrix) {
      planTraceMatrix._traceRows = rows;
      planTraceMatrix.dataset.rowCount = String(rows.length);
    }
    if (!planTraceScanBody) return;
    planTraceScanBody.innerHTML = "";
    if (planTraceEmpty) {
      planTraceEmpty.hidden = rows.length > 0;
      planTraceEmpty.textContent = rows.length
        ? ""
        : "Traceability: (no story rows)";
    }
    rows.forEach(function (r) {
      const bugs = (r.linked_bug_keys || []).join(", ") || "—";
      const known = r.known_issue ? "yes" : "no";
      const last = r.last_result || "not_loaded";
      const fetchLabel = r.fetch_time_label || "fetch time unknown";
      const tr = document.createElement("tr");
      tr.className = "plan-trace-scan-row plan-tabs-scan-row plan-trace-row";
      tr.dataset.caseId = r.primary_case_id || "";
      tr.dataset.storyKey = r.story_key || "";
      tr.dataset.fetchTime = fetchLabel;
      tr.setAttribute("role", "row");
      tr.title = r.primary_case_id
        ? "Open case " + r.primary_case_id + " · " + fetchLabel
        : "No case to open for this story · " + fetchLabel;
      const cells = [
        r.story_key || "?",
        r.case_count != null ? String(r.case_count) : "0",
        last,
        bugs,
        known,
      ];
      cells.forEach(function (text) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.appendChild(td);
      });
      tr.tabIndex = 0;
      tr.addEventListener("click", function () {
        syncTraceDetail(r);
        openTraceabilityRow(r);
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              planTraceScanBody.querySelectorAll(".plan-trace-scan-row")
            );
          },
          activate: function (row) {
            const sk = row.dataset.storyKey || "";
            const cid = row.dataset.caseId || "";
            const match = rows.find(function (x) {
              return (
                (x.story_key || "") === sk &&
                (x.primary_case_id || "") === cid
              );
            });
            if (match) {
              syncTraceDetail(match);
              openTraceabilityRow(match);
            }
          },
        });
      });
      planTraceScanBody.appendChild(tr);
    });
    if (rows.length) {
      const keep =
        rows.find(function (r) {
          return (
            focusedTraceRow &&
            r.story_key === focusedTraceRow.story_key &&
            r.primary_case_id === focusedTraceRow.primary_case_id
          );
        }) || rows[0];
      syncTraceDetail(keep);
    } else {
      syncTraceDetail(null);
    }
  }

  async function openTraceabilityRow(row) {
    if (!row) return;
    syncTraceDetail(row);
    if (!row.primary_case_id || !planCaseId) return;
    showPlanPanel("cases");
    planCaseId.value = row.primary_case_id;
    if (planCaseName && row.summary) planCaseName.value = row.summary;
    await refreshCaseDetail();
    if (typeof syncPlanCaseRowFocus === "function") syncPlanCaseRowFocus();
    if (planCaseId.focus) planCaseId.focus();
    if (planStatus) {
      planStatus.textContent =
        "Opened case " +
        row.primary_case_id +
        " for " +
        (row.story_key || "story");
    }
  }

  if (planTraceOpenCase) {
    planTraceOpenCase.addEventListener("click", function () {
      if (focusedTraceRow) openTraceabilityRow(focusedTraceRow);
    });
  }

  function renderPlanSearchResults(payload) {
    if (!planSearchResults) return;
    planSearchResults.innerHTML = "";
    const hits = (payload && payload.hits) || [];
    if (!hits.length) {
      planSearchResults.textContent =
        (payload && payload.message) ||
        (payload && payload.query
          ? "No matches in the active security level."
          : "Enter a search term.");
      return;
    }
    const hint = document.createElement("div");
    hint.textContent =
      hits.length +
      " hit" +
      (hits.length === 1 ? "" : "s") +
      " · " +
      (payload.security_level || "") +
      (payload.truncated ? " (truncated)" : "") +
      (payload.search_works_offline ? " · local (works offline)" : "");
    planSearchResults.appendChild(hint);
    hits.forEach(function (hit, idx) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "save-btn secondary";
      btn.style.display = "block";
      btn.style.width = "100%";
      btn.style.textAlign = "left";
      btn.style.marginTop = "0.35rem";
      btn.setAttribute("role", "listitem");
      const matched = (hit.matched_fields || []).join(", ");
      const fetchLabel = hit.fetch_time_label || "";
      btn.textContent =
        idx +
        1 +
        ". " +
        (hit.plan_name || hit.plan_id || "?") +
        (hit.case_name ? " · " + hit.case_name : "") +
        (hit.jira_key ? " · " + hit.jira_key : "") +
        (hit.failure_class ? " · " + hit.failure_class : "") +
        (matched ? " [" + matched + "]" : "") +
        (fetchLabel ? " · " + fetchLabel : "");
      btn.dataset.fetchTime = fetchLabel || "fetch time unknown";
      btn.title = hit.case_id
        ? "Open case " + hit.case_id + (fetchLabel ? " · " + fetchLabel : "")
        : "Open plan " + (hit.plan_id || "");
      btn.addEventListener("click", function () {
        openPlanSearchHit(hit);
      });
      planSearchResults.appendChild(btn);
    });
  }

  async function openPlanSearchHit(hit) {
    if (!hit || !hit.plan_id) return;
    await openPlan(hit.plan_id);
    if (hit.case_id && planCaseId) {
      planCaseId.value = hit.case_id;
      if (planCaseName && hit.case_name) planCaseName.value = hit.case_name;
      await refreshCaseDetail();
      if (planCaseId.focus) planCaseId.focus();
      if (planStatus) {
        planStatus.textContent =
          "Search hit → case " + hit.case_id + " in " + (hit.plan_name || hit.plan_id);
      }
    } else if (planStatus) {
      planStatus.textContent =
        "Search hit → plan " + (hit.plan_name || hit.plan_id) + " (no case)";
    }
  }

  async function runPlanSearch() {
    const q =
      planSearchQ && planSearchQ.value ? planSearchQ.value.trim() : "";
    if (planStatus) planStatus.textContent = q ? "Searching…" : "Enter a search term.";
    try {
      const res = await fetch(
        "/api/plans/search?q=" + encodeURIComponent(q)
      );
      const payload = await res.json();
      renderPlanSearchResults(payload);
      if (planStatus) {
        if (!q) {
          planStatus.textContent = payload.message || "Enter a search term.";
        } else {
          planStatus.textContent =
            (payload.count != null ? payload.count : 0) +
            " search hit(s) in " +
            (payload.security_level || "active level");
        }
      }
    } catch (err) {
      if (planSearchResults) planSearchResults.textContent = "Search failed.";
      if (planStatus) planStatus.textContent = "Search request failed.";
    }
  }

  async function refreshTraceabilityMatrix() {
    if (!openPlanId) {
      renderTraceabilityMatrix({ rows: [] });
      return;
    }
    const q =
      planTraceFilter && planTraceFilter.value
        ? planTraceFilter.value.trim()
        : "";
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/traceability?q=" +
          encodeURIComponent(q)
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        renderTraceabilityMatrix({ rows: [] });
        if (planTraceEmpty) {
          planTraceEmpty.hidden = false;
          planTraceEmpty.textContent =
            payload.message || "Traceability unavailable.";
        }
        return;
      }
      renderTraceabilityMatrix(payload);
    } catch (err) {
      renderTraceabilityMatrix({ rows: [] });
      if (planTraceEmpty) {
        planTraceEmpty.hidden = false;
        planTraceEmpty.textContent = "Could not load traceability matrix.";
      }
    }
  }

  function formatDurationMs(ms) {
    if (ms == null || ms === "") return "—";
    const n = Number(ms);
    if (!isFinite(n) || n < 0) return "—";
    if (n < 1000) return n + "ms";
    return (n / 1000).toFixed(1) + "s";
  }

  function fillHistorySelect(selectEl, runs, preferredId) {
    if (!selectEl) return;
    const keep = preferredId || selectEl.value || "";
    selectEl.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "(select run)";
    selectEl.appendChild(blank);
    (runs || []).forEach(function (r) {
      const opt = document.createElement("option");
      opt.value = r.id || "";
      const when = r.finished_at || r.started_at || "?";
      opt.textContent =
        (r.id || "?") +
        " · " +
        when +
        " · P" +
        (r.pass != null ? r.pass : 0) +
        "/F" +
        (r.fail != null ? r.fail : 0) +
        (r.tag ? " · #" + r.tag : "");
      selectEl.appendChild(opt);
    });
    if (keep) {
      selectEl.value = keep;
      if (selectEl.value !== keep) selectEl.value = "";
    }
  }

  function syncHistoryRadiosFromSelects() {
    if (!planHistoryScanBody) return;
    const aVal = planHistoryA ? planHistoryA.value : "";
    const bVal = planHistoryB ? planHistoryB.value : "";
    planHistoryScanBody.querySelectorAll('input[name="plan-hist-a"]').forEach(
      function (radio) {
        radio.checked = radio.value === aVal;
      }
    );
    planHistoryScanBody.querySelectorAll('input[name="plan-hist-b"]').forEach(
      function (radio) {
        radio.checked = radio.value === bVal;
      }
    );
  }

  function focusHistoryRunDetail(run) {
    if (!run) return;
    focusedHistoryRunId = run.id || "";
    if (planHistoryDetailId) planHistoryDetailId.value = run.id || "";
    if (planHistoryDetailWhen) {
      planHistoryDetailWhen.value = run.finished_at || run.started_at || "";
    }
    if (planHistoryDetailMeta) {
      planHistoryDetailMeta.textContent =
        "pass " +
        (run.pass != null ? run.pass : 0) +
        " · fail " +
        (run.fail != null ? run.fail : 0) +
        " · " +
        formatDurationMs(run.duration_ms) +
        (run.tag ? " · tag " + run.tag : "") +
        (run.known_issues ? " · known " + run.known_issues : "") +
        (run.error ? " · err " + run.error : "");
    }
    if (planHistoryScanBody) {
      planHistoryScanBody.querySelectorAll(".plan-history-scan-row").forEach(
        function (tr) {
          tr.classList.toggle(
            "is-focus",
            (tr.dataset.suiteRunId || "") === focusedHistoryRunId
          );
        }
      );
    }
  }

  function renderSuiteHistory(payload) {
    const runs = (payload && payload.runs) || [];
    if (!planHistoryScanBody) {
      if (planHistoryEmpty) {
        planHistoryEmpty.hidden = false;
        planHistoryEmpty.textContent = "Suite history: (no runs yet)";
      }
      fillHistorySelect(planHistoryA, [], "");
      fillHistorySelect(planHistoryB, [], "");
      if (planCompareOut) planCompareOut.textContent = "";
      return;
    }
    planHistoryScanBody.innerHTML = "";
    if (!runs.length) {
      if (planHistoryEmpty) {
        planHistoryEmpty.hidden = false;
        planHistoryEmpty.textContent = "Suite history: (no runs yet)";
      }
      fillHistorySelect(planHistoryA, [], "");
      fillHistorySelect(planHistoryB, [], "");
      if (planCompareOut) planCompareOut.textContent = "";
      if (planHistoryDetailId) planHistoryDetailId.value = "";
      if (planHistoryDetailWhen) planHistoryDetailWhen.value = "";
      if (planHistoryDetailMeta) {
        planHistoryDetailMeta.textContent = "Select a run row.";
      }
      focusedHistoryRunId = "";
      return;
    }
    if (planHistoryEmpty) {
      planHistoryEmpty.hidden = false;
      planHistoryEmpty.textContent =
        runs.length +
        " run" +
        (runs.length === 1 ? "" : "s") +
        " · " +
        (payload.security_level || "") +
        (payload.cross_level === false ? " (level-local)" : "");
    }
    const preferredA =
      planHistoryA && planHistoryA.value
        ? planHistoryA.value
        : runs[0] && runs[0].id;
    const preferredB =
      planHistoryB && planHistoryB.value
        ? planHistoryB.value
        : runs[1] && runs[1].id
          ? runs[1].id
          : "";
    fillHistorySelect(planHistoryA, runs, preferredA);
    fillHistorySelect(planHistoryB, runs, preferredB);
    runs.forEach(function (r) {
      const tr = document.createElement("tr");
      tr.className = "plan-history-scan-row plan-tabs-scan-row";
      tr.dataset.suiteRunId = r.id || "";
      tr.setAttribute("role", "row");
      const tdA = document.createElement("td");
      tdA.className = "plan-tabs-hit-cell";
      const radioA = document.createElement("input");
      radioA.type = "radio";
      radioA.name = "plan-hist-a";
      radioA.value = r.id || "";
      radioA.setAttribute("aria-label", "Compare A");
      radioA.addEventListener("click", function (ev) {
        ev.stopPropagation();
        if (planHistoryA) planHistoryA.value = r.id || "";
        if (planStatus) {
          planStatus.textContent =
            "Compare A=" +
            (planHistoryA && planHistoryA.value ? planHistoryA.value : "—") +
            " B=" +
            (planHistoryB && planHistoryB.value ? planHistoryB.value : "—");
        }
      });
      tdA.appendChild(radioA);
      const tdB = document.createElement("td");
      tdB.className = "plan-tabs-hit-cell";
      const radioB = document.createElement("input");
      radioB.type = "radio";
      radioB.name = "plan-hist-b";
      radioB.value = r.id || "";
      radioB.setAttribute("aria-label", "Compare B");
      radioB.addEventListener("click", function (ev) {
        ev.stopPropagation();
        if (planHistoryB) planHistoryB.value = r.id || "";
        if (planStatus) {
          planStatus.textContent =
            "Compare A=" +
            (planHistoryA && planHistoryA.value ? planHistoryA.value : "—") +
            " B=" +
            (planHistoryB && planHistoryB.value ? planHistoryB.value : "—");
        }
      });
      tdB.appendChild(radioB);
      const tdTime = document.createElement("td");
      tdTime.textContent = r.finished_at || r.started_at || "?";
      const tdDur = document.createElement("td");
      tdDur.textContent = formatDurationMs(r.duration_ms);
      const tdPass = document.createElement("td");
      tdPass.textContent = r.pass != null ? String(r.pass) : "0";
      const tdFail = document.createElement("td");
      tdFail.textContent = r.fail != null ? String(r.fail) : "0";
      const tdTag = document.createElement("td");
      tdTag.textContent = r.tag || "—";
      tr.appendChild(tdA);
      tr.appendChild(tdB);
      tr.appendChild(tdTime);
      tr.appendChild(tdDur);
      tr.appendChild(tdPass);
      tr.appendChild(tdFail);
      tr.appendChild(tdTag);
      tr.tabIndex = 0;
      tr.addEventListener("click", function () {
        focusHistoryRunDetail(r);
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          checkboxStop: ".plan-tabs-hit-cell",
          rows: function () {
            return Array.prototype.slice.call(
              planHistoryScanBody.querySelectorAll(".plan-history-scan-row")
            );
          },
          activate: function (row) {
            const rid = row.dataset.suiteRunId || "";
            const match = runs.find(function (x) {
              return (x.id || "") === rid;
            });
            if (match) focusHistoryRunDetail(match);
          },
        });
      });
      planHistoryScanBody.appendChild(tr);
    });
    syncHistoryRadiosFromSelects();
    const focusRun =
      runs.find(function (r) {
        return r && r.id === focusedHistoryRunId;
      }) || runs[0];
    focusHistoryRunDetail(focusRun);
  }

  function formatDurationDelta(ms) {
    if (ms == null || ms === "") return "";
    const n = Number(ms);
    if (!isFinite(n) || n === 0) return "±0";
    const sign = n > 0 ? "+" : "−";
    return sign + formatDurationMs(Math.abs(n));
  }

  function renderSuiteCompare(payload) {
    if (!planCompareOut) return;
    planCompareOut.innerHTML = "";
    if (!payload) {
      planCompareOut.textContent = "";
      return;
    }
    if (payload.status !== "ok") {
      planCompareOut.textContent =
        payload.message || payload.error || "Compare failed.";
      return;
    }
    const changes = payload.changes || [];
    const durationChanges = payload.duration_changes || [];
    const head = document.createElement("div");
    head.textContent =
      "Result changed " +
      (payload.changed != null ? payload.changed : changes.length) +
      " · duration changed " +
      (payload.duration_changed != null
        ? payload.duration_changed
        : durationChanges.length) +
      " · unchanged " +
      (payload.unchanged != null ? payload.unchanged : 0) +
      (payload.cross_level === false ? " · level-local" : "") +
      (payload.upload === false ? " · no upload" : "");
    planCompareOut.appendChild(head);
    const suiteDur = document.createElement("div");
    suiteDur.textContent =
      "Suite duration " +
      formatDurationMs(payload.duration_ms_a) +
      " → " +
      formatDurationMs(payload.duration_ms_b) +
      (payload.duration_delta_ms != null
        ? " (" + formatDurationDelta(payload.duration_delta_ms) + ")"
        : "");
    planCompareOut.appendChild(suiteDur);
    function bindCaseOpen(btn, c) {
      if (!c || !c.case_id) return;
      btn.title = "Open case " + c.case_id;
      btn.addEventListener("click", function () {
        if (planCaseId) planCaseId.value = c.case_id;
        if (planCaseName && c.case_name) planCaseName.value = c.case_name;
        refreshCaseDetail();
      });
    }
    if (!changes.length) {
      const none = document.createElement("div");
      none.textContent = "No cases changed result between these runs.";
      planCompareOut.appendChild(none);
    }
    changes.forEach(function (c) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "save-btn secondary";
      btn.style.display = "block";
      btn.style.width = "100%";
      btn.style.textAlign = "left";
      btn.style.marginTop = "0.35rem";
      btn.setAttribute("role", "listitem");
      const durBit =
        c.duration_ms_a != null || c.duration_ms_b != null
          ? " · " +
            formatDurationMs(c.duration_ms_a) +
            " → " +
            formatDurationMs(c.duration_ms_b) +
            (c.duration_delta_ms != null
              ? " (" + formatDurationDelta(c.duration_delta_ms) + ")"
              : "")
          : "";
      btn.textContent =
        (c.case_name || c.case_id || "?") +
        " · " +
        (c.result_a || "?") +
        " → " +
        (c.result_b || "?") +
        durBit +
        (c.known_issue
          ? " · " + (c.known_issue_label || "known")
          : "");
      bindCaseOpen(btn, c);
      planCompareOut.appendChild(btn);
    });
    if (durationChanges.length) {
      const durHead = document.createElement("div");
      durHead.style.marginTop = "0.5rem";
      durHead.textContent = "Duration changes (same result):";
      planCompareOut.appendChild(durHead);
      durationChanges.forEach(function (c) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "save-btn secondary";
        btn.style.display = "block";
        btn.style.width = "100%";
        btn.style.textAlign = "left";
        btn.style.marginTop = "0.35rem";
        btn.setAttribute("role", "listitem");
        btn.textContent =
          (c.case_name || c.case_id || "?") +
          " · " +
          (c.result || "?") +
          " · " +
          formatDurationMs(c.duration_ms_a) +
          " → " +
          formatDurationMs(c.duration_ms_b) +
          (c.duration_delta_ms != null
            ? " (" + formatDurationDelta(c.duration_delta_ms) + ")"
            : "") +
          (c.known_issue
            ? " · " + (c.known_issue_label || "known")
            : "");
        bindCaseOpen(btn, c);
        planCompareOut.appendChild(btn);
      });
    }
  }

  async function refreshSuiteHistory() {
    if (!openPlanId) {
      renderSuiteHistory({ runs: [] });
      return;
    }
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/suite-history"
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        renderSuiteHistory({ runs: [] });
        if (planHistoryEmpty) {
          planHistoryEmpty.hidden = false;
          planHistoryEmpty.textContent =
            payload.message || "Suite history unavailable.";
        }
        return;
      }
      renderSuiteHistory(payload);
    } catch (err) {
      renderSuiteHistory({ runs: [] });
      if (planHistoryEmpty) {
        planHistoryEmpty.hidden = false;
        planHistoryEmpty.textContent = "Could not load suite history.";
      }
    }
  }

  async function runSuiteCompare() {
    if (!openPlanId) {
      if (planCompareOut) planCompareOut.textContent = "Open a plan first.";
      return;
    }
    const a = planHistoryA && planHistoryA.value ? planHistoryA.value.trim() : "";
    const b = planHistoryB && planHistoryB.value ? planHistoryB.value.trim() : "";
    if (planStatus) planStatus.textContent = "Comparing suite runs…";
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/suite-compare?a=" +
          encodeURIComponent(a) +
          "&b=" +
          encodeURIComponent(b)
      );
      const payload = await res.json();
      renderSuiteCompare(payload);
      if (planStatus) {
        if (payload.status === "ok") {
          planStatus.textContent =
            "Compare: " +
            (payload.changed != null ? payload.changed : 0) +
            " changed";
        } else {
          planStatus.textContent = payload.message || "Compare failed.";
        }
      }
    } catch (err) {
      if (planCompareOut) planCompareOut.textContent = "Compare request failed.";
      if (planStatus) planStatus.textContent = "Compare request failed.";
    }
  }

  function renderAcceptanceDrift(payload) {
    if (!planDriftOut) return;
    if (!payload) {
      planDriftOut.hidden = true;
      planDriftOut.textContent = "";
      return;
    }
    const lines = [];
    if (payload.message) lines.push(payload.message);
    if (payload.stale_count != null) {
      lines.push("Stale count: " + payload.stale_count);
    }
    const items =
      payload.stale_items && payload.stale_items.length
        ? payload.stale_items
        : payload.checked || [];
    items.forEach(function (row, idx) {
      lines.push("");
      lines.push(
        idx +
          1 +
          ". " +
          (row.key || "?") +
          (row.stale ? " [STALE]" : " [ok]") +
          (row.read_ok === false ? " (read failed)" : "")
      );
      if (row.message) lines.push("   " + row.message);
      if (row.stale || (row.old_summary || row.new_summary)) {
        lines.push("   OLD summary: " + (row.old_summary || "(empty)"));
        lines.push("   NEW summary: " + (row.new_summary || "(empty)"));
        lines.push(
          "   OLD AC:\n" + (row.old_acceptance_criteria || "(empty)")
        );
        lines.push(
          "   NEW AC:\n" + (row.new_acceptance_criteria || "(empty)")
        );
      }
    });
    if (payload.runs_before != null) {
      lines.push("");
      lines.push(
        "Runs before: " +
          payload.runs_before +
          " · after: " +
          (payload.runs_after != null ? payload.runs_after : "?") +
          " · deleted: " +
          (payload.runs_deleted ? "yes" : "no")
      );
    }
    planDriftOut.hidden = false;
    planDriftOut.textContent = lines.join("\n");
  }

  async function postAcceptanceDrift(path) {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      renderAcceptanceDrift({
        message: "Open a plan with linked Jira keys first.",
        stale_items: [],
      });
      return null;
    }
    if (planStatus) planStatus.textContent = "Acceptance drift…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + path,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      renderAcceptanceDrift(payload);
      if (payload.status === "ok") {
        if (payload.plan) renderPlanCases(payload.plan);
        if (planStatus) planStatus.textContent = payload.message || "Done.";
        await loadPlanList(openPlanId);
      } else if (planStatus) {
        planStatus.textContent = payload.message || "Drift action failed.";
      }
      return payload;
    } catch (err) {
      renderAcceptanceDrift({
        message: "Could not reach acceptance-drift API.",
        stale_items: [],
      });
      if (planStatus) planStatus.textContent = "Acceptance drift failed.";
      return null;
    }
  }

  function applyOfflineNetworkActions(payload) {
    planOfflineState = payload || null;
    const actions = (payload && payload.network_actions) || [];
    const byId = {};
    actions.forEach(function (a) {
      if (a && a.id) byId[a.id] = a;
    });
    function gate(el, actionId) {
      if (!el) return;
      const action = byId[actionId];
      if (!action) return;
      const enable = !!action.enabled;
      el.disabled = !enable;
      if (!enable) {
        el.title = action.reason || "Jira unavailable — network action disabled.";
        el.setAttribute("data-offline-disabled", "1");
      } else {
        el.removeAttribute("data-offline-disabled");
        if (el.getAttribute("title") && el.getAttribute("title").indexOf("Jira") === 0) {
          el.removeAttribute("title");
        }
      }
    }
    gate(planDraftBtn, "draft_from_story");
    gate(planDraftProjectBtn, "draft_from_project");
    gate(planDriftCheckBtn, "acceptance_drift_check");
    gate(planDriftRefreshBtn, "acceptance_drift_refresh");
    gate(jiraReadBtn, "read_jira_issue");
    gate(document.getElementById("hud-lab-draft"), "draft_from_story");
  }

  async function refreshOfflineReadBanner() {
    try {
      const res = await fetch("/api/plans/offline-read");
      const payload = await res.json();
      applyOfflineNetworkActions(payload);
      if (planOfflineBanner) {
        if (payload.offline) {
          planOfflineBanner.hidden = false;
          planOfflineBanner.dataset.offline = "1";
          planOfflineBanner.textContent =
            payload.message ||
            "Jira is down — search and matrix use last stored keys. Network actions disabled.";
        } else {
          planOfflineBanner.hidden = true;
          planOfflineBanner.dataset.offline = "0";
          planOfflineBanner.textContent = "";
        }
      }
      return payload;
    } catch (err) {
      if (planOfflineBanner) {
        planOfflineBanner.hidden = true;
        planOfflineBanner.dataset.offline = "0";
      }
      return null;
    }
  }

  async function refreshPlanDegradedHint() {
    if (!planDegradedHint) return;
    try {
      const res = await fetch("/api/degraded-mode");
      const payload = await res.json();
      const msgs = payload.messages || {};
      const parts = Object.keys(msgs).map(function (k) {
        return msgs[k];
      });
      if (parts.length) {
        planDegradedHint.hidden = false;
        planDegradedHint.textContent = parts.join(" ");
      } else {
        planDegradedHint.hidden = true;
        planDegradedHint.textContent = "";
      }
    } catch (err) {
      planDegradedHint.hidden = true;
    }
    await refreshOfflineReadBanner();
  }

  async function refreshCaseDetail() {
    if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
      if (planCaseDetail) planCaseDetail.hidden = true;
      syncFrameworkStubHonestyUi();
      return;
    }
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/cases/" +
          encodeURIComponent(planCaseId.value.trim())
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !planCaseDetail) return;
      const ki = payload.known_issue || {};
      const caseTags = Array.isArray(payload.tags) ? payload.tags : [];
      const q = payload.quarantine || {};
      const flake = payload.flake || {};
      const lastFail = payload.last_failure || flake.last_failure || null;
      const lines = [
        "Case: " + (payload.name || ""),
        "Jira: " + (payload.jira_key || "—"),
        "Tags: " + (caseTags.length ? caseTags.join(", ") : "—"),
        "Priority: " + (payload.priority != null ? payload.priority : 0),
        "Enabled: " + (payload.enabled === false ? "no" : "yes"),
        "Archived: " + (payload.archived ? "yes" : "no"),
        "Quarantined: " +
          (payload.quarantined || q.quarantined
            ? "yes (skipped on run, not a pass)"
            : q.expired
              ? "expired — selectable again"
              : "no"),
        q.reason ? "Quarantine reason: " + q.reason : "",
        q.expires_at ? "Quarantine expires: " + q.expires_at : "",
        "Flake: " +
          (payload.flake_label || flake.flake_label || "0/0") +
          " fails in last " +
          (flake.window || 10),
        "Runs kept: " + (payload.run_count != null ? payload.run_count : 0),
        "Source: " + (payload.source_kind || "manual-draft") + " — " + (payload.source_ref || "—"),
        payload.manual_draft ? "Marked manual-draft (no Jira/doc source)" : "",
        "Step timeout: " +
          (payload.step_timeout_ms != null ? payload.step_timeout_ms : 10000) +
          " ms",
        payload.note ? "Case note: " + payload.note : "",
        payload.tester_note ? "Run note: " + payload.tester_note : "",
        payload.known_label ? "Label: known (not a new regression)" : "",
        ki.note ? "Known note: " + ki.note : "",
        ki.jira_key ? "Known Jira: " + ki.jira_key : "",
        payload.last_run_summary ? "Last run: " + payload.last_run_summary : "Last run: (none)",
        lastFail
          ? "Last failure: " +
            (lastFail.result || "fail") +
            (lastFail.failure_class ? " · " + lastFail.failure_class : "") +
            (lastFail.id ? " · " + lastFail.id : "")
          : "",
      ].filter(Boolean);
      planCaseDetail.hidden = false;
      planCaseDetail.textContent = lines.join("\n");
      (function fillPlanEvidence() {
        const last = payload.last_run || null;
        const shotPath = String(
          payload.evidence_shot ||
            (function findShot() {
              const ev = (last && last.evidence) || [];
              for (let i = 0; i < ev.length; i++) {
                const text = String(ev[i] || "");
                if (text.toLowerCase().indexOf(".png") >= 0) return text;
              }
              return "";
            })() ||
            ""
        );
        const tracePath = (function findTrace() {
          const ev = (last && last.evidence) || [];
          for (let i = 0; i < ev.length; i++) {
            const text = String(ev[i] || "");
            if (/\.zip$/i.test(text) && /trace/i.test(text)) return text;
          }
          for (let i = 0; i < ev.length; i++) {
            const text = String(ev[i] || "");
            if (/\.zip$/i.test(text)) return text;
          }
          return "";
        })();
        const parts = [];
        if (last) {
          parts.push(String(last.result || "pending"));
          if (last.finished_at || last.started_at || last.created_at) {
            parts.push(
              String(last.finished_at || last.started_at || last.created_at).slice(
                0,
                19
              )
            );
          } else if (last.duration_ms != null) {
            parts.push(last.duration_ms + "ms");
          }
          if (last.failure_class) parts.push(String(last.failure_class));
        } else if (payload.last_run_summary) {
          parts.push(String(payload.last_run_summary));
        }
        const root = evidenceFirstRoot("plan-case-evidence-first");
        fillEvidenceFirst(root, {
          force: true,
          summary: parts.length ? parts.join(" · ") : "No run yet",
          link: "",
          hasScreenshot: !!shotPath,
          tracePath: tracePath,
          hasTrace: !!tracePath,
        });
        const caseId =
          payload.case_id ||
          (planCaseId && planCaseId.value ? planCaseId.value.trim() : "") ||
          "";
        const metaParts = [];
        if (last) {
          const dur = formatRunStoryDuration(last.duration_ms);
          if (dur) metaParts.push(dur);
          if (last.failure_class) metaParts.push(String(last.failure_class));
          else if ((payload.tags || caseTags || []).length) {
            metaParts.push(String((payload.tags || caseTags)[0]));
          }
          if (last.sandbox) metaParts.push(String(last.sandbox));
          else if (last.environment_name) {
            metaParts.push(String(last.environment_name));
          }
          const when = last.finished_at || last.started_at || "";
          if (when) {
            metaParts.push(
              String(when).slice(11, 16) || String(when).slice(0, 19)
            );
          }
        }
        let capturedPages = Array.isArray(payload.evidence_captured_pages)
          ? payload.evidence_captured_pages.slice()
          : [];
        if (!capturedPages.length && shotPath) {
          const fail = (Array.isArray(last.step_outcomes) ? last.step_outcomes : []).find(
            function (s) {
              const st = String((s && s.status) || "").toLowerCase();
              return st === "fail" || st === "error";
            }
          );
          const outcomes = Array.isArray(last.step_outcomes)
            ? last.step_outcomes
            : [];
          const attach = fail || outcomes[outcomes.length - 1] || null;
          capturedPages = [
            {
              path: shotPath,
              step_index: attach ? attach.index : null,
              label: attach
                ? String(attach.label || attach.action || "Step")
                : "Captured page",
              status: String(
                (attach && attach.status) || last.result || "pending"
              ),
            },
          ];
        }
        planDeepViewState = last
          ? {
              lastRun: last,
              planId: openPlanId || "",
              caseId: caseId,
              runId: String((last && last.id) || "").trim(),
              caseName: String(payload.name || caseId || "Case"),
              result: last.result,
              meta: metaParts.join(" · "),
              outcomes: Array.isArray(last.step_outcomes)
                ? last.step_outcomes
                : [],
              pages: capturedPages,
              shotPath: shotPath,
              emptyReason: payload.evidence_empty_reason || "",
              tracePath: tracePath,
            }
          : null;
        if (!last) closePlanRunEvidenceDeep();
        fillPlanRunStory(root, {
          lastRun: last,
          shotPath: shotPath,
          emptyReason: payload.evidence_empty_reason || "",
          tags: payload.tags || caseTags || [],
          planId: openPlanId || "",
          caseId: caseId,
        });
      })();
      syncPlanCaseRowFocus();
      if (planCaseName && payload.name) planCaseName.value = payload.name;
      if (planCaseNote && payload.note != null) planCaseNote.value = payload.note || "";
      if (planCaseTags) planCaseTags.value = caseTags.join(", ");
      if (planCasePriority) {
        planCasePriority.value =
          payload.priority != null ? String(payload.priority) : "0";
      }
      if (planCaseStepTimeout) {
        planCaseStepTimeout.value =
          payload.step_timeout_ms != null
            ? String(payload.step_timeout_ms)
            : "10000";
      }
      if (planCaseEnabled) planCaseEnabled.checked = payload.enabled !== false;
      if (planCaseArchived) planCaseArchived.checked = !!payload.archived;
      if (planQuarantineReason && q.reason != null) {
        planQuarantineReason.value = q.reason || "";
      }
      if (planQuarantineExpires && q.expires_at) {
        planQuarantineExpires.value = q.expires_at;
      }
      if (planRunNote) planRunNote.value = payload.tester_note || "";
      if (planKnownNote) planKnownNote.value = ki.note || "";
      if (planKnownJira) planKnownJira.value = ki.jira_key || "";
      if (payload.last_run && payload.last_run.id) {
        lastCaseRunId = payload.last_run.id;
        if (planRunFailureClass && payload.last_run.failure_class) {
          planRunFailureClass.value = payload.last_run.failure_class;
        }
      } else {
        lastCaseRunId = "";
        if (planRunFailureClass) planRunFailureClass.value = "";
      }
      syncPlanCaseTriageStrip(payload.last_run || null);
      syncFrameworkStubHonestyUi();
    } catch (err) {
      if (planCaseDetail) planCaseDetail.hidden = true;
      syncPlanCaseTriageStrip(null);
      syncFrameworkStubHonestyUi();
    }
  }

  async function loadPlanList(selectId) {
    if (!planList) return;
    try {
      const res = await fetch("/api/plans");
      const payload = await res.json();
      const plans = payload.plans || [];
      planList.innerHTML = "";
      if (!plans.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "(none yet)";
        planList.appendChild(opt);
      } else {
        plans.forEach(function (p) {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent =
            (p.name || p.id) + " — " + (p.case_count || 0) + " case(s)";
          planList.appendChild(opt);
        });
      }
      if (selectId) planList.value = selectId;
    } catch (err) {
      if (planStatus) planStatus.textContent = "Could not list plans.";
    }
  }

  async function openPlan(planId) {
    if (!planId) return;
    if (planStatus) planStatus.textContent = "Loading plan…";
    try {
      const res = await fetch("/api/plans/" + encodeURIComponent(planId));
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent = payload.message || "Plan not found.";
        }
        return;
      }
      openPlanId = payload.plan.id;
      lastSuiteRunId = "";
      if (payload.plan.suite_runs && payload.plan.suite_runs.length) {
        const finished = payload.plan.suite_runs.filter(function (r) {
          return r && r.finished_at;
        });
        if (finished.length) {
          lastSuiteRunId = finished[finished.length - 1].id || "";
        }
      }
      await refreshFlakeReport();
      renderPlanCases(payload.plan);
      await refreshCoverageGaps();
      await refreshTraceabilityMatrix();
      await refreshSuiteHistory();
      if (planList) planList.value = openPlanId;
      if (planStatus) {
        planStatus.textContent =
          "Open: " +
          (payload.plan.name || openPlanId) +
          " (" +
          ((payload.plan.suite && payload.plan.suite.cases) || []).length +
          " cases)";
      }
      await refreshPlanDegradedHint();
      await refreshCaseDetail();
    } catch (err) {
      if (planStatus) planStatus.textContent = "Could not open plan.";
    }
  }

  function selectedCaseIndex() {
    const cid = planCaseId && planCaseId.value ? planCaseId.value.trim() : "";
    if (!cid) return -1;
    for (let i = 0; i < openPlanCases.length; i++) {
      if (openPlanCases[i].id === cid) return i;
    }
    return -1;
  }

  function applySecurityStatus(payload) {
    if (!payload) return;
    if (secLevel && payload.security_level) {
      secLevel.value = payload.security_level;
    }
    if (secProfile) {
      secProfile.textContent =
        "Browser profile: " + (payload.browser_profile || "—");
    }
    if (typeof updateHudSecurity === "function") {
      updateHudSecurity(payload.security_level || "");
    }
  }

  async function loadSecurityStatus() {
    try {
      const res = await fetch("/api/security-level");
      if (!res.ok) return;
      applySecurityStatus(await res.json());
      pendingSecurityLevel = "";
      if (secConfirm) secConfirm.disabled = true;
      if (secStatus) secStatus.textContent = "Ready";
    } catch (err) {
      if (secStatus) secStatus.textContent = "Could not load security level.";
    }
  }

  function selectedPrivacyCategories() {
    return Object.keys(privChecks).filter(function (key) {
      return privChecks[key] && privChecks[key].checked;
    });
  }

  function applyPrivacyStatus(payload) {
    if (!payload) return;
    if (privTelemetry) {
      privTelemetry.textContent =
        "Telemetry: " +
        (payload.telemetry_enabled ? "on" : "off (default)") +
        ". Consent required for extracted data.";
    }
    if (privInventory && payload.categories) {
      const parts = Object.keys(payload.categories).map(function (key) {
        const info = payload.categories[key] || {};
        if (!info.exists) return key + ": none";
        return key + ": " + (info.items || 0) + " item(s)";
      });
      privInventory.textContent = "Local artifacts: " + parts.join("; ");
    }
  }

  async function loadPrivacyStatus() {
    try {
      const res = await fetch("/api/privacy");
      if (!res.ok) return;
      applyPrivacyStatus(await res.json());
      pendingPrivacyCategories = null;
      if (privConfirm) privConfirm.disabled = true;
      if (privStatus) privStatus.textContent = "Ready";
    } catch (err) {
      if (privStatus) privStatus.textContent = "Could not load privacy status.";
    }
  }

  async function loadRedactionStatus() {
    if (!redactionStatusEl) return;
    try {
      const res = await fetch("/api/redaction");
      const data = await res.json();
      if (!data || data.status !== "ok") {
        redactionStatusEl.textContent = "Redaction: unavailable";
        return;
      }
      redactionStatusEl.textContent =
        "Redaction: patterns on · stored tokens on · OCR off · " +
        "configured secrets in store: " +
        (data.stored_secrets_configured || 0) +
        " (values never shown)";
      if (redactionShotWarn) {
        if (data.screenshot_warning) {
          redactionShotWarn.hidden = false;
          redactionShotWarn.textContent = data.screenshot_warning;
        } else {
          redactionShotWarn.hidden = true;
          redactionShotWarn.textContent = "";
        }
      }
    } catch (err) {
      redactionStatusEl.textContent = "Redaction: could not load.";
    }
  }

  function fillBackupSelect(rows) {
    if (!backupSelect) return;
    const previous = backupSelect.value || pendingBackupPath || "";
    backupSelect.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = rows && rows.length ? "— select a backup —" : "— no backups yet —";
    backupSelect.appendChild(blank);
    (rows || []).forEach(function (row) {
      const opt = document.createElement("option");
      opt.value = row.path || "";
      opt.textContent =
        (row.filename || "backup") +
        " · " +
        (row.security_level || "?") +
        (row.include_secrets ? " · secrets" : "") +
        (row.bytes ? " · " + row.bytes + " B" : "");
      backupSelect.appendChild(opt);
    });
    if (previous) {
      backupSelect.value = previous;
      if (backupSelect.value !== previous) backupSelect.value = "";
    }
    if (secBackupScanBody) {
      secBackupScanBody.innerHTML = "";
      if (!rows || !rows.length) {
        const empty = document.createElement("tr");
        empty.className = "sec-scan-empty";
        empty.setAttribute("data-scan-quiet-empty", "1");
        const td = document.createElement("td");
        td.colSpan = 3;
        td.textContent = "No backups yet";
        empty.appendChild(td);
        secBackupScanBody.appendChild(empty);
        focusBackupRow("", "Restore");
        return;
      }
      rows.forEach(function (row, idx) {
        const tr = document.createElement("tr");
        tr.className = "sec-scan-row";
        tr.setAttribute("data-backup-path", row.path || "");
        tr.tabIndex = 0;
        const when = row.filename || row.created_at || row.path || "backup";
        const tdWhen = document.createElement("td");
        tdWhen.textContent = when;
        const tdLevel = document.createElement("td");
        tdLevel.textContent = row.security_level || "?";
        const tdSecrets = document.createElement("td");
        tdSecrets.textContent = row.include_secrets ? "Yes" : "No";
        tr.appendChild(tdWhen);
        tr.appendChild(tdLevel);
        tr.appendChild(tdSecrets);
        tr.addEventListener("click", function () {
          focusBackupRow(row.path || "", when);
        });
        tr.addEventListener("keydown", function (ev) {
          onScanRowKeydown(ev, {
            row: tr,
            rows: function () {
              return Array.prototype.slice.call(
                secBackupScanBody.querySelectorAll(".sec-scan-row")
              );
            },
            activate: function (rowEl) {
              const p = rowEl.getAttribute("data-backup-path") || "";
              const label =
                (rowEl.querySelector("td") &&
                  rowEl.querySelector("td").textContent) ||
                "Restore";
              focusBackupRow(p, label);
            },
          });
        });
        secBackupScanBody.appendChild(tr);
        if ((previous && previous === (row.path || "")) || (!previous && idx === 0)) {
          focusBackupRow(row.path || "", when);
        }
      });
      if (previous && backupSelect && backupSelect.value !== previous) {
        focusBackupRow("", "Restore");
      }
    }
  }

  async function loadBackupStatus() {
    try {
      const res = await fetch("/api/backup?limit=20");
      const data = await res.json();
      if (backupSummary) {
        backupSummary.textContent =
          "Active " +
          (data.security_level || "?") +
          ": " +
          (data.plans_count || 0) +
          " plan(s), " +
          (data.evidence_indexes_count || 0) +
          " evidence index(es). Secrets default off. Cloud: off.";
      }
      fillBackupSelect((data && data.recent_backups) || []);
      pendingBackupPath = "";
      if (backupRestoreConfirm) backupRestoreConfirm.disabled = true;
      if (backupStatus && backupStatus.textContent === "Ready") {
        /* keep Ready */
      } else if (backupStatus && !pendingBackupPath) {
        backupStatus.textContent = "Ready";
      }
    } catch (err) {
      if (backupSummary) backupSummary.textContent = "Backup: could not load.";
      if (backupStatus) backupStatus.textContent = "Could not load backups.";
    }
  }

  async function loadLocalAudit() {
    if (!localAuditList) return;
    try {
      const res = await fetch("/api/local-audit?limit=40");
      const data = await res.json();
      localAuditList.innerHTML = "";
      const rows = (data && data.entries) || [];
      if (!rows.length) {
        const empty = document.createElement("tr");
        empty.className = "sec-scan-empty";
        empty.setAttribute("data-scan-quiet-empty", "1");
        const td = document.createElement("td");
        td.colSpan = 3;
        td.textContent = "No local side-effect events yet.";
        empty.appendChild(td);
        localAuditList.appendChild(empty);
        focusAuditEntry("No local side-effect events yet.");
      } else {
        rows.forEach(function (row, idx) {
          const tr = document.createElement("tr");
          tr.className = "sec-scan-row";
          tr.tabIndex = 0;
          const refBits = [
            row.plan_id ? "plan " + row.plan_id : "",
            row.case_id ? "case " + row.case_id : "",
            row.security_level || "",
            row.session_id ? "session " + row.session_id : "",
          ].filter(Boolean);
          const tdTime = document.createElement("td");
          tdTime.textContent = row.timestamp || "";
          const tdAction = document.createElement("td");
          tdAction.textContent = row.action || "";
          const tdRef = document.createElement("td");
          tdRef.textContent = refBits.join(" · ") || "—";
          tr.appendChild(tdTime);
          tr.appendChild(tdAction);
          tr.appendChild(tdRef);
          const summary =
            [row.action || "", refBits.join(" · "), row.security_level || ""]
              .filter(Boolean)
              .join(" · ") || "Entry";
          tr.addEventListener("click", function () {
            document.querySelectorAll("#sec-audit-scan .sec-scan-row").forEach(function (r) {
              r.classList.remove("is-focus");
            });
            tr.classList.add("is-focus");
            focusAuditEntry(summary);
          });
          tr.addEventListener("keydown", function (ev) {
            onScanRowKeydown(ev, {
              row: tr,
              rows: function () {
                return Array.prototype.slice.call(
                  localAuditList.querySelectorAll(".sec-scan-row")
                );
              },
              activate: function (rowEl) {
                rowEl.click();
              },
            });
          });
          localAuditList.appendChild(tr);
          if (idx === 0) {
            tr.classList.add("is-focus");
            focusAuditEntry(summary);
          }
        });
      }
      if (localAuditStatus) {
        localAuditStatus.textContent =
          "Jira write audit remains" +
          (data && data.jira_write_audit_exists ? " (file present)" : "") +
          ". Cloud SIEM: off.";
      }
    } catch (err) {
      if (localAuditList) {
        localAuditList.innerHTML = "";
        const empty = document.createElement("tr");
        empty.className = "sec-scan-empty";
        const td = document.createElement("td");
        td.colSpan = 3;
        td.textContent = "Could not load local audit.";
        empty.appendChild(td);
        localAuditList.appendChild(empty);
      }
      if (localAuditStatus) localAuditStatus.textContent = "Could not load local audit.";
      focusAuditEntry("Could not load local audit.");
    }
  }

  async function postPrivacyDelete(categories, confirm) {
    const res = await fetch("/api/privacy/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ categories: categories, confirm: !!confirm }),
    });
    return { ok: res.ok, payload: await res.json() };
  }

  async function postSecurityLevel(level, confirm) {
    const res = await fetch("/api/security-level", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ security_level: level, confirm: !!confirm }),
    });
    return { ok: res.ok, payload: await res.json() };
  }

  function setDeskScanStatus(label, kind) {
    if (!deskScanStatus) return;
    const pill = document.createElement("span");
    pill.className =
      "desk-pill" +
      (kind === "ok"
        ? " desk-pill-ok"
        : kind === "warn"
          ? " desk-pill-warn"
          : " desk-pill-idle");
    pill.textContent = label || "—";
    deskScanStatus.replaceChildren(pill);
  }

  function focusDesktopDetail() {
    if (deskScanRow) deskScanRow.classList.add("is-focus");
    if (deskDetail && typeof deskDetail.scrollIntoView === "function") {
      try {
        deskDetail.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } catch (err) {
        /* ignore */
      }
    }
    if (deskExe) {
      try {
        deskExe.focus({ preventScroll: true });
      } catch (err) {
        deskExe.focus();
      }
    }
  }

  function applyDesktopPlugin(payload) {
    if (!payload) return;
    if (deskEnabled) {
      deskEnabled.checked = !!payload.plugin_desktop_enabled;
    }
    const path = (payload.target_app_path || "").trim();
    if (deskPath) {
      deskPath.textContent = path || "—";
      deskPath.title = path || "No path set — pass a path on Run smoke or override in detail";
    }
    if (payload.plugin_desktop_enabled) {
      setDeskScanStatus(path ? "Ready" : "No path", path ? "ok" : "idle");
    } else {
      setDeskScanStatus("Disabled", "warn");
    }
    if (deskLastSmoke) deskLastSmoke.textContent = deskLastSmokeText;
    fillEvidenceFirst(evidenceFirstRoot("desk-evidence-first"), {
      force: true,
      summary: deskLastSmokeText || "—",
      hasScreenshot: false,
    });
  }

  async function loadDesktopPlugin() {
    try {
      const res = await fetch("/api/desktop-plugin");
      if (!res.ok) return;
      applyDesktopPlugin(await res.json());
      if (deskStatus) deskStatus.textContent = "Ready";
    } catch (err) {
      if (deskStatus) deskStatus.textContent = "Could not load desktop plugin.";
    }
  }

  function suiteReadyStatusText() {
    const saved = String(suiteSavedPath || "").trim();
    return saved
      ? "Ready · Saved: " + saved
      : "Ready · Saved: (not set)";
  }

  function setSuiteReadyStatus() {
    if (suiteStatus) suiteStatus.textContent = suiteReadyStatusText();
  }

  function applyPlaywrightSuite(payload) {
    if (!payload) return;
    const saved = payload.playwright_suite_path || "";
    suiteSavedPath = saved;
    if (suitePath && saved && !suitePath.value) {
      suitePath.value = saved;
    }
    const discovered = payload.discovered;
    if (discovered && Array.isArray(discovered.specs) && discovered.specs.length) {
      renderSuiteList(
        discovered.specs.map(function (s) {
          return { title: s, file: s, line: null };
        }),
        "filesystem"
      );
    }
  }

  function suiteRowKey(file, grep) {
    return String(file || "") + "\0" + String(grep || "");
  }

  function clearSuiteFocus() {
    suiteSelected = { test_file: "", grep: "", title: "" };
    if (suiteScanBody) {
      suiteScanBody.querySelectorAll(".suite-scan-row.is-focus").forEach(function (el) {
        el.classList.remove("is-focus");
      });
    }
    if (suiteDetailTitle) suiteDetailTitle.textContent = "No test focused";
    if (suiteDetailHint) {
      suiteDetailHint.textContent =
        "Select a row. Checkbox state is independent of focus.";
    }
    if (suiteDetailName) suiteDetailName.value = "";
    if (suiteDetailFile) suiteDetailFile.value = "";
    if (suiteDetailGrep) suiteDetailGrep.value = "";
    if (suiteDetailLast) suiteDetailLast.textContent = "Last result: —";
    hideEvidenceFirst(evidenceFirstRoot("suite-evidence-first"));
    if (suiteRunFocused) suiteRunFocused.disabled = true;
    if (suiteCopyPath) suiteCopyPath.disabled = true;
  }

  function clearSuiteSelection() {
    clearSuiteFocus();
    if (suiteScanBody) {
      suiteScanBody.querySelectorAll('input[type="checkbox"]').forEach(function (cb) {
        cb.checked = false;
      });
    }
  }

  function countSuiteChecked() {
    if (!suiteScanBody) return 0;
    return suiteScanBody.querySelectorAll('input[type="checkbox"]:checked').length;
  }

  function getSuiteCheckedRows() {
    if (!suiteScanBody) return [];
    const out = [];
    suiteScanBody.querySelectorAll(".suite-scan-row").forEach(function (tr) {
      const cb = tr.querySelector('input[type="checkbox"]');
      if (!cb || !cb.checked) return;
      out.push({
        test_file: tr.dataset.testFile || "",
        grep: tr.dataset.grep || "",
        title: tr.dataset.title || "",
      });
    });
    return out;
  }

  function updateSuiteListStatus(source) {
    if (!suiteStatus || !suiteScanBody) return;
    const n = suiteScanBody.querySelectorAll(".suite-scan-row").length;
    const checked = countSuiteChecked();
    const base =
      "Listed " + n + " item(s)" + (source ? " (" + source + ")" : "");
    suiteStatus.textContent =
      checked > 0 ? base + " · " + checked + " selected" : base + ".";
  }

  function focusSuiteDetail(tr, opts) {
    if (!tr) return;
    if (suiteScanBody) {
      suiteScanBody.querySelectorAll(".suite-scan-row.is-focus").forEach(function (el) {
        el.classList.remove("is-focus");
      });
    }
    tr.classList.add("is-focus");
    const file = tr.dataset.testFile || "";
    const grep = tr.dataset.grep || "";
    const title = tr.dataset.title || file || "test";
    suiteSelected = { test_file: file, grep: grep, title: title };
    if (suiteDetailTitle) suiteDetailTitle.textContent = title;
    if (suiteDetailHint) {
      suiteDetailHint.textContent =
        "Focused row. Checkbox state is independent of focus.";
    }
    if (suiteDetailName) suiteDetailName.value = title;
    if (suiteDetailFile) suiteDetailFile.value = file;
    if (suiteDetailGrep) suiteDetailGrep.value = grep || title;
    const last = suiteLastByKey[suiteRowKey(file, grep)];
    if (suiteDetailLast) {
      suiteDetailLast.textContent = last
        ? "Last result: " + last
        : "Last result: —";
    }
    fillEvidenceFirst(evidenceFirstRoot("suite-evidence-first"), {
      force: true,
      summary: last ? "Last result: " + last : "Last result: —",
      hasScreenshot: false,
    });
    if (suiteRunFocused) suiteRunFocused.disabled = !(file || grep);
    if (suiteCopyPath) suiteCopyPath.disabled = !file;
    if (opts && opts.focusField && suiteDetailName) {
      try {
        suiteDetailName.focus();
      } catch (err) {
        /* ignore */
      }
    }
  }

  function renderSuiteList(items, source) {
    if (!suiteScanBody) return;
    suiteScanBody.innerHTML = "";
    clearSuiteFocus();
    const rows = Array.isArray(items) ? items : [];
    if (suiteListEmpty) {
      suiteListEmpty.hidden = rows.length > 0;
      if (!rows.length) {
        suiteListEmpty.textContent =
          "No tests listed yet. Discover or List tests for the project path.";
      }
    }
    const statusLabel = source === "filesystem" ? "Listed" : "Ready";
    rows.forEach(function (row, idx) {
      const file = (row && (row.file || row.title)) || "";
      const title = (row && (row.title || row.file)) || "test " + (idx + 1);
      const grep = title !== file ? title : "";
      const key = suiteRowKey(file, grep);
      const last = suiteLastByKey[key];
      const tr = document.createElement("tr");
      tr.className = "suite-scan-row";
      tr.tabIndex = 0;
      tr.dataset.testFile = file;
      tr.dataset.grep = grep;
      tr.dataset.title = title;
      tr.setAttribute("role", "row");

      const tdHit = document.createElement("td");
      tdHit.className = "suite-hit";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.setAttribute("aria-label", "Select " + title);
      cb.setAttribute("data-suite-checkbox-stop", "1");
      cb.addEventListener("click", function (ev) {
        ev.stopPropagation();
      });
      cb.addEventListener("change", function (ev) {
        ev.stopPropagation();
        updateSuiteListStatus(source);
      });
      tdHit.appendChild(cb);

      const tdStatus = document.createElement("td");
      const statusPill = document.createElement("span");
      statusPill.className =
        "suite-pill " + (statusLabel === "Ready" ? "ok" : "idle");
      statusPill.textContent = statusLabel;
      tdStatus.appendChild(statusPill);

      const tdTitle = document.createElement("td");
      tdTitle.textContent = title;

      const tdFile = document.createElement("td");
      tdFile.className = "mono";
      tdFile.textContent = file || "—";

      const tdLast = document.createElement("td");
      const lastPill = document.createElement("span");
      if (last && /^Pass/i.test(last)) {
        lastPill.className = "suite-pill ok";
        lastPill.textContent = "Pass";
      } else if (last && /^Fail/i.test(last)) {
        lastPill.className = "suite-pill warn";
        lastPill.textContent = "Fail";
      } else {
        lastPill.className = "suite-pill idle";
        lastPill.textContent = "—";
      }
      tdLast.appendChild(lastPill);

      tr.appendChild(tdHit);
      tr.appendChild(tdStatus);
      tr.appendChild(tdTitle);
      tr.appendChild(tdFile);
      tr.appendChild(tdLast);

      tr.addEventListener("click", function (ev) {
        if (
          ev.target &&
          ev.target.closest &&
          ev.target.closest('[data-suite-checkbox-stop="1"]')
        ) {
          return;
        }
        focusSuiteDetail(tr, { focusField: false });
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          checkboxStop: '[data-suite-checkbox-stop="1"]',
          rows: function () {
            return Array.prototype.slice.call(
              suiteScanBody.querySelectorAll(".suite-scan-row")
            );
          },
          activate: function (row) {
            focusSuiteDetail(row, { focusField: false });
          },
        });
      });

      suiteScanBody.appendChild(tr);
    });
    if (rows.length && suiteStatus) {
      updateSuiteListStatus(source);
    }
  }

  async function loadPlaywrightSuite() {
    try {
      const res = await fetch("/api/playwright-suite");
      if (!res.ok) return;
      const payload = await res.json();
      applyPlaywrightSuite(payload);
      setSuiteReadyStatus();
      const path = suitePathValue();
      if (path) {
        try {
          const listRes = await fetch("/api/playwright-suite/list", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ suite_path: path }),
          });
          const listPayload = await listRes.json();
          if (listRes.ok && listPayload.status === "ok") {
            renderSuiteList(listPayload.tests || [], listPayload.source || "list");
          }
        } catch (listErr) {
          /* keep Ready / discovered specs if list fails */
        }
      }
    } catch (err) {
      if (suiteStatus) suiteStatus.textContent = "Could not load Playwright suite settings.";
    }
  }

  function msReadyLabel(status) {
    const s = String(status || "idle").toLowerCase();
    if (s === "prepared") return "Prepared";
    if (s === "error") return "Error";
    if (s === "planned") return "Planned";
    return "Idle";
  }

  function msReadyPillClass(status) {
    const s = String(status || "idle").toLowerCase();
    if (s === "prepared") return "ms-pill ms-pill-ok";
    if (s === "error") return "ms-pill ms-pill-warn";
    return "ms-pill ms-pill-idle";
  }

  function resetMsRemoveConfirm() {
    if (msRemoveConfirm) {
      msRemoveConfirm.disabled = true;
    }
  }

  function focusSandboxDetail(sandbox) {
    const row = sandbox || null;
    msFocusedId = row && row.id ? String(row.id) : "";
    if (msDetailTitle) {
      msDetailTitle.textContent = msFocusedId || "Sandbox";
    }
    if (msId) msId.value = msFocusedId;
    if (msLabel) msLabel.value = row && row.label ? String(row.label) : "";
    if (msUrl) msUrl.value = row && row.url ? String(row.url) : "";
    resetMsRemoveConfirm();
    if (msScanBody) {
      Array.prototype.forEach.call(
        msScanBody.querySelectorAll(".ms-scan-row"),
        function (tr) {
          const id = tr.getAttribute("data-ms-id") || "";
          tr.classList.toggle("is-focus", !!msFocusedId && id === msFocusedId);
        }
      );
    }
  }

  function renderSandboxList(sandboxes) {
    if (!msScanBody) return;
    const rows = Array.isArray(sandboxes) ? sandboxes : [];
    msSandboxCache = rows.slice();
    msScanBody.textContent = "";
    if (!rows.length) {
      const empty = document.createElement("tr");
      empty.className = "ms-scan-empty";
      empty.setAttribute("data-scan-quiet-empty", "1");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.textContent = "Sandboxes: (none configured)";
      empty.appendChild(td);
      msScanBody.appendChild(empty);
      if (msFocusedId) {
        focusSandboxDetail(null);
      }
      return;
    }
    rows.forEach(function (s) {
      const tr = document.createElement("tr");
      tr.className = "ms-scan-row";
      tr.setAttribute("data-ms-scan-row", "1");
      tr.setAttribute("data-ms-id", s.id || "");
      tr.tabIndex = 0;
      const cells = [
        s.id || "—",
        s.label || s.id || "—",
        s.url || "—",
        null,
      ];
      cells.forEach(function (text, idx) {
        const td = document.createElement("td");
        if (idx === 3) {
          const pill = document.createElement("span");
          pill.className = msReadyPillClass(s.status);
          pill.textContent = msReadyLabel(s.status);
          td.appendChild(pill);
        } else {
          td.textContent = text;
        }
        tr.appendChild(td);
      });
      tr.addEventListener("click", function () {
        focusSandboxDetail(s);
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          rows: function () {
            return Array.prototype.slice.call(
              msScanBody.querySelectorAll(".ms-scan-row")
            );
          },
          activate: function (row) {
            const sid = row.getAttribute("data-ms-id") || "";
            const match = msSandboxCache.find(function (x) {
              return String(x.id || "") === sid;
            });
            if (match) focusSandboxDetail(match);
            else focusSandboxDetail(s);
          },
        });
      });
      msScanBody.appendChild(tr);
    });
    const keep =
      msFocusedId &&
      rows.find(function (s) {
        return String(s.id || "") === msFocusedId;
      });
    if (keep) {
      focusSandboxDetail(keep);
    } else if (rows.length) {
      focusSandboxDetail(rows[0]);
    } else {
      focusSandboxDetail(null);
    }
  }

  function applyMultiSandboxPlugin(payload) {
    if (!payload) return;
    if (msEnabled) {
      msEnabled.checked = !!payload.plugin_multi_sandbox_enabled;
    }
    if (payload.sandboxes) {
      renderSandboxList(payload.sandboxes);
    }
  }

  async function runMultiSandboxAction(action, extra) {
    const body = Object.assign(
      {
        action: action || "list",
        sandbox_id: msId && msId.value ? msId.value.trim() : "",
        label: msLabel && msLabel.value ? msLabel.value.trim() : "",
        url: msUrl && msUrl.value ? msUrl.value.trim() : "",
      },
      extra || {}
    );
    const res = await fetch("/api/multi-sandbox/orchestrate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error("request failed");
    }
    renderSandboxList(payload.sandboxes || []);
    return payload;
  }

  async function loadPluginRegistry() {
    try {
      const res = await fetch("/api/plugins");
      if (!res.ok) return;
      const payload = await res.json();
      const plugins = payload.plugins || [];
      const ms = plugins.find(function (p) {
        return p.id === "multi_sandbox";
      });
      if (msPlugins) {
        const parts = plugins.map(function (p) {
          return p.id + ":" + (p.enabled ? "on" : "off");
        });
        msPlugins.textContent =
          "Plugins: " + (parts.length ? parts.join(", ") : "—");
      }
      if (ms && msEnabled) {
        msEnabled.checked = !!ms.enabled;
      }
    } catch (err) {
      if (msPlugins) msPlugins.textContent = "Plugins: (could not load)";
    }
  }

  async function loadMultiSandboxPlugin() {
    try {
      const res = await fetch("/api/multi-sandbox-plugin");
      if (!res.ok) return;
      applyMultiSandboxPlugin(await res.json());
      await loadPluginRegistry();
      try {
        const listed = await runMultiSandboxAction("list");
        if (listed && listed.status === "disabled") {
          renderSandboxList([]);
        }
      } catch (err) {
        /* list optional when plugin off */
      }
      if (msStatus) msStatus.textContent = "Ready";
    } catch (err) {
      if (msStatus) msStatus.textContent = "Could not load multi-sandbox plugin.";
    }
  }

  const AREA_LAYOUT_KEY = "desktop-area-layout-v1";
  const HUD_KEY = "desktop-hud-widgets-v1";
  const CHECKLIST_DISMISS_KEY = "desktop-home-checklist-dismissed-v1";
  const AREA_LAYOUTS = ["overlay", "stage", "orb_hub", "split", "floating"];
  const AREA_LABELS = {
    settings: "Settings",
    security: "Security",
    reports: "Reports",
    documents: "Documents",
    heal: "Heal review",
    desktop: "Desktop",
    suites: "Suites",
    plans: "Plans",
    manual: "Manual",
    sandboxes: "Sandboxes",
  };
  const areaMap = {
    settings: { section: settingsSection, nav: settingsNav },
    security: { section: securitySection, nav: securityNav },
    reports: { section: reportsSection, nav: reportsNav },
    documents: { section: documentsSection, nav: documentsNav },
    heal: { section: healSection, nav: healNav },
    desktop: { section: desktopSection, nav: desktopNav },
    suites: { section: suitesSection, nav: suitesNav },
    plans: { section: plansSection, nav: plansNav },
    manual: { section: manualSection, nav: manualNav },
    sandboxes: { section: sandboxesSection, nav: sandboxesNav },
  };
  const areaLayer = document.getElementById("area-layer");
  const areaSurface = document.getElementById("area-surface");
  const areaTitle = document.getElementById("area-title");
  const areaBody = document.getElementById("area-body");
  const areaBack = document.getElementById("area-back");
  const areaScrim = document.getElementById("area-scrim");
  const orbHub = document.getElementById("orb-hub");
  const orbHubHit = document.getElementById("orb-hub-hit");
  const sectionHost = document.getElementById("area-section-host");
  const hudSecurityToggle = document.getElementById("hud-security-toggle");
  const hudReportsToggle = document.getElementById("hud-reports-toggle");
  const hudLabToggle = document.getElementById("hud-lab-toggle");
  const hudTesterConnToggle = document.getElementById("hud-tester-conn-toggle");
  const hudTesterLastToggle = document.getElementById("hud-tester-last-toggle");
  const hudTesterFailsToggle = document.getElementById("hud-tester-fails-toggle");
  const hudTesterQuarantineToggle = document.getElementById(
    "hud-tester-quarantine-toggle"
  );
  const hudMgrPassToggle = document.getElementById("hud-mgr-pass-toggle");
  const hudMgrKnownToggle = document.getElementById("hud-mgr-known-toggle");
  const hudMgrGapsToggle = document.getElementById("hud-mgr-gaps-toggle");
  const hudMgrBugsToggle = document.getElementById("hud-mgr-bugs-toggle");
  const hudRelEnvToggle = document.getElementById("hud-rel-env-toggle");
  const hudRelLastToggle = document.getElementById("hud-rel-last-toggle");
  const hudRelUncoveredToggle = document.getElementById("hud-rel-uncovered-toggle");
  const hudRelBugsToggle = document.getElementById("hud-rel-bugs-toggle");
  const hudCovStoryToggle = document.getElementById("hud-cov-story-toggle");
  const hudCovCoveredToggle = document.getElementById("hud-cov-covered-toggle");
  const hudCovPartialToggle = document.getElementById("hud-cov-partial-toggle");
  const hudCovMissingToggle = document.getElementById("hud-cov-missing-toggle");
  const hudExportLastToggle = document.getElementById("hud-export-last-toggle");
  const hudChecklistToggle = document.getElementById("hud-checklist-toggle");
  const hudSecurityPanel = document.getElementById("hud-security");
  const hudReportsPanel = document.getElementById("hud-reports");
  const hudLabPanel = document.getElementById("hud-lab");
  const hudChecklistPanel = document.getElementById("hud-checklist");
  const hudChecklistMessage = document.getElementById("hud-checklist-message");
  const hudChecklistSteps = document.getElementById("hud-checklist-steps");
  const hudChecklistConn = document.getElementById("hud-checklist-conn");
  const hudChecklistPlans = document.getElementById("hud-checklist-plans");
  const hudTesterConnPanel = document.getElementById("hud-tester-conn");
  const hudTesterLastPanel = document.getElementById("hud-tester-last");
  const hudTesterFailsPanel = document.getElementById("hud-tester-fails");
  const hudTesterQuarantinePanel = document.getElementById("hud-tester-quarantine");
  const hudMgrPassPanel = document.getElementById("hud-mgr-pass");
  const hudMgrKnownPanel = document.getElementById("hud-mgr-known");
  const hudMgrGapsPanel = document.getElementById("hud-mgr-gaps");
  const hudMgrBugsPanel = document.getElementById("hud-mgr-bugs");
  const hudRelEnvPanel = document.getElementById("hud-rel-env");
  const hudRelLastPanel = document.getElementById("hud-rel-last");
  const hudRelUncoveredPanel = document.getElementById("hud-rel-uncovered");
  const hudRelBugsPanel = document.getElementById("hud-rel-bugs");
  const hudCovStoryPanel = document.getElementById("hud-cov-story");
  const hudCovCoveredPanel = document.getElementById("hud-cov-covered");
  const hudCovPartialPanel = document.getElementById("hud-cov-partial");
  const hudCovMissingPanel = document.getElementById("hud-cov-missing");
  const hudExportLastPanel = document.getElementById("hud-export-last");
  const hudExportLastBody = document.getElementById("hud-export-last-body");
  const hudExportLastOpen = document.getElementById("hud-export-last-open");
  const hudSecurityLevel = document.getElementById("hud-security-level");
  const hudReportsBody = document.getElementById("hud-reports-body");
  const hudLabMessage = document.getElementById("hud-lab-message");
  const hudLabStatus = document.getElementById("hud-lab-status");
  const hudLabConn = document.getElementById("hud-lab-conn");
  const hudLabDraft = document.getElementById("hud-lab-draft");
  const hudLabStarter = document.getElementById("hud-lab-starter");
  const hudLabIssue = document.getElementById("hud-lab-issue");
  const hudTesterConnBody = document.getElementById("hud-tester-conn-body");
  const hudTesterConnList = document.getElementById("hud-tester-conn-list");
  const hudTesterLastBody = document.getElementById("hud-tester-last-body");
  const hudTesterLastOpen = document.getElementById("hud-tester-last-open");
  const hudTesterFailsEmpty = document.getElementById("hud-tester-fails-empty");
  const hudTesterFailsList = document.getElementById("hud-tester-fails-list");
  const hudTesterQuarantineEmpty = document.getElementById(
    "hud-tester-quarantine-empty"
  );
  const hudTesterQuarantineList = document.getElementById(
    "hud-tester-quarantine-list"
  );
  const hudMgrPassBody = document.getElementById("hud-mgr-pass-body");
  const hudMgrPassOpen = document.getElementById("hud-mgr-pass-open");
  const hudMgrKnownEmpty = document.getElementById("hud-mgr-known-empty");
  const hudMgrKnownList = document.getElementById("hud-mgr-known-list");
  const hudMgrGapsEmpty = document.getElementById("hud-mgr-gaps-empty");
  const hudMgrGapsList = document.getElementById("hud-mgr-gaps-list");
  const hudMgrBugsEmpty = document.getElementById("hud-mgr-bugs-empty");
  const hudMgrBugsList = document.getElementById("hud-mgr-bugs-list");
  const hudRelEnvBody = document.getElementById("hud-rel-env-body");
  const hudRelEnvOpen = document.getElementById("hud-rel-env-open");
  const hudRelLastBody = document.getElementById("hud-rel-last-body");
  const hudRelLastOpen = document.getElementById("hud-rel-last-open");
  const hudRelUncoveredEmpty = document.getElementById("hud-rel-uncovered-empty");
  const hudRelUncoveredList = document.getElementById("hud-rel-uncovered-list");
  const hudRelBugsEmpty = document.getElementById("hud-rel-bugs-empty");
  const hudRelBugsList = document.getElementById("hud-rel-bugs-list");
  const hudCovStoryBody = document.getElementById("hud-cov-story-body");
  const hudCovStoryOpen = document.getElementById("hud-cov-story-open");
  const hudCovCoveredEmpty = document.getElementById("hud-cov-covered-empty");
  const hudCovCoveredList = document.getElementById("hud-cov-covered-list");
  const hudCovPartialEmpty = document.getElementById("hud-cov-partial-empty");
  const hudCovPartialList = document.getElementById("hud-cov-partial-list");
  const hudCovMissingEmpty = document.getElementById("hud-cov-missing-empty");
  const hudCovMissingList = document.getElementById("hud-cov-missing-list");
  let areaLayout = "overlay";
  let openAreaName = "";
  let hudFlags = {
    security: false,
    reports: false,
    lab: false,
    testerConn: false,
    testerLast: false,
    testerFails: false,
    testerQuarantine: false,
    mgrPass: false,
    mgrKnown: false,
    mgrGaps: false,
    mgrBugs: false,
    relEnv: false,
    relLast: false,
    relUncovered: false,
    relBugs: false,
    covStory: false,
    covCovered: false,
    covPartial: false,
    covMissing: false,
    exportLast: false,
    checklist: false,
  };
  let labHomeEmpty = false;
  let checklistAllDone = false;
  let hubCloseTimer = 0;
  let testerHudLastPlanId = "";
  let testerHudCache = null;
  let managerHudPlanId = "";
  let managerHudCache = null;
  let releaseHudCache = null;
  let coverageHudCache = null;
  let coverageHudPlanId = "";

  if (areaBody && sectionHost) {
    areaBody.appendChild(sectionHost);
  }

  function normalizeAreaLayout(value) {
    const key = String(value || "").trim().toLowerCase();
    return AREA_LAYOUTS.indexOf(key) >= 0 ? key : "overlay";
  }

  function chromeFor(mode, areaOpen) {
    if (!areaOpen) return "home";
    if (mode === "orb_hub") return "overlay";
    return mode;
  }

  function loadAreaLayout() {
    try {
      return normalizeAreaLayout(localStorage.getItem(AREA_LAYOUT_KEY));
    } catch (err) {
      return "overlay";
    }
  }

  function syncLayoutRadios() {
    document.querySelectorAll('input[name="area-layout"]').forEach(function (input) {
      input.checked = input.value === areaLayout;
    });
  }

  function isHubOpen() {
    return !!(orbHub && orbHub.classList.contains("is-open") && !orbHub.hidden);
  }

  function setHubOpen(open) {
    if (!orbHub) return;
    if (hubCloseTimer) {
      window.clearTimeout(hubCloseTimer);
      hubCloseTimer = 0;
    }
    if (open) {
      orbHub.classList.remove("is-closing");
      orbHub.hidden = false;
      if (orbHubHit) {
        orbHubHit.setAttribute("aria-expanded", "true");
        orbHubHit.setAttribute("aria-label", "Close area hub");
      }
      window.requestAnimationFrame(function () {
        orbHub.classList.add("is-open");
      });
      return;
    }
    const wasOpen = orbHub.classList.contains("is-open") && !orbHub.hidden;
    orbHub.classList.remove("is-open");
    if (orbHubHit) {
      orbHubHit.setAttribute("aria-expanded", "false");
      orbHubHit.setAttribute("aria-label", "Open area hub");
    }
    if (!wasOpen) {
      orbHub.classList.remove("is-closing");
      orbHub.hidden = true;
      return;
    }
    orbHub.classList.add("is-closing");
    hubCloseTimer = window.setTimeout(function () {
      hubCloseTimer = 0;
      orbHub.classList.remove("is-closing");
      if (!orbHub.classList.contains("is-open")) orbHub.hidden = true;
    }, 240);
  }

  function syncHubAffordance() {
    const hubMode = areaLayout === "orb_hub" && !openAreaName;
    if (orbHubHit) orbHubHit.hidden = !hubMode;
    if (!hubMode) setHubOpen(false);
  }

  function clearSurfaceBox() {
    if (!areaSurface) return;
    areaSurface.style.left = "";
    areaSurface.style.top = "";
    areaSurface.style.width = "";
    areaSurface.style.height = "";
    areaSurface.style.right = "";
    areaSurface.style.bottom = "";
  }

  function syncFloatingChrome() {
    if (!areaSurface) return;
    const floating = document.documentElement.getAttribute("data-area-chrome") === "floating";
    if (floating) {
      areaSurface.dataset.widget = "area-surface";
      areaSurface.classList.add("movable-widget");
      if (!areaSurface.dataset.dragBound) {
        areaSurface.dataset.dragBound = "1";
        bindWidgetDrag(areaSurface);
        bindWidgetResize(areaSurface);
      }
      const saved = layout.widgets && layout.widgets["area-surface"];
      if (saved && typeof saved.left === "number" && typeof saved.top === "number") {
        placeWidget(
          areaSurface,
          saved.left,
          saved.top,
          typeof saved.width === "number" ? saved.width : null,
          typeof saved.height === "number" ? saved.height : null
        );
      }
    } else {
      areaSurface.classList.remove("movable-widget", "dragging", "resizing");
      clearSurfaceBox();
    }
  }

  function applyAreaLayout(mode) {
    areaLayout = normalizeAreaLayout(mode);
    try {
      localStorage.setItem(AREA_LAYOUT_KEY, areaLayout);
    } catch (err) {
      console.warn("area layout save failed", err);
    }
    const root = document.documentElement;
    root.setAttribute("data-area-layout", areaLayout);
    root.setAttribute("data-area-chrome", chromeFor(areaLayout, !!openAreaName));
    if (openAreaName) root.setAttribute("data-area-open", "true");
    else root.removeAttribute("data-area-open");
    syncLayoutRadios();
    syncHubAffordance();
    syncFloatingChrome();
  }

  function loadAreaData(name) {
    if (name === "settings") {
      loadAppSettings();
      loadReportSections();
    }
    if (name === "reports") {
      loadReportSections();
      loadReportLibrary();
      loadExportableRuns();
    }
    if (name === "security") {
      loadSecurityStatus();
      loadPrivacyStatus();
      loadLocalAudit();
      loadRedactionStatus();
      loadBackupStatus();
    }
    if (name === "documents") loadDocUploads();
    if (name === "heal") {
      loadExportableRuns().then(function () {
        loadHealProposals();
      });
    }
    if (name === "desktop") loadDesktopPlugin();
    if (name === "suites") loadPlaywrightSuite();
    if (name === "plans") {
      showPlanPanel("cases");
      closePlanAddCaseMenu();
      loadPlanList(openPlanId);
      refreshOfflineReadBanner();
      loadPlanRunSandboxes();
    }
    if (name === "manual") {
      if (!manualOpenSessionId) {
        if (manualAssist) manualAssist.checked = false;
        if (manualMist) manualMist.checked = false;
      }
      refreshManualSessions();
      if (manualStatus && !(manualStatus.textContent || "").trim()) {
        manualStatus.textContent = "Ready — no session running";
      }
    }
    if (name === "sandboxes") loadMultiSandboxPlugin();
  }

  function clearManualLinkedContext() {
    if (manualPlanId) manualPlanId.value = "";
    if (manualCaseId) manualCaseId.value = "";
    if (manualStoryKey) manualStoryKey.value = "";
    if (manualTestKey) manualTestKey.value = "";
    if (manualTicketBound) manualTicketBound.checked = false;
    if (manualStatus) {
      manualStatus.textContent = "Linked context cleared — charter-only explore ready";
    }
  }

  function fillManualFromPlanContext(planId, caseId, storyKey) {
    if (manualPlanId) manualPlanId.value = planId || "";
    if (manualCaseId) manualCaseId.value = caseId || "";
    if (manualStoryKey) manualStoryKey.value = storyKey || "";
    if (manualAssist) manualAssist.checked = false;
    if (manualMist) manualMist.checked = false;
    if (manualTicketBound) manualTicketBound.checked = !!storyKey;
    const parts = [];
    if (planId) parts.push("plan " + planId);
    if (caseId) parts.push("case " + caseId);
    if (storyKey) parts.push("story " + storyKey);
    if (manualStatus) {
      manualStatus.textContent = parts.length
        ? "Prefill from Plans — " + parts.join(" · ") + " — ready to Start"
        : "Manual ready — pick a Plans case for prefill, or charter-only";
    }
  }

  function openManualFromPlansDeepLink() {
    const planId = openPlanId || "";
    const caseId =
      planCaseId && planCaseId.value ? planCaseId.value.trim() : "";
    let storyKey = "";
    const idx = selectedCaseIndex();
    if (idx >= 0 && openPlanCases[idx]) {
      storyKey = (openPlanCases[idx].jira_key || "").trim();
    }
    if (!planId && !caseId) {
      if (planStatus) {
        planStatus.textContent =
          "Select a plan case first, then Start manual on this case.";
      }
      return;
    }
    ensureAreaOpen("manual");
    fillManualFromPlanContext(planId, caseId, storyKey);
  }

  function applyCharterFrameRect() {
    if (!charterFrameRect) return;
    const f = charterFrameState;
    charterFrameRect.style.left = f.x * 100 + "%";
    charterFrameRect.style.top = f.y * 100 + "%";
    charterFrameRect.style.width = f.w * 100 + "%";
    charterFrameRect.style.height = f.h * 100 + "%";
  }

  function setCharterMistVisible(on) {
    if (!charterFrameMist) return;
    charterFrameMist.hidden = !on;
  }

  function setManualLoopStage(stage) {
    const section = manualSection;
    const next = stage || "idle";
    if (section) section.setAttribute("data-loop-stage", next);
    if (manualLoopStageLabel) {
      if (next === "recording") {
        manualLoopStageLabel.textContent =
          "Loop: recording — notes / stills / End / Cancel on Charter Frame dock";
      } else if (next === "review") {
        manualLoopStageLabel.textContent =
          "Loop: review — Propose, then Confirm or Cancel proposal (no silent Jira)";
      } else {
        manualLoopStageLabel.textContent =
          "Loop: idle — enter a charter to Start";
      }
    }
  }

  function showCharterCancelConfirm(show) {
    const on = !!show;
    if (charterCancelConfirm) charterCancelConfirm.hidden = !on;
    if (charterDockControls) charterDockControls.hidden = on;
  }

  function updateCharterPageContext(sessionOrCtx) {
    if (!charterPageContext) return;
    const ctx =
      (sessionOrCtx && sessionOrCtx.page_context) ||
      sessionOrCtx ||
      {};
    const known = !!(ctx && ctx.known);
    charterPageContext.hidden = false;
    charterPageContext.setAttribute("data-known", known ? "1" : "0");
    if (!known) {
      charterPageContext.textContent = "AUT page: none known (notes/stills still work)";
      return;
    }
    const title = (ctx.title || "").trim();
    const url = (ctx.url || "").trim();
    const label = title || url || "known";
    charterPageContext.textContent =
      "AUT: " +
      label.slice(0, 72) +
      (url && title ? " · " + url.slice(0, 48) : "");
  }

  function updateCharterFrameChip(session) {
    if (!charterFrameChip) return;
    const noteCount = ((session && session.notes) || []).length;
    const stillCount = ((session && session.stills) || []).length;
    const mode = (session && session.frame_mode) || "free";
    const snap =
      charterSnapLabel ||
      (session && session.snap_label) ||
      "";
    let prefix = "Recording";
    if (mode === "monitor" || mode === "window") {
      prefix = "Snap · " + (snap || mode);
    }
    charterFrameChip.textContent =
      prefix +
      " · " +
      (((session && session.charter) || "").slice(0, 36) ||
        (session && session.id) ||
        "session") +
      " · " +
      noteCount +
      " notes · " +
      stillCount +
      " stills";
    updateCharterPageContext(session);
    const stills = (session && session.stills) || [];
    if (stills.length) {
      manualLastStillId = stills[stills.length - 1].id || manualLastStillId;
    }
  }

  function hideCharterSnapPicker() {
    charterSnapModePending = "";
    if (charterSnapPicker) charterSnapPicker.hidden = true;
    if (charterSnapPickerList) charterSnapPickerList.innerHTML = "";
  }

  function desktopBridgeApi() {
    return (window.pywebview && window.pywebview.api) || null;
  }

  function withTimeout(promise, ms) {
    return Promise.race([
      promise,
      new Promise(function (resolve) {
        setTimeout(function () {
          resolve({ status: "timeout" });
        }, ms);
      }),
    ]);
  }

  async function openOsCharterFloat(session) {
    const bridge = desktopBridgeApi();
    if (!bridge || !bridge.charter_float_available || !bridge.charter_float_open) {
      return false;
    }
    try {
      const avail = await withTimeout(bridge.charter_float_available(), 800);
      if (!avail || avail.status === "timeout" || !avail.available) return false;
      /* Keep Start responsive: if float bridge stalls, fall back to in-app frame. */
      const opened = await withTimeout(
        bridge.charter_float_open(session || {}),
        1500
      );
      return !!(opened && opened.status === "ok");
    } catch (_err) {
      return false;
    }
  }

  async function closeOsCharterFloat() {
    const bridge = desktopBridgeApi();
    if (!bridge || !bridge.charter_float_close) return;
    try {
      await bridge.charter_float_close();
    } catch (_err) {
      /* ignore */
    }
  }

  async function showCharterFrame(session) {
    if (!session) return;
    manualOpenSessionId = session.id || "";
    charterFrameState = Object.assign(
      { x: 0.18, y: 0.16, w: 0.64, h: 0.58 },
      session.frame || {}
    );
    charterSnapLabel = session.snap_label || "";
    showCharterCancelConfirm(false);
    hideCharterSnapPicker();
    updateCharterFrameChip(session);
    setManualLoopStage("recording");

    /* Arm in-app first so Start never looks dead if OS float stalls. */
    if (charterFrameRoot) {
      applyCharterFrameRect();
      setCharterMistVisible(!!session.armed_mist);
      if (charterAssistLive) charterAssistLive.checked = !!session.agent_assist;
      if (charterMistLive) charterMistLive.checked = !!session.armed_mist;
      charterFrameRoot.hidden = false;
      charterFrameRoot.setAttribute("aria-hidden", "false");
    }

    /* Prefer OS ring+dock. When it arms, hide in-app chrome so one movable UI remains. */
    const floated = await openOsCharterFloat(session);
    charterOsFloatActive = floated;
    if (floated) {
      if (charterFrameRoot) {
        charterFrameRoot.hidden = true;
        charterFrameRoot.setAttribute("aria-hidden", "true");
      }
      setCharterMistVisible(false);
      if (manualStatus) {
        manualStatus.textContent =
          "Recording — drag Charter Frame header to move ring+dock; ←↑↓→ nudge; ± resize capture; End on dock";
      }
      return;
    }
    if (manualStatus) {
      manualStatus.textContent =
        "Session started — drag Charter Frame label to move; edges resize (no Jira write)";
    }
  }

  async function hideCharterFrame() {
    if (charterOsFloatActive) {
      await closeOsCharterFloat();
      charterOsFloatActive = false;
    }
    if (!charterFrameRoot) return;
    showCharterCancelConfirm(false);
    hideCharterSnapPicker();
    charterFrameRoot.hidden = true;
    charterFrameRoot.setAttribute("aria-hidden", "true");
    setCharterMistVisible(false);
    charterSnapLabel = "";
  }

  window.__charterFloatEvent = async function (payload) {
    const ev = (payload && payload.type) || "";
    const sid = (payload && payload.session_id) || manualOpenSessionId;
    if (ev === "ended") {
      charterOsFloatActive = false;
      const endedId = sid || manualOpenSessionId;
      manualOpenSessionId = "";
      window.__manualLastEndedId = endedId;
      ensureAreaOpen("manual");
      try {
        const res = await fetch(
          "/api/manual-sessions/" + encodeURIComponent(endedId) + "/review"
        );
        const data = await res.json();
        if (data.status === "ok") {
          showManualReview(data.session, data.review);
          if (manualStatus) {
            manualStatus.textContent =
              "Session ended — review then Propose (Confirm uses FR-JIRA-5; Cancel writes nothing)";
          }
        } else if (manualStatus) {
          manualStatus.textContent = "Session ended — open library row to review";
          setManualLoopStage("review");
        }
      } catch (_err) {
        setManualLoopStage("review");
      }
      await refreshManualSessions();
      return;
    }
    if (ev === "cancelled") {
      charterOsFloatActive = false;
      manualOpenSessionId = "";
      ensureAreaOpen("manual");
      setManualLoopStage("idle");
      if (manualReview) manualReview.hidden = true;
      if (manualStatus) {
        manualStatus.textContent = "Session cancelled — no Jira write";
      }
      await refreshManualSessions();
      return;
    }
    if ((ev === "still" || ev === "note") && sid) {
      try {
        const res = await fetch(
          "/api/manual-sessions/" + encodeURIComponent(sid)
        );
        const data = await res.json();
        if (data && data.session) updateCharterFrameChip(data.session);
      } catch (_err) {
        /* ignore */
      }
    }
  };

  function scheduleFrameSave() {
    if (!manualOpenSessionId) return;
    if (charterFrameSaveTimer) clearTimeout(charterFrameSaveTimer);
    charterFrameSaveTimer = setTimeout(async function () {
      try {
        // Manual drag/resize → free-region (clears absolute snap bbox).
        charterSnapLabel = "";
        const res = await fetch(
          "/api/manual-sessions/" + encodeURIComponent(manualOpenSessionId) + "/frame",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(
              Object.assign({}, charterFrameState, { frame_mode: "free" })
            ),
          }
        );
        const data = await res.json();
        if (data && data.session) updateCharterFrameChip(data.session);
      } catch (_err) {
        /* ignore transient frame save errors */
      }
    }, 250);
  }

  async function openCharterSnapPicker(mode) {
    if (!manualOpenSessionId || !charterSnapPicker || !charterSnapPickerList) return;
    charterSnapModePending = mode;
    if (charterSnapPickerTitle) {
      charterSnapPickerTitle.textContent =
        mode === "window" ? "Snap to window" : "Snap to monitor";
    }
    charterSnapPickerList.innerHTML = "";
    const loading = document.createElement("p");
    loading.className = "drawer-hint";
    loading.textContent = "Loading targets…";
    charterSnapPickerList.appendChild(loading);
    charterSnapPicker.hidden = false;
    try {
      const res = await fetch("/api/manual-sessions/snap-targets");
      const data = await res.json();
      charterSnapPickerList.innerHTML = "";
      const items =
        mode === "window" ? data.windows || [] : data.monitors || [];
      if (!items.length) {
        const empty = document.createElement("p");
        empty.className = "drawer-hint";
        empty.textContent =
          mode === "window"
            ? "No visible windows found."
            : "No monitors found.";
        charterSnapPickerList.appendChild(empty);
        return;
      }
      items.forEach(function (item) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "charter-snap-option";
        btn.setAttribute("role", "option");
        btn.dataset.targetId = item.id || "";
        btn.textContent =
          mode === "window"
            ? item.title || item.id || "Window"
            : item.label || item.id || "Monitor";
        charterSnapPickerList.appendChild(btn);
      });
    } catch (_err) {
      charterSnapPickerList.innerHTML = "";
      const err = document.createElement("p");
      err.className = "drawer-hint";
      err.textContent = "Could not load snap targets.";
      charterSnapPickerList.appendChild(err);
    }
  }

  async function applyCharterSnap(targetId) {
    if (!manualOpenSessionId || !charterSnapModePending || !targetId) return;
    try {
      const res = await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(manualOpenSessionId) +
          "/snap",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mode: charterSnapModePending,
            target_id: targetId,
          }),
        }
      );
      const data = await res.json();
      if (data.status === "ok" && data.session) {
        charterFrameState = Object.assign(
          { x: 0.18, y: 0.16, w: 0.64, h: 0.58 },
          data.session.frame || {}
        );
        charterSnapLabel = data.session.snap_label || "";
        applyCharterFrameRect();
        // Mist/assist toggles unchanged by snap.
        if (charterAssistLive) {
          charterAssistLive.checked = !!data.session.agent_assist;
        }
        if (charterMistLive) {
          charterMistLive.checked = !!data.session.armed_mist;
          setCharterMistVisible(!!data.session.armed_mist);
        }
        updateCharterFrameChip(data.session);
        hideCharterSnapPicker();
      } else if (charterFrameChip) {
        charterFrameChip.textContent = data.message || "Snap failed";
      }
    } catch (_err) {
      if (charterFrameChip) charterFrameChip.textContent = "Snap failed";
    }
  }

  function formatManualSessionWhen(iso) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return String(iso).slice(0, 16);
      return d.toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (_err) {
      return String(iso).slice(0, 16);
    }
  }

  function manualSessionLinkLabel(s) {
    const story = (s && s.jira_story_key) || "";
    if (story) return story;
    const caseId = (s && s.case_id) || "";
    if (caseId) return caseId;
    const planId = (s && s.plan_id) || "";
    if (planId) return planId;
    return "—";
  }

  function manualSessionStageLabel(s) {
    const status = String((s && s.status) || "").toLowerCase();
    if (status === "open") return "Recording";
    if (status === "ended") return "Review";
    if (status === "cancelled") return "Ended";
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : "—";
  }

  function setManualScanFocus(sessionId) {
    manualFocusedSessionId = sessionId || "";
    if (!manualSessionList) return;
    const rows = manualSessionList.querySelectorAll(".manual-scan-row");
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const sid = row.getAttribute("data-session-id") || "";
      if (sid && sid === manualFocusedSessionId) {
        row.classList.add("is-focus");
      } else {
        row.classList.remove("is-focus");
      }
    }
  }

  function focusManualSessionRow(session) {
    if (!session) return;
    const sid = session.id || "";
    setManualScanFocus(sid);
    if (manualDetailTitle) {
      manualDetailTitle.textContent = sid
        ? "Focused session"
        : "No session focused";
    }
    if (manualDetailCharter) {
      manualDetailCharter.value = session.charter || "";
    }
    if (manualDetailHint) {
      if (session.reviewable) {
        manualDetailHint.textContent =
          "Review for this session. Propose then Confirm — row click never writes Jira.";
      } else {
        manualDetailHint.textContent =
          "Session is not reviewable. Start session opens Charter Frame; this row does not.";
      }
    }
    const stills = session.stills || [];
    const notes = session.notes || [];
    const stage = manualSessionStageLabel(session);
    const when = formatManualSessionWhen(session.created_at || session.ended_at);
    const shotCount = Array.isArray(stills) ? stills.length : 0;
    fillEvidenceFirst(evidenceFirstRoot("manual-evidence-first"), {
      force: true,
      summary: [stage, when, notes.length ? notes.length + " note(s)" : ""]
        .filter(Boolean)
        .join(" · "),
      link: shotCount
        ? shotCount + " still(s) — open from review; not a gallery"
        : "",
      hasScreenshot: shotCount > 0,
    });
  }

  function showManualReview(session, review) {
    setManualLoopStage("review");
    if (manualReview) manualReview.hidden = false;
    if (session) focusManualSessionRow(session);
    const notes = (session && session.notes) || (review && review.notes) || [];
    const stills = (session && session.stills) || (review && review.stills) || [];
    const drafts =
      (session && session.assist_drafts) || (review && review.assist_drafts) || [];
    const assistStatus =
      (session && session.assist_status) ||
      (review && review.assist_status) ||
      "off";
    const assistMessage =
      (session && session.assist_message) ||
      (review && review.assist_message) ||
      "";
    const assistEl = document.getElementById("manual-assist-status");
    if (assistEl) {
      if (assistStatus === "unavailable") {
        assistEl.hidden = false;
        assistEl.setAttribute("data-assist-state", "unavailable");
        assistEl.textContent =
          assistMessage ||
          "Agent assist unavailable — Ollama is down. No fake AI drafts.";
      } else if (assistStatus === "ready" && drafts.length) {
        assistEl.hidden = false;
        assistEl.setAttribute("data-assist-state", "ready");
        assistEl.textContent =
          assistMessage ||
          drafts.length +
            " local unpublished Ollama draft(s) — Propose then Confirm for Jira.";
      } else if (assistStatus === "ready") {
        assistEl.hidden = false;
        assistEl.setAttribute("data-assist-state", "ready");
        assistEl.textContent =
          assistMessage || "Assist on — no drafts from this session yet.";
      } else if (assistStatus === "pending") {
        assistEl.hidden = false;
        assistEl.setAttribute("data-assist-state", "pending");
        assistEl.textContent =
          assistMessage || "Assist pending — drafts build at End.";
      } else {
        assistEl.hidden = true;
        assistEl.setAttribute("data-assist-state", "off");
        assistEl.textContent = "";
      }
    }
    if (manualReviewOut) {
      const draftLines = drafts.length
        ? drafts
            .map(function (d) {
              return (
                "* [" +
                (d.kind || "draft") +
                "] " +
                (d.title ? d.title + " — " : "") +
                (d.text || "") +
                (d.source === "ollama" ? " (ollama, unpublished)" : " (local, unpublished)")
              );
            })
            .join("\n")
        : "(no assist drafts)";
      const pageCtx = (session && session.page_context) || {};
      const pageLine = pageCtx.known
        ? "AUT page: " +
          ((pageCtx.title || "").trim() || "(no title)") +
          " · " +
          ((pageCtx.url || "").trim() || "(no url)")
        : "AUT page: none known";
      const stillLines =
        stills
          .map(function (s) {
            const ann = (s.annotation || "").trim();
            return (
              "- " +
              (s.id || "still") +
              (ann ? " · annotated: " + ann : "")
            );
          })
          .join("\n") || "(no stills)";
      manualReviewOut.textContent = [
        "Session: " + ((session && session.id) || ""),
        "Charter: " + ((session && session.charter) || ""),
        pageLine,
        "Notes: " + notes.length,
        "Stills: " + stills.length,
        "Assist: " + assistStatus + " · drafts " + drafts.length + " (local only, never silent Jira)",
        "Jira writes: never silent — Propose then Confirm (FR-JIRA-5)",
        "",
        "Notes:",
        notes
          .map(function (n) {
            return "- " + (n.text || "");
          })
          .join("\n") || "(no notes)",
        "",
        "Stills:",
        stillLines,
        "",
        "Assist drafts:",
        draftLines,
      ].join("\n");
    }
    if (manualProposeOut) {
      manualProposeOut.hidden = true;
      manualProposeOut.textContent = "";
    }
    if (manualConfirmRow) manualConfirmRow.hidden = true;
    manualPendingProposalId = "";
  }

  function clearManualUiForLevelSwitch() {
    /* Previous level's open session must not stay visible after confirm switch. */
    try {
      void hideCharterFrame();
    } catch (_err) {
      /* frame optional */
    }
    manualOpenSessionId = "";
    manualFocusedSessionId = "";
    window.__manualLastEndedId = "";
    window.__manualProposeSessionId = "";
    manualPendingProposalId = "";
    if (manualDetailCharter) manualDetailCharter.value = "";
    if (manualDetailTitle) manualDetailTitle.textContent = "Focused session";
    if (manualDetailHint) {
      manualDetailHint.textContent =
        "Row click opens review for that session. Propose stays deliberate. Confirm dock is below the work.";
    }
    hideEvidenceFirst(evidenceFirstRoot("manual-evidence-first"));
    if (manualReview) manualReview.hidden = true;
    if (manualProposeOut) {
      manualProposeOut.hidden = true;
      manualProposeOut.textContent = "";
    }
    if (manualConfirmRow) manualConfirmRow.hidden = true;
    setManualLoopStage("idle");
    if (manualStatus) {
      manualStatus.textContent =
        "Security level switched — Manual library shows this level only";
    }
  }

  async function reopenManualFromLibrary(sessionId) {
    if (!sessionId) return;
    try {
      const res = await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/reopen",
        { method: "POST" }
      );
      const data = await res.json();
      if (data.status !== "ok") {
        if (manualStatus) {
          manualStatus.textContent =
            data.message || data.error || "Could not reopen session";
        }
        return;
      }
      window.__manualLastEndedId = sessionId;
      ensureAreaOpen("manual");
      showManualReview(data.session, data.review);
      if (manualStatus) {
        manualStatus.textContent =
          data.message ||
          "Reopened local draft — Propose then Confirm (no silent Jira)";
      }
    } catch (err) {
      if (manualStatus) {
        manualStatus.textContent = "Reopen failed: " + (err.message || err);
      }
    }
  }

  async function refreshManualSessions() {
    try {
      const res = await fetch("/api/manual-sessions");
      const data = await res.json();
      if (manualLibraryLevel) {
        manualLibraryLevel.textContent =
          "Active level: " + (data.level || "—") + " (isolated)";
      }
      if (manualSessionList) {
        const rows = data.sessions || [];
        if (manualSessionEmpty) {
          manualSessionEmpty.hidden = rows.length > 0;
        }
        if (!rows.length) {
          manualSessionList.innerHTML = "";
        } else {
          manualSessionList.innerHTML = rows
            .slice(0, 20)
            .map(function (s) {
              const sid = String(s.id || "").replace(/"/g, "");
              const charter = String(s.charter || "(no charter)")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
              const link = String(manualSessionLinkLabel(s))
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
              const stage = String(manualSessionStageLabel(s))
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
              const when = String(formatManualSessionWhen(s.created_at))
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
              const focusClass =
                sid && sid === manualFocusedSessionId ? " is-focus" : "";
              return (
                '<tr class="manual-scan-row' +
                focusClass +
                '" tabindex="0" data-session-id="' +
                sid +
                '" data-session-status="' +
                String(s.status || "").replace(/"/g, "") +
                '" data-reviewable="' +
                (s.reviewable ? "1" : "0") +
                '" data-manual-session-row="1" role="row">' +
                "<td>" +
                when +
                "</td>" +
                "<td>" +
                charter +
                "</td>" +
                "<td>" +
                link +
                "</td>" +
                "<td><span class=\"manual-pill\">" +
                stage +
                "</span></td>" +
                "</tr>"
              );
            })
            .join("");
        }
      }
      if (data.open_session_id) {
        /* Never arm Charter chrome on home/orb — only while Manual is open (KAN-507). */
        if (openAreaName === "manual") {
          if (!manualOpenSessionId) {
            const openRes = await fetch("/api/manual-sessions/open");
            const openData = await openRes.json();
            if (openData.open && openData.session) {
              await showCharterFrame(openData.session);
            }
          }
          if (manualStatus) {
            manualStatus.textContent = charterOsFloatActive
              ? "Session recording — use Charter dock (drag header to move). End before a new charter."
              : "Session recording — Charter Frame armed. End before typing a new charter.";
          }
        }
      } else {
        if (manualOpenSessionId) {
          await hideCharterFrame();
          manualOpenSessionId = "";
        }
        const stage =
          (manualSection && manualSection.getAttribute("data-loop-stage")) || "";
        if (stage === "recording") {
          setManualLoopStage("idle");
        }
      }
    } catch (_err) {
      if (manualSessionEmpty) {
        manualSessionEmpty.hidden = false;
        manualSessionEmpty.textContent = "Could not load sessions.";
      }
      if (manualSessionList) {
        manualSessionList.innerHTML = "";
      }
    }
  }

  async function startManualSession() {
    const charter = manualCharter ? manualCharter.value.trim() : "";
    if (!charter) {
      if (manualStatus) manualStatus.textContent = "Charter is required to Start.";
      return;
    }
    const ticketBound = !!(manualTicketBound && manualTicketBound.checked);
    const story = manualStoryKey ? manualStoryKey.value.trim() : "";
    if (ticketBound && !story) {
      if (manualStatus) {
        manualStatus.textContent =
          "Story key is required when Link to Jira is checked.";
      }
      return;
    }
    if (manualStatus) manualStatus.textContent = "Starting Charter Frame…";
    try {
      const res = await fetch("/api/manual-sessions/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          charter: charter,
          plan_id: manualPlanId ? manualPlanId.value.trim() : "",
          case_id: manualCaseId ? manualCaseId.value.trim() : "",
          jira_story_key: story,
          jira_test_key: manualTestKey ? manualTestKey.value.trim() : "",
          ticket_bound: ticketBound,
          agent_assist: !!(manualAssist && manualAssist.checked),
          armed_mist: !!(manualMist && manualMist.checked),
        }),
      });
      const data = await res.json();
      if (data.status !== "ok") {
        if (manualStatus) {
          const errCode = data.error || "";
          if (errCode === "session_already_open") {
            manualStatus.textContent =
              "A session is already recording — End or Cancel it before starting another.";
            await refreshManualSessions();
          } else {
            manualStatus.textContent =
              data.message || data.error || "Start failed";
          }
        }
        return;
      }
      if (manualReview) manualReview.hidden = true;
      /* Keep Manual open so Start is visible; do not closeArea (looked like a no-op glitch). */
      await showCharterFrame(data.session);
      await refreshManualSessions();
    } catch (err) {
      if (manualStatus) {
        manualStatus.textContent = "Start failed: " + (err.message || err);
      }
    }
  }

  async function endManualSessionFromFrame() {
    if (!manualOpenSessionId) return;
    showCharterCancelConfirm(false);
    try {
      const res = await fetch(
        "/api/manual-sessions/" + encodeURIComponent(manualOpenSessionId) + "/end",
        { method: "POST" }
      );
      const data = await res.json();
      await hideCharterFrame();
      const sid = manualOpenSessionId;
      manualOpenSessionId = "";
      window.__manualLastEndedId = sid;
      ensureAreaOpen("manual");
      if (data.status === "ok") {
        showManualReview(data.session, data.review);
        if (manualStatus) {
          manualStatus.textContent =
            "Session ended — review then Propose (Confirm uses FR-JIRA-5; Cancel writes nothing)";
        }
      } else if (manualStatus) {
        manualStatus.textContent = data.message || "End failed";
        setManualLoopStage("idle");
      }
      await refreshManualSessions();
      return sid;
    } catch (err) {
      if (manualStatus) {
        manualStatus.textContent = "End failed: " + (err.message || err);
      }
    }
  }

  function requestCancelManualSession() {
    if (!manualOpenSessionId) return;
    showCharterCancelConfirm(true);
  }

  async function cancelManualSessionFromFrame() {
    if (!manualOpenSessionId) return;
    try {
      const res = await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(manualOpenSessionId) +
          "/cancel",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ confirm: true }),
        }
      );
      const data = await res.json();
      await hideCharterFrame();
      manualOpenSessionId = "";
      ensureAreaOpen("manual");
      setManualLoopStage("idle");
      if (manualReview) manualReview.hidden = true;
      if (manualStatus) {
        manualStatus.textContent =
          data.message || "Session cancelled — no Jira write";
      }
      await refreshManualSessions();
    } catch (err) {
      showCharterCancelConfirm(false);
      if (manualStatus) {
        manualStatus.textContent = "Cancel failed: " + (err.message || err);
      }
    }
  }

  function manualFailureClassValue() {
    return (manualFailureClass && manualFailureClass.value) || "product_bug";
  }

  function manualExplicitBugValue() {
    return !!(manualExplicitBug && manualExplicitBug.checked);
  }

  function formatManualProposalPreview(data) {
    const prop = (data && data.proposal) || data || {};
    if (prop.packet) {
      const p = prop.packet;
      const steps = (p.replication_steps || [])
        .map(function (s, i) {
          return String(i + 1) + ". " + s;
        })
        .join("\n");
      return [
        "Kind: create_bug",
        "Failure class: " + (p.selected_failure_class || p.failure_class || ""),
        p.explicit_bug_pick ? "Explicit Bug pick: yes" : "",
        "Symptom: " + (p.symptom || ""),
        "Expected: " + (p.expected || ""),
        "Actual: " + (p.actual || ""),
        "Environment: " + (p.environment || ""),
        "Replication:",
        steps,
        p.evidence_paths && p.evidence_paths.length
          ? "Evidence: " + p.evidence_paths.join(", ")
          : "",
        prop.message || "",
      ]
        .filter(Boolean)
        .join("\n");
    }
    return JSON.stringify(prop, null, 2);
  }

  async function proposeManual(kind) {
    let sessionId =
      window.__manualLastEndedId ||
      manualOpenSessionId ||
      "";
    if (!sessionId) {
      try {
        const listRes = await fetch("/api/manual-sessions");
        const listData = await listRes.json();
        const ended = (listData.sessions || []).find(function (s) {
          return s.status === "ended";
        });
        sessionId = ended ? ended.id : "";
      } catch (_err) {
        sessionId = "";
      }
    }
    if (!sessionId) {
      if (manualProposeOut) {
        manualProposeOut.hidden = false;
        manualProposeOut.textContent = "No ended session to propose from.";
      }
      return;
    }
    try {
      const res = await fetch(
        "/api/manual-sessions/" + encodeURIComponent(sessionId) + "/propose",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            kind: kind,
            failure_class: manualFailureClassValue(),
            explicit_bug: manualExplicitBugValue(),
          }),
        }
      );
      const data = await res.json();
      if (manualProposeOut) {
        manualProposeOut.hidden = false;
        manualProposeOut.textContent =
          data.status === "ok"
            ? formatManualProposalPreview(data)
            : JSON.stringify(data, null, 2);
      }
      if (data.status === "ok" && data.proposal) {
        manualPendingProposalId = data.proposal.id || "";
        window.__manualProposeSessionId = sessionId;
        if (manualConfirmRow) {
          manualConfirmRow.hidden = false;
        }
        if (manualStatus) {
          manualStatus.textContent =
            data.proposal.message ||
            "Preview ready — Confirm (audited write) or Cancel proposal (writes nothing)";
        }
      } else {
        if (manualConfirmRow) manualConfirmRow.hidden = true;
        manualPendingProposalId = "";
        if (manualStatus) {
          manualStatus.textContent = data.message || data.error || "Propose failed";
        }
      }
    } catch (err) {
      if (manualProposeOut) {
        manualProposeOut.hidden = false;
        manualProposeOut.textContent = String(err.message || err);
      }
    }
  }

  async function confirmManualProposal(doConfirm) {
    const sessionId = window.__manualProposeSessionId || "";
    if (!sessionId || !manualPendingProposalId) return;
    try {
      const res = await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(sessionId) +
          "/proposals/" +
          encodeURIComponent(manualPendingProposalId) +
          "/confirm",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ confirm: !!doConfirm }),
        }
      );
      const data = await res.json();
      if (manualProposeOut) {
        manualProposeOut.hidden = false;
        manualProposeOut.textContent = JSON.stringify(data, null, 2);
      }
      if (manualStatus) {
        if (!doConfirm) {
          manualStatus.textContent =
            data.message || "Proposal cancelled — nothing written to Jira";
        } else if (data.status === "ok" && data.writes_jira) {
          manualStatus.textContent =
            data.message || "Confirmed — Jira write completed (audited)";
        } else if (data.status === "ok") {
          manualStatus.textContent =
            data.message || "Confirmed — local only (no Jira write)";
        } else {
          manualStatus.textContent =
            data.message || data.error || "Confirm failed — nothing audited as success";
        }
      }
      if (data.status === "ok" || !doConfirm) {
        if (manualConfirmRow) manualConfirmRow.hidden = true;
        manualPendingProposalId = "";
      }
    } catch (err) {
      if (manualStatus) {
        manualStatus.textContent = "Confirm failed: " + (err.message || err);
      }
    }
  }

  async function addCharterNoteFromDock() {
    if (!manualOpenSessionId || !charterNoteInput) return;
    const text = charterNoteInput.value.trim();
    if (!text) return;
    try {
      const res = await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(manualOpenSessionId) +
          "/notes",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text }),
        }
      );
      const data = await res.json();
      if (data.status === "ok") {
        charterNoteInput.value = "";
        if (charterFrameChip) {
          charterFrameChip.textContent =
            "Note saved · " +
            (data.session.notes || []).length +
            " notes · " +
            (data.session.stills || []).length +
            " stills";
        }
      } else if (charterFrameChip) {
        charterFrameChip.textContent = data.message || "Note failed";
      }
    } catch (_err) {
      if (charterFrameChip) charterFrameChip.textContent = "Note failed";
    }
  }

  function onCharterPointerDown(ev) {
    if (!charterFrameRoot || charterFrameRoot.hidden) return;
    const handle = ev.target && ev.target.getAttribute
      ? ev.target.getAttribute("data-resize")
      : null;
    const isDrag = ev.target === charterFrameDrag;
    if (!handle && !isDrag) return;
    charterDragMode = handle || "move";
    charterDragOrigin = {
      x: ev.clientX,
      y: ev.clientY,
      frame: Object.assign({}, charterFrameState),
    };
    ev.preventDefault();
  }

  function onCharterPointerMove(ev) {
    if (!charterDragMode || !charterDragOrigin) return;
    const dx = (ev.clientX - charterDragOrigin.x) / window.innerWidth;
    const dy = (ev.clientY - charterDragOrigin.y) / window.innerHeight;
    const o = charterDragOrigin.frame;
    let next = Object.assign({}, o);
    if (charterDragMode === "move") {
      next.x = Math.min(1 - o.w, Math.max(0, o.x + dx));
      next.y = Math.min(1 - o.h, Math.max(0, o.y + dy));
    } else {
      if (charterDragMode.indexOf("e") >= 0) {
        next.w = Math.min(1 - o.x, Math.max(0.12, o.w + dx));
      }
      if (charterDragMode.indexOf("s") >= 0) {
        next.h = Math.min(1 - o.y, Math.max(0.12, o.h + dy));
      }
      if (charterDragMode.indexOf("w") >= 0) {
        const nx = Math.min(o.x + o.w - 0.12, Math.max(0, o.x + dx));
        next.w = o.w + (o.x - nx);
        next.x = nx;
      }
      if (charterDragMode.indexOf("n") >= 0) {
        const ny = Math.min(o.y + o.h - 0.12, Math.max(0, o.y + dy));
        next.h = o.h + (o.y - ny);
        next.y = ny;
      }
    }
    charterFrameState = next;
    applyCharterFrameRect();
  }

  function onCharterPointerUp() {
    if (!charterDragMode) return;
    charterDragMode = null;
    charterDragOrigin = null;
    scheduleFrameSave();
  }

  function selectedHealRunId() {
    if (!healRunFilter || !healRunFilter.value) return "";
    const parts = healRunFilter.value.split("|");
    return parts[2] || "";
  }

  function formatHealClassLabel(raw) {
    const text = String(raw || "unclassified").replace(/_/g, " ").trim();
    if (!text) return "Unclassified";
    return text.replace(/\b\w/g, function (ch) {
      return ch.toUpperCase();
    });
  }

  function healLocatorLabel(item) {
    const evidence = (item && item.evidence) || {};
    const proposed = String(evidence.proposed || "").trim();
    if (proposed) return proposed;
    const original = String(evidence.original || "").trim();
    if (original) return original;
    const proposal = String((item && (item.proposal || item.message)) || "").trim();
    if (!proposal) return "—";
    const first = proposal.split(/\r?\n/).find(function (line) {
      return line.trim();
    });
    return (first || proposal).slice(0, 80);
  }

  function healWhenLabel(raw) {
    const text = String(raw || "").trim();
    if (!text) return "—";
    // Prefer compact "22 Nov 09:14" when ISO-like.
    const m = text.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    if (!m) return text.slice(0, 19);
    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    const mon = months[Number(m[2]) - 1] || m[2];
    return Number(m[3]) + " " + mon + " " + m[4] + ":" + m[5];
  }

  function getHealCheckedIds() {
    if (!healScanBody) return [];
    const ids = [];
    healScanBody.querySelectorAll(".heal-scan-row").forEach(function (tr) {
      const cb = tr.querySelector('input[type="checkbox"]');
      if (cb && cb.checked && tr.dataset.id) ids.push(tr.dataset.id);
    });
    return ids;
  }

  function syncHealBulkToolbar() {
    const ids = getHealCheckedIds();
    const n = ids.length;
    if (healBulkWrap) healBulkWrap.hidden = n < 1;
    if (healBulkApprove) {
      healBulkApprove.disabled = n < 1;
      if (n < 1) {
        healBulkAwaitingConfirm = false;
        healBulkApprove.textContent = "Approve selected (0)";
      } else if (healBulkAwaitingConfirm) {
        healBulkApprove.textContent = "Confirm approve (" + n + ")";
      } else {
        healBulkApprove.textContent = "Approve selected (" + n + ")";
      }
    }
  }

  function setHealDetailFocused(focused) {
    const healDetail = document.getElementById("heal-detail");
    const healUnfocused = document.getElementById("heal-unfocused");
    const healActions = document.querySelector('[data-heal-actions="1"]');
    if (healDetail) healDetail.setAttribute("data-heal-focused", focused ? "1" : "0");
    if (healUnfocused) healUnfocused.hidden = !!focused;
    if (healActions) healActions.hidden = !focused;
  }

  function clearHealFocus() {
    healFocusedId = "";
    if (healScanBody) {
      healScanBody.querySelectorAll(".heal-scan-row.is-focus").forEach(function (el) {
        el.classList.remove("is-focus");
      });
    }
    if (healDetailTitle) healDetailTitle.textContent = "No proposal focused";
    if (healDetailHint) {
      healDetailHint.textContent =
        "Select a row. Sel is multi-select only. Approve and Reject act on the focused id only.";
    }
    if (healDetailId) healDetailId.value = "";
    if (healDetailDiff) healDetailDiff.textContent = "";
    hideEvidenceFirst(evidenceFirstRoot("heal-evidence-first"));
    if (healApproveBtn) healApproveBtn.disabled = true;
    if (healRejectBtn) healRejectBtn.disabled = true;
    setHealDetailFocused(false);
  }

  function focusHealDetail(tr, opts) {
    const options = opts || {};
    if (!tr || !tr.dataset) return;
    const id = tr.dataset.id || "";
    if (healScanBody) {
      healScanBody.querySelectorAll(".heal-scan-row.is-focus").forEach(function (el) {
        el.classList.remove("is-focus");
      });
    }
    tr.classList.add("is-focus");
    healFocusedId = id;
    const item = healById[id] || {};
    if (healDetailTitle) healDetailTitle.textContent = "Proposal";
    if (healDetailHint) {
      healDetailHint.textContent =
        "Approve / Reject act on this focused proposal only. Suite files are not auto-committed.";
    }
    if (healDetailId) healDetailId.value = id;
    if (healDetailDiff) {
      healDetailDiff.textContent =
        item.proposal || item.message || "(no diff)";
    }
    fillEvidenceFirst(evidenceFirstRoot("heal-evidence-first"), {
      force: true,
      summary: [
        formatHealClassLabel(item.classification),
        healWhenLabel(item.created_at || item.when || item.timestamp),
        healLocatorLabel(item),
      ]
        .filter(function (part) {
          return part && part !== "—";
        })
        .join(" · "),
      link: "",
      hasScreenshot: false,
    });
    if (healApproveBtn) healApproveBtn.disabled = !id;
    if (healRejectBtn) healRejectBtn.disabled = !id;
    setHealDetailFocused(!!id);
    if (options.focusField && healDetailId) {
      try {
        healDetailId.focus();
      } catch (err) {
        /* ignore */
      }
    }
  }

  function renderHealProposals(payload) {
    if (!healScanBody) return;
    const pending = (payload && payload.pending) || [];
    const prevFocus = healFocusedId;
    const prevChecked = {};
    getHealCheckedIds().forEach(function (id) {
      prevChecked[id] = true;
    });
    healScanBody.innerHTML = "";
    healById = {};
    healBulkAwaitingConfirm = false;
    clearHealFocus();

    if (healListEmpty) {
      healListEmpty.hidden = pending.length > 0;
      healListEmpty.textContent = selectedHealRunId()
        ? "No pending heal proposals for this run."
        : "No pending heal proposals.";
    }

    pending.forEach(function (item) {
      const id = (item && item.id) || "";
      if (!id) return;
      healById[id] = item;
      const tr = document.createElement("tr");
      tr.className = "heal-scan-row";
      tr.tabIndex = 0;
      tr.dataset.id = id;
      tr.setAttribute("role", "row");

      const tdHit = document.createElement("td");
      tdHit.className = "heal-hit";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.setAttribute("aria-label", "Select " + id);
      cb.setAttribute("data-heal-checkbox-stop", "1");
      if (prevChecked[id]) cb.checked = true;
      cb.addEventListener("click", function (ev) {
        ev.stopPropagation();
      });
      cb.addEventListener("change", function (ev) {
        ev.stopPropagation();
        healBulkAwaitingConfirm = false;
        syncHealBulkToolbar();
      });
      tdHit.appendChild(cb);

      const tdClass = document.createElement("td");
      const classPill = document.createElement("span");
      const classRaw = String((item && item.classification) || "unclassified");
      classPill.className =
        "heal-pill " +
        (classRaw === "test_defect" || classRaw === "product_bug" ? "warn" : "idle");
      classPill.textContent = formatHealClassLabel(classRaw);
      tdClass.appendChild(classPill);

      const tdLoc = document.createElement("td");
      tdLoc.className = "mono";
      tdLoc.textContent = healLocatorLabel(item);

      const tdRun = document.createElement("td");
      tdRun.className = "mono";
      tdRun.textContent = (item && item.run_id) || "—";

      const tdWhen = document.createElement("td");
      tdWhen.textContent = healWhenLabel(item && item.timestamp);

      tr.appendChild(tdHit);
      tr.appendChild(tdClass);
      tr.appendChild(tdLoc);
      tr.appendChild(tdRun);
      tr.appendChild(tdWhen);

      tr.addEventListener("click", function (ev) {
        if (
          ev.target &&
          ev.target.closest &&
          ev.target.closest('[data-heal-checkbox-stop="1"]')
        ) {
          return;
        }
        focusHealDetail(tr, { focusField: false });
      });
      tr.addEventListener("keydown", function (ev) {
        onScanRowKeydown(ev, {
          row: tr,
          checkboxStop: '[data-heal-checkbox-stop="1"]',
          rows: function () {
            return Array.prototype.slice.call(
              healScanBody.querySelectorAll(".heal-scan-row")
            );
          },
          activate: function (row) {
            focusHealDetail(row, { focusField: false });
          },
        });
      });

      healScanBody.appendChild(tr);
    });

    syncHealBulkToolbar();
    if (prevFocus && healById[prevFocus]) {
      const row = healScanBody.querySelector(
        '.heal-scan-row[data-id="' + prevFocus.replace(/"/g, "") + '"]'
      );
      if (row) focusHealDetail(row, { focusField: false });
    }
  }

  async function loadHealProposals() {
    if (healStatus) healStatus.textContent = "Loading…";
    try {
      const runId = selectedHealRunId();
      const url = runId
        ? "/api/heal/proposals?run_id=" + encodeURIComponent(runId)
        : "/api/heal/proposals";
      const res = await fetch(url);
      const data = await res.json();
      renderHealProposals(data);
      if (healStatus) {
        const n = (data && data.count) || 0;
        if (n === 0) {
          healStatus.textContent = runId
            ? "No pending heals for this run."
            : "No pending heals.";
        } else {
          healStatus.textContent = runId
            ? n + " pending heal(s) for this run."
            : n + " pending heal(s).";
        }
      }
    } catch (err) {
      if (healStatus) healStatus.textContent = "Could not load heal proposals.";
    }
  }

  async function resolveHealProposal(id, action) {
    if (!id) return false;
    try {
      const res = await fetch(action === "approve" ? "/api/heal/approve" : "/api/heal/reject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposal_id: id, reviewer: "local_user" }),
      });
      const data = await res.json();
      if (!data || !data.ok) {
        if (healStatus) {
          healStatus.textContent =
            (data && data.error) || "Could not update heal proposal.";
        }
        return false;
      }
      return true;
    } catch (err) {
      if (healStatus) healStatus.textContent = "Could not update heal proposal.";
      return false;
    }
  }

  async function approveFocusedHeal() {
    if (!healFocusedId) return;
    if (healStatus) healStatus.textContent = "Approving…";
    const ok = await resolveHealProposal(healFocusedId, "approve");
    if (!ok) return;
    await loadHealProposals();
    if (healStatus) {
      healStatus.textContent =
        "Approved — approver recorded; suite not auto-committed.";
    }
  }

  async function rejectFocusedHeal() {
    if (!healFocusedId) return;
    if (healStatus) healStatus.textContent = "Rejecting…";
    const ok = await resolveHealProposal(healFocusedId, "reject");
    if (!ok) return;
    await loadHealProposals();
    if (healStatus) {
      healStatus.textContent = "Rejected — heal not treated as accepted.";
    }
  }

  async function bulkApproveSelectedHeals() {
    const ids = getHealCheckedIds();
    if (!ids.length) {
      syncHealBulkToolbar();
      return;
    }
    if (!healBulkAwaitingConfirm) {
      healBulkAwaitingConfirm = true;
      syncHealBulkToolbar();
      if (healStatus) {
        // KAN-352: count + "files are not written"; Reject stays on focused detail only.
        healStatus.textContent =
          "Approve " +
          ids.length +
          " proposals? Files are not written. Reject is not part of this step. Click Confirm approve to proceed.";
      }
      return;
    }
    if (healStatus) healStatus.textContent = "Approving selected…";
    let okCount = 0;
    for (let i = 0; i < ids.length; i += 1) {
      const ok = await resolveHealProposal(ids[i], "approve");
      if (ok) okCount += 1;
    }
    healBulkAwaitingConfirm = false;
    await loadHealProposals();
    if (healStatus) {
      healStatus.textContent =
        "Approved " +
        okCount +
        " of " +
        ids.length +
        " selected — suite not auto-committed.";
    }
  }

  function closeArea() {
    openAreaName = "";
    Object.keys(areaMap).forEach(function (key) {
      const entry = areaMap[key];
      if (entry.section) entry.section.hidden = true;
      if (entry.nav) entry.nav.setAttribute("aria-pressed", "false");
    });
    if (areaLayer) areaLayer.hidden = true;
    if (appDrawerHint) appDrawerHint.hidden = false;
    applyAreaLayout(areaLayout);
    applyHud(hudFlags);
  }

  function openArea(name) {
    if (!areaMap[name]) return;
    if (openAreaName === name) {
      closeArea();
      return;
    }
    openAreaName = name;
    Object.keys(areaMap).forEach(function (key) {
      const entry = areaMap[key];
      const on = key === name;
      if (entry.section) entry.section.hidden = !on;
      if (entry.nav) entry.nav.setAttribute("aria-pressed", on ? "true" : "false");
    });
    if (areaTitle) areaTitle.textContent = AREA_LABELS[name] || name;
    if (areaLayer) areaLayer.hidden = false;
    setHubOpen(false);
    if (appDrawerHint) appDrawerHint.hidden = true;
    if (appDrawer && appDrawer.classList.contains("open")) {
      setDrawer(appDrawer, appToggle, false);
    }
    applyAreaLayout(areaLayout);
    applyHud(hudFlags);
    if (name === "settings") {
      setSettingsCategory(settingsCategoryPending || "app");
      settingsCategoryPending = null;
    }
    loadAreaData(name);
  }

  /* Keep Manual (etc.) open when already showing — openArea toggles closed. */
  function ensureAreaOpen(name) {
    if (!areaMap[name]) return;
    if (openAreaName === name) return;
    openArea(name);
  }

  document.querySelectorAll(".app-nav-item[data-section], .hub-spoke[data-section]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const section = btn.getAttribute("data-section");
      /* Chat = home (close area). Lab tools + Primary areas open via openArea. */
      if (section === "chat") {
        closeArea();
        document.querySelectorAll(".app-nav-item[data-section]").forEach(function (nav) {
          nav.setAttribute(
            "aria-pressed",
            nav.getAttribute("data-section") === "chat" ? "true" : "false"
          );
        });
        if (appDrawer && appDrawer.classList.contains("open")) {
          setDrawer(appDrawer, appToggle, false);
        }
        return;
      }
      openArea(section);
    });
  });

  if (areaBack) {
    areaBack.addEventListener("click", closeArea);
  }
  if (areaScrim) {
    areaScrim.addEventListener("click", function () {
      const chrome = document.documentElement.getAttribute("data-area-chrome");
      if (chrome === "split") return;
      closeArea();
    });
  }
  if (orbHubHit) {
    orbHubHit.addEventListener("click", function () {
      if (areaLayout !== "orb_hub" || openAreaName) return;
      setHubOpen(!isHubOpen());
    });
  }
  document.querySelectorAll('input[name="area-layout"]').forEach(function (input) {
    input.addEventListener("change", function () {
      if (!input.checked) return;
      applyAreaLayout(input.value);
    });
  });
  /* F5 keyboard: Alt+R run selected, Alt+N next failure, Esc Back to orb.
     Explicitly no shortcuts for Jira write confirm or heal approve. */
  const KEYBOARD_SHORTCUTS = {
    run_selected: "Alt+R",
    next_failure: "Alt+N",
    back_to_orb: "Escape",
    never: ["jira_write_confirm", "heal_approve"],
  };

  function backToOrbFromKeyboard() {
    const hubOpen = isHubOpen();
    const appOpen = !!(appDrawer && appDrawer.classList.contains("open"));
    const screenOpen = !!(screenDrawer && screenDrawer.classList.contains("open"));
    if (!hubOpen && !openAreaName && !appOpen && !screenOpen) return false;
    if (hubOpen) {
      setHubOpen(false);
      return true;
    }
    if (openAreaName) {
      closeArea();
      return true;
    }
    if (appOpen) {
      setDrawer(appDrawer, appToggle, false);
      return true;
    }
    if (screenOpen) {
      setDrawer(screenDrawer, screenToggle, false);
      return true;
    }
    return false;
  }

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") {
      const hubOpen = isHubOpen();
      const appOpen = !!(appDrawer && appDrawer.classList.contains("open"));
      const screenOpen = !!(screenDrawer && screenDrawer.classList.contains("open"));
      if (!hubOpen && !openAreaName && !appOpen && !screenOpen) return;
      if (ev.target && (ev.target.tagName === "INPUT" || ev.target.tagName === "TEXTAREA" || ev.target.tagName === "SELECT")) {
        /* KAN-348: Esc from detail fields returns to scan first (never side-effect confirms). */
        if (focusScanFromDetail(ev.target)) {
          ev.preventDefault();
          ev.target.blur();
          return;
        }
        ev.target.blur();
      } else if (focusScanFromDetail(ev.target)) {
        ev.preventDefault();
        return;
      }
      if (backToOrbFromKeyboard()) {
        ev.preventDefault();
      }
      return;
    }

    if (!ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    const key = String(ev.key || "").toLowerCase();
    if (key === "r") {
      ev.preventDefault();
      runSelectedCaseFromKeyboard();
      return;
    }
    if (key === "n") {
      ev.preventDefault();
      selectNextFailureFromKeyboard();
    }
  });

  function updateHudSecurity(level) {
    if (!hudSecurityLevel) return;
    const text = String(level || "").trim().toUpperCase();
    hudSecurityLevel.textContent = text || "—";
  }

  function formatHudReports(summary) {
    if (!summary || !summary.available) return "No recent run";
    const bits = [];
    if (typeof summary.pass_rate_percent === "number") {
      bits.push("pass " + Math.round(summary.pass_rate_percent) + "%");
    }
    if (typeof summary.stories_covered === "number") {
      bits.push(
        summary.stories_covered +
          (summary.stories_covered === 1 ? " story" : " stories")
      );
    }
    if (typeof summary.tests_passed === "number") {
      bits.push(
        summary.tests_passed +
          (summary.tests_passed === 1 ? " test" : " tests")
      );
    }
    if (!bits.length) return "No recent run";
    return "Last run: " + bits.join(", ");
  }

  function applyHudReports(summary) {
    if (hudReportsBody) hudReportsBody.textContent = formatHudReports(summary);
  }

  async function loadHudReports() {
    try {
      const res = await fetch("/api/reports/latest-summary");
      if (!res.ok) {
        applyHudReports({ available: false });
        return;
      }
      applyHudReports(await res.json());
    } catch (err) {
      applyHudReports({ available: false });
    }
  }

  function applyHud(flags) {
    hudFlags = {
      security: !!(flags && flags.security),
      reports: !!(flags && flags.reports),
      lab: !!(flags && flags.lab),
      testerConn: !!(flags && flags.testerConn),
      testerLast: !!(flags && flags.testerLast),
      testerFails: !!(flags && flags.testerFails),
      testerQuarantine: !!(flags && flags.testerQuarantine),
      mgrPass: !!(flags && flags.mgrPass),
      mgrKnown: !!(flags && flags.mgrKnown),
      mgrGaps: !!(flags && flags.mgrGaps),
      mgrBugs: !!(flags && flags.mgrBugs),
      relEnv: !!(flags && flags.relEnv),
      relLast: !!(flags && flags.relLast),
      relUncovered: !!(flags && flags.relUncovered),
      relBugs: !!(flags && flags.relBugs),
      covStory: !!(flags && flags.covStory),
      covCovered: !!(flags && flags.covCovered),
      covPartial: !!(flags && flags.covPartial),
      covMissing: !!(flags && flags.covMissing),
      exportLast: !!(flags && flags.exportLast),
      checklist: !!(flags && flags.checklist),
    };
    if (hudSecurityToggle) hudSecurityToggle.checked = hudFlags.security;
    if (hudReportsToggle) hudReportsToggle.checked = hudFlags.reports;
    if (hudLabToggle) hudLabToggle.checked = hudFlags.lab;
    if (hudChecklistToggle) hudChecklistToggle.checked = hudFlags.checklist;
    if (hudTesterConnToggle) hudTesterConnToggle.checked = hudFlags.testerConn;
    if (hudTesterLastToggle) hudTesterLastToggle.checked = hudFlags.testerLast;
    if (hudTesterFailsToggle) hudTesterFailsToggle.checked = hudFlags.testerFails;
    if (hudTesterQuarantineToggle) {
      hudTesterQuarantineToggle.checked = hudFlags.testerQuarantine;
    }
    if (hudMgrPassToggle) hudMgrPassToggle.checked = hudFlags.mgrPass;
    if (hudMgrKnownToggle) hudMgrKnownToggle.checked = hudFlags.mgrKnown;
    if (hudMgrGapsToggle) hudMgrGapsToggle.checked = hudFlags.mgrGaps;
    if (hudMgrBugsToggle) hudMgrBugsToggle.checked = hudFlags.mgrBugs;
    if (hudRelEnvToggle) hudRelEnvToggle.checked = hudFlags.relEnv;
    if (hudRelLastToggle) hudRelLastToggle.checked = hudFlags.relLast;
    if (hudRelUncoveredToggle) {
      hudRelUncoveredToggle.checked = hudFlags.relUncovered;
    }
    if (hudRelBugsToggle) hudRelBugsToggle.checked = hudFlags.relBugs;
    if (hudCovStoryToggle) hudCovStoryToggle.checked = hudFlags.covStory;
    if (hudCovCoveredToggle) hudCovCoveredToggle.checked = hudFlags.covCovered;
    if (hudCovPartialToggle) hudCovPartialToggle.checked = hudFlags.covPartial;
    if (hudCovMissingToggle) hudCovMissingToggle.checked = hudFlags.covMissing;
    if (hudExportLastToggle) hudExportLastToggle.checked = hudFlags.exportLast;
    const home = !openAreaName;
    if (hudSecurityPanel) hudSecurityPanel.hidden = !(home && hudFlags.security);
    if (hudReportsPanel) hudReportsPanel.hidden = !(home && hudFlags.reports);
    // Empty lab auto-shows checklist on home; toggle keeps it available when plans exist.
    if (hudLabPanel) {
      hudLabPanel.hidden = !(home && (labHomeEmpty || hudFlags.lab));
    }
    // First-hour checklist: Screen toggle is authoritative (KAN-323).
    // Auto-show seeds the toggle while incomplete unless the user dismissed it;
    // all-done auto-hides; reopen from Screen drawer.
    if (hudChecklistPanel) {
      hudChecklistPanel.hidden = !(home && hudFlags.checklist);
    }
    // Tester pack is home-only (hidden while any App area is open).
    if (hudTesterConnPanel) {
      hudTesterConnPanel.hidden = !(home && hudFlags.testerConn);
    }
    if (hudTesterLastPanel) {
      hudTesterLastPanel.hidden = !(home && hudFlags.testerLast);
    }
    if (hudTesterFailsPanel) {
      hudTesterFailsPanel.hidden = !(home && hudFlags.testerFails);
    }
    if (hudTesterQuarantinePanel) {
      hudTesterQuarantinePanel.hidden = !(home && hudFlags.testerQuarantine);
    }
    // Manager pack is home-only (no separate Manager home).
    if (hudMgrPassPanel) {
      hudMgrPassPanel.hidden = !(home && hudFlags.mgrPass);
    }
    if (hudMgrKnownPanel) {
      hudMgrKnownPanel.hidden = !(home && hudFlags.mgrKnown);
    }
    if (hudMgrGapsPanel) {
      hudMgrGapsPanel.hidden = !(home && hudFlags.mgrGaps);
    }
    if (hudMgrBugsPanel) {
      hudMgrBugsPanel.hidden = !(home && hudFlags.mgrBugs);
    }
    // Release pack is home-only (no separate Release home; readiness in Reports).
    if (hudRelEnvPanel) {
      hudRelEnvPanel.hidden = !(home && hudFlags.relEnv);
    }
    if (hudRelLastPanel) {
      hudRelLastPanel.hidden = !(home && hudFlags.relLast);
    }
    if (hudRelUncoveredPanel) {
      hudRelUncoveredPanel.hidden = !(home && hudFlags.relUncovered);
    }
    if (hudRelBugsPanel) {
      hudRelBugsPanel.hidden = !(home && hudFlags.relBugs);
    }
    // Coverage pack is home-only (no separate PO home; never edits Jira).
    if (hudCovStoryPanel) {
      hudCovStoryPanel.hidden = !(home && hudFlags.covStory);
    }
    if (hudCovCoveredPanel) {
      hudCovCoveredPanel.hidden = !(home && hudFlags.covCovered);
    }
    if (hudCovPartialPanel) {
      hudCovPartialPanel.hidden = !(home && hudFlags.covPartial);
    }
    if (hudCovMissingPanel) {
      hudCovMissingPanel.hidden = !(home && hudFlags.covMissing);
    }
    if (hudExportLastPanel) {
      hudExportLastPanel.hidden = !(home && hudFlags.exportLast);
    }
  }

  function defaultHudFlags() {
    return {
      security: false,
      reports: false,
      lab: false,
      testerConn: false,
      testerLast: false,
      testerFails: false,
      testerQuarantine: false,
      mgrPass: false,
      mgrKnown: false,
      mgrGaps: false,
      mgrBugs: false,
      relEnv: false,
      relLast: false,
      relUncovered: false,
      relBugs: false,
      covStory: false,
      covCovered: false,
      covPartial: false,
      covMissing: false,
      exportLast: false,
      checklist: false,
    };
  }

  function loadHud() {
    try {
      const raw = localStorage.getItem(HUD_KEY);
      applyHud(raw ? JSON.parse(raw) : defaultHudFlags());
    } catch (err) {
      applyHud(defaultHudFlags());
    }
  }

  function isHomeChecklistDismissed() {
    try {
      return localStorage.getItem(CHECKLIST_DISMISS_KEY) === "1";
    } catch (err) {
      return false;
    }
  }

  function setHomeChecklistDismissed(dismissed) {
    try {
      if (dismissed) localStorage.setItem(CHECKLIST_DISMISS_KEY, "1");
      else localStorage.removeItem(CHECKLIST_DISMISS_KEY);
    } catch (err) {
      console.warn("checklist dismiss save failed", err);
    }
  }

  function persistHudFlags(flags) {
    try {
      localStorage.setItem(HUD_KEY, JSON.stringify(flags));
    } catch (err) {
      console.warn("hud save failed", err);
    }
  }

  function saveHud() {
    const flags = {
      security: !!(hudSecurityToggle && hudSecurityToggle.checked),
      reports: !!(hudReportsToggle && hudReportsToggle.checked),
      lab: !!(hudLabToggle && hudLabToggle.checked),
      testerConn: !!(hudTesterConnToggle && hudTesterConnToggle.checked),
      testerLast: !!(hudTesterLastToggle && hudTesterLastToggle.checked),
      testerFails: !!(hudTesterFailsToggle && hudTesterFailsToggle.checked),
      testerQuarantine: !!(
        hudTesterQuarantineToggle && hudTesterQuarantineToggle.checked
      ),
      mgrPass: !!(hudMgrPassToggle && hudMgrPassToggle.checked),
      mgrKnown: !!(hudMgrKnownToggle && hudMgrKnownToggle.checked),
      mgrGaps: !!(hudMgrGapsToggle && hudMgrGapsToggle.checked),
      mgrBugs: !!(hudMgrBugsToggle && hudMgrBugsToggle.checked),
      relEnv: !!(hudRelEnvToggle && hudRelEnvToggle.checked),
      relLast: !!(hudRelLastToggle && hudRelLastToggle.checked),
      relUncovered: !!(
        hudRelUncoveredToggle && hudRelUncoveredToggle.checked
      ),
      relBugs: !!(hudRelBugsToggle && hudRelBugsToggle.checked),
      covStory: !!(hudCovStoryToggle && hudCovStoryToggle.checked),
      covCovered: !!(hudCovCoveredToggle && hudCovCoveredToggle.checked),
      covPartial: !!(hudCovPartialToggle && hudCovPartialToggle.checked),
      covMissing: !!(hudCovMissingToggle && hudCovMissingToggle.checked),
      exportLast: !!(hudExportLastToggle && hudExportLastToggle.checked),
      checklist: !!(hudChecklistToggle && hudChecklistToggle.checked),
    };
    // Uncheck = dismiss (survives reload while incomplete); check = reopen.
    setHomeChecklistDismissed(!flags.checklist);
    applyHud(flags);
    persistHudFlags(flags);
    if (
      flags.testerConn ||
      flags.testerLast ||
      flags.testerFails ||
      flags.testerQuarantine
    ) {
      loadTesterHud();
    }
    if (flags.mgrPass || flags.mgrKnown || flags.mgrGaps || flags.mgrBugs) {
      loadManagerHud();
    }
    if (
      flags.relEnv ||
      flags.relLast ||
      flags.relUncovered ||
      flags.relBugs
    ) {
      loadReleaseHud();
    }
    if (
      flags.covStory ||
      flags.covCovered ||
      flags.covPartial ||
      flags.covMissing
    ) {
      loadCoverageHud();
    }
    if (flags.exportLast) {
      loadExportPackHud();
    }
    loadHomeChecklistHud();
  }

  async function refreshLabHome() {
    try {
      const res = await fetch("/api/plans/home");
      const payload = await res.json();
      labHomeEmpty = !!(payload && payload.empty);
      if (hudLabMessage) {
        hudLabMessage.textContent =
          (payload && payload.message) ||
          (labHomeEmpty
            ? "No plan yet — pick a next step."
            : "Plans ready for this level.");
      }
      applyHud(hudFlags);
      loadHomeChecklistHud();
    } catch (err) {
      labHomeEmpty = false;
      if (hudLabStatus) hudLabStatus.textContent = "Could not load lab home status.";
      applyHud(hudFlags);
    }
  }

  function clearHudRowList(el) {
    if (!el) return;
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function appendHudRow(listEl, label, title, onClick) {
    if (!listEl) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "hud-row-btn";
    btn.textContent = label;
    if (title) btn.title = title;
    btn.addEventListener("click", onClick);
    listEl.appendChild(btn);
  }

  async function openPlansOnCase(planId, caseId, caseName) {
    if (!planId) return;
    if (openAreaName !== "plans") {
      openArea("plans");
    }
    await loadPlanList(planId);
    await openPlan(planId);
    if (caseId && planCaseId) {
      planCaseId.value = caseId;
      if (planCaseName && caseName) planCaseName.value = caseName;
      await refreshCaseDetail();
      if (planCaseId.focus) planCaseId.focus();
      if (planStatus) {
        planStatus.textContent =
          "HUD → case " + caseId + " in " + planId;
      }
    } else if (planStatus) {
      planStatus.textContent = "HUD → plan " + planId;
    }
  }

  function renderTesterHud(payload) {
    testerHudCache = payload || null;
    const conn = (payload && payload.connection) || {};
    if (hudTesterConnBody) {
      hudTesterConnBody.textContent =
        conn.message ||
        ("Health: " + (conn.overall || "unknown"));
    }
    clearHudRowList(hudTesterConnList);
    (conn.checks || []).forEach(function (c) {
      const state = c.up ? "up" : c.state || "down";
      appendHudRow(
        hudTesterConnList,
        (c.label || c.id || "?") + ": " + state,
        c.message || "",
        function () {
          openArea("settings");
        }
      );
    });

    const last = payload && payload.last_run;
    testerHudLastPlanId = last && last.plan_id ? last.plan_id : "";
    if (hudTesterLastBody) {
      if (!last) {
        hudTesterLastBody.textContent = "No suite run yet";
      } else {
        const bits = [];
        if (typeof last.pass === "number") bits.push(last.pass + " pass");
        if (typeof last.fail === "number") bits.push(last.fail + " fail");
        if (typeof last.error === "number" && last.error) {
          bits.push(last.error + " error");
        }
        hudTesterLastBody.textContent =
          (last.plan_name || last.plan_id || "Plan") +
          (bits.length ? " — " + bits.join(", ") : "");
      }
    }
    if (hudTesterLastOpen) {
      hudTesterLastOpen.hidden = !testerHudLastPlanId;
    }

    const fails = (payload && payload.failed_cases) || [];
    clearHudRowList(hudTesterFailsList);
    if (hudTesterFailsEmpty) {
      hudTesterFailsEmpty.hidden = fails.length > 0;
      hudTesterFailsEmpty.textContent = fails.length
        ? ""
        : "No fails on last run";
    }
    fails.forEach(function (row) {
      appendHudRow(
        hudTesterFailsList,
        (row.case_name || row.case_id || "?") +
          (row.result ? " · " + row.result : ""),
        (row.plan_name || row.plan_id || "") +
          (row.failure_class ? " · " + row.failure_class : ""),
        function () {
          openPlansOnCase(row.plan_id, row.case_id, row.case_name);
        }
      );
    });

    const quarantine = (payload && payload.quarantined_cases) || [];
    clearHudRowList(hudTesterQuarantineList);
    if (hudTesterQuarantineEmpty) {
      hudTesterQuarantineEmpty.hidden = quarantine.length > 0;
      hudTesterQuarantineEmpty.textContent = quarantine.length
        ? ""
        : "Nothing quarantined";
    }
    quarantine.forEach(function (row) {
      appendHudRow(
        hudTesterQuarantineList,
        row.case_name || row.case_id || "?",
        (row.reason || "quarantined") +
          (row.expires_at ? " · until " + row.expires_at : ""),
        function () {
          openPlansOnCase(row.plan_id, row.case_id, row.case_name);
        }
      );
    });
  }

  async function loadTesterHud() {
    try {
      const res = await fetch("/api/plans/tester-hud");
      if (!res.ok) {
        renderTesterHud(null);
        return;
      }
      renderTesterHud(await res.json());
    } catch (err) {
      renderTesterHud(null);
    }
  }

  function renderManagerHud(payload) {
    managerHudCache = payload || null;
    const rate = (payload && payload.pass_rate) || {};
    managerHudPlanId = rate.plan_id || "";
    if (hudMgrPassBody) {
      if (rate.pass_rate_percent == null && !rate.case_count) {
        hudMgrPassBody.textContent = "No suite run yet";
      } else {
        const pct =
          rate.pass_rate_percent != null
            ? rate.pass_rate_percent + "%"
            : "n/a";
        const bits = [pct + " pass"];
        if (typeof rate.known_issues === "number" && rate.known_issues) {
          bits.push(rate.known_issues + " known (not pass)");
        }
        hudMgrPassBody.textContent =
          (rate.plan_name || rate.plan_id || "Plan") + " — " + bits.join(", ");
      }
    }
    if (hudMgrPassOpen) {
      hudMgrPassOpen.hidden = !managerHudPlanId;
    }

    const known = (payload && payload.known_issues) || [];
    clearHudRowList(hudMgrKnownList);
    if (hudMgrKnownEmpty) {
      hudMgrKnownEmpty.hidden = known.length > 0;
      hudMgrKnownEmpty.textContent = known.length
        ? ""
        : "None labelled known";
    }
    known.forEach(function (row) {
      appendHudRow(
        hudMgrKnownList,
        (row.case_name || row.case_id || "?") +
          " · known" +
          (row.result && row.result !== "pass" ? " · " + row.result : ""),
        (row.note || row.jira_key || "known issue") +
          " (not counted as pass)",
        function () {
          openPlansOnCase(row.plan_id, row.case_id, row.case_name);
        }
      );
    });

    const gaps = (payload && payload.stories_no_case) || [];
    clearHudRowList(hudMgrGapsList);
    if (hudMgrGapsEmpty) {
      hudMgrGapsEmpty.hidden = gaps.length > 0;
      hudMgrGapsEmpty.textContent = gaps.length ? "" : "No coverage gaps";
    }
    gaps.forEach(function (row) {
      appendHudRow(
        hudMgrGapsList,
        row.story_key || "?",
        row.summary || "story with no case",
        function () {
          openPlansOnCase(row.plan_id, "", "");
        }
      );
    });

    const bugs = (payload && payload.bugs) || [];
    clearHudRowList(hudMgrBugsList);
    if (hudMgrBugsEmpty) {
      hudMgrBugsEmpty.hidden = bugs.length > 0;
      hudMgrBugsEmpty.textContent = bugs.length ? "" : "No product bugs";
    }
    bugs.forEach(function (row) {
      appendHudRow(
        hudMgrBugsList,
        (row.case_name || row.case_id || "?") +
          (row.jira_key ? " · " + row.jira_key : ""),
        (row.plan_name || row.plan_id || "") + " · product_bug",
        function () {
          openPlansOnCase(row.plan_id, row.case_id, row.case_name);
        }
      );
    });
  }

  async function loadManagerHud() {
    try {
      const res = await fetch("/api/plans/manager-hud");
      if (!res.ok) {
        renderManagerHud(null);
        return;
      }
      renderManagerHud(await res.json());
    } catch (err) {
      renderManagerHud(null);
    }
  }

  function openReleaseReadiness() {
    // AC: readiness ticks stay on Reports — not a separate Release home.
    openArea("reports");
  }

  function renderReleaseHud(payload) {
    releaseHudCache = payload || null;
    const env = (payload && payload.environment) || {};
    if (hudRelEnvBody) {
      if (!env.name) {
        hudRelEnvBody.textContent = "No named environment";
      } else {
        const bits = [env.name];
        if (env.target_url_set) bits.push("URL set");
        if (env.target_app_path_set) bits.push("exe set");
        hudRelEnvBody.textContent = bits.join(" · ");
      }
    }
    if (hudRelEnvOpen) {
      hudRelEnvOpen.hidden = false;
    }

    const last = (payload && payload.last_run) || {};
    if (hudRelLastBody) {
      if (!last.plan_id && !last.case_count) {
        hudRelLastBody.textContent = "No suite run yet";
      } else {
        const bits = [];
        if (last.pass_rate_percent != null) {
          bits.push(last.pass_rate_percent + "% pass");
        }
        if (typeof last.pass === "number") bits.push(last.pass + " pass");
        if (typeof last.fail === "number") bits.push(last.fail + " fail");
        if (typeof last.error === "number" && last.error) {
          bits.push(last.error + " error");
        }
        if (last.environment_name) bits.push("env " + last.environment_name);
        hudRelLastBody.textContent =
          (last.plan_name || last.plan_id || "Plan") +
          (bits.length ? " — " + bits.join(", ") : "");
      }
    }
    if (hudRelLastOpen) {
      hudRelLastOpen.hidden = !(last && last.plan_id);
    }

    const uncovered = (payload && payload.uncovered_stories) || [];
    clearHudRowList(hudRelUncoveredList);
    if (hudRelUncoveredEmpty) {
      hudRelUncoveredEmpty.hidden = uncovered.length > 0;
      hudRelUncoveredEmpty.textContent = uncovered.length
        ? ""
        : "No uncovered stories";
    }
    uncovered.forEach(function (row) {
      appendHudRow(
        hudRelUncoveredList,
        row.story_key || "?",
        (row.summary || "uncovered") + " → Reports readiness",
        openReleaseReadiness
      );
    });

    const bugs = (payload && payload.open_product_bugs) || [];
    clearHudRowList(hudRelBugsList);
    if (hudRelBugsEmpty) {
      hudRelBugsEmpty.hidden = bugs.length > 0;
      hudRelBugsEmpty.textContent = bugs.length
        ? ""
        : "No open product bugs";
    }
    bugs.forEach(function (row) {
      appendHudRow(
        hudRelBugsList,
        (row.case_name || row.case_id || "?") +
          (row.jira_key ? " · " + row.jira_key : ""),
        (row.plan_name || row.plan_id || "") + " · product_bug → Reports",
        openReleaseReadiness
      );
    });
  }

  async function loadReleaseHud() {
    try {
      const res = await fetch("/api/plans/release-hud");
      if (!res.ok) {
        renderReleaseHud(null);
        return;
      }
      renderReleaseHud(await res.json());
    } catch (err) {
      renderReleaseHud(null);
    }
  }

  function openCoverageLine(row) {
    if (!row) return;
    openPlansOnCase(row.plan_id || "", row.case_id || "", row.case_name || "");
  }

  function renderCoverageHud(payload) {
    coverageHudCache = payload || null;
    const story = (payload && payload.open_story) || {};
    coverageHudPlanId = story.plan_id || "";
    if (hudCovStoryBody) {
      if (!story.story_key) {
        hudCovStoryBody.textContent = "No open story";
      } else {
        const bits = [
          (story.covered_count || 0) + " covered",
          (story.partial_count || 0) + " partial",
          (story.missing_count || 0) + " missing",
        ];
        hudCovStoryBody.textContent =
          story.story_key +
          (story.summary ? " — " + story.summary : "") +
          " · " +
          bits.join(", ");
      }
    }
    if (hudCovStoryOpen) {
      hudCovStoryOpen.hidden = !coverageHudPlanId;
    }

    function fillAcList(rows, emptyEl, listEl, emptyLabel) {
      clearHudRowList(listEl);
      if (emptyEl) {
        emptyEl.hidden = rows.length > 0;
        emptyEl.textContent = rows.length ? "" : emptyLabel;
      }
      rows.forEach(function (row) {
        appendHudRow(
          listEl,
          row.line || "?",
          (row.status || "") +
            (row.case_name ? " · " + row.case_name : " · no case") +
            " → Plans",
          function () {
            openCoverageLine(row);
          }
        );
      });
    }

    fillAcList(
      (payload && payload.covered) || [],
      hudCovCoveredEmpty,
      hudCovCoveredList,
      "No covered lines"
    );
    fillAcList(
      (payload && payload.partial) || [],
      hudCovPartialEmpty,
      hudCovPartialList,
      "No partial lines"
    );
    fillAcList(
      (payload && payload.missing) || [],
      hudCovMissingEmpty,
      hudCovMissingList,
      "No missing lines"
    );
  }

  async function loadCoverageHud() {
    try {
      let url = "/api/plans/coverage-hud";
      const key =
        hudLabIssue && hudLabIssue.value ? hudLabIssue.value.trim() : "";
      if (key) {
        url += "?story_key=" + encodeURIComponent(key);
      }
      const res = await fetch(url);
      if (!res.ok) {
        renderCoverageHud(null);
        return;
      }
      renderCoverageHud(await res.json());
    } catch (err) {
      renderCoverageHud(null);
    }
  }

  function renderExportPackHud(payload) {
    if (!hudExportLastBody) return;
    const available = !!(payload && payload.available);
    if (!available) {
      hudExportLastBody.textContent = "No pack yet";
      if (hudExportLastOpen) hudExportLastOpen.hidden = true;
      return;
    }
    const when = payload.last_export_time || "unknown time";
    const level = payload.security_level || "";
    const folder = payload.folder_name || payload.pack_id || "";
    hudExportLastBody.textContent =
      (level ? level + " · " : "") + when + (folder ? " · " + folder : "");
    if (hudExportLastOpen) hudExportLastOpen.hidden = false;
  }

  async function loadExportPackHud() {
    try {
      const res = await fetch("/api/export-pack/last");
      if (!res.ok) {
        renderExportPackHud(null);
        return;
      }
      renderExportPackHud(await res.json());
    } catch (err) {
      renderExportPackHud(null);
    }
  }

  function renderHomeChecklistHud(payload) {
    const wasAllDone = checklistAllDone;
    checklistAllDone = !!(payload && payload.all_done);
    if (hudChecklistMessage) {
      hudChecklistMessage.textContent =
        (payload && payload.message) ||
        "Connection · first plan · first run";
    }
    if (hudChecklistSteps) {
      hudChecklistSteps.innerHTML = "";
      const steps = (payload && payload.steps) || [];
      steps.forEach(function (step) {
        const li = document.createElement("li");
        li.setAttribute("role", "listitem");
        li.dataset.done = step.done ? "true" : "false";
        const mark = document.createElement("span");
        mark.className = "hud-checklist-mark";
        mark.textContent = step.done ? "✓" : "○";
        mark.setAttribute("aria-hidden", "true");
        const body = document.createElement("span");
        body.textContent =
          (step.label || "") +
          (step.hint ? " — " + step.hint : "");
        li.appendChild(mark);
        li.appendChild(body);
        hudChecklistSteps.appendChild(li);
      });
    }
    if (checklistAllDone) {
      // Auto-hide on transition to done; user may reopen via Screen toggle.
      if (!wasAllDone && hudFlags.checklist) {
        hudFlags.checklist = false;
        persistHudFlags(hudFlags);
      }
    } else if (!isHomeChecklistDismissed() && !hudFlags.checklist) {
      // Auto-show while incomplete unless the user dismissed it (KAN-323).
      hudFlags.checklist = true;
      persistHudFlags(hudFlags);
    }
    applyHud(hudFlags);
  }

  async function loadHomeChecklistHud() {
    try {
      const res = await fetch("/api/plans/home-checklist");
      if (!res.ok) {
        renderHomeChecklistHud(null);
        return;
      }
      const payload = await res.json();
      if (!payload || payload.status !== "ok" || !Array.isArray(payload.steps)) {
        renderHomeChecklistHud(null);
        return;
      }
      renderHomeChecklistHud(payload);
    } catch (err) {
      renderHomeChecklistHud(null);
    }
  }

  if (hudSecurityToggle) hudSecurityToggle.addEventListener("change", saveHud);
  if (hudReportsToggle) hudReportsToggle.addEventListener("change", saveHud);
  if (hudLabToggle) hudLabToggle.addEventListener("change", saveHud);
  if (hudTesterConnToggle) hudTesterConnToggle.addEventListener("change", saveHud);
  if (hudTesterLastToggle) hudTesterLastToggle.addEventListener("change", saveHud);
  if (hudTesterFailsToggle) hudTesterFailsToggle.addEventListener("change", saveHud);
  if (hudTesterQuarantineToggle) {
    hudTesterQuarantineToggle.addEventListener("change", saveHud);
  }
  if (hudMgrPassToggle) hudMgrPassToggle.addEventListener("change", saveHud);
  if (hudMgrKnownToggle) hudMgrKnownToggle.addEventListener("change", saveHud);
  if (hudMgrGapsToggle) hudMgrGapsToggle.addEventListener("change", saveHud);
  if (hudMgrBugsToggle) hudMgrBugsToggle.addEventListener("change", saveHud);
  if (hudRelEnvToggle) hudRelEnvToggle.addEventListener("change", saveHud);
  if (hudRelLastToggle) hudRelLastToggle.addEventListener("change", saveHud);
  if (hudRelUncoveredToggle) {
    hudRelUncoveredToggle.addEventListener("change", saveHud);
  }
  if (hudRelBugsToggle) hudRelBugsToggle.addEventListener("change", saveHud);
  if (hudCovStoryToggle) hudCovStoryToggle.addEventListener("change", saveHud);
  if (hudCovCoveredToggle) {
    hudCovCoveredToggle.addEventListener("change", saveHud);
  }
  if (hudCovPartialToggle) {
    hudCovPartialToggle.addEventListener("change", saveHud);
  }
  if (hudCovMissingToggle) {
    hudCovMissingToggle.addEventListener("change", saveHud);
  }
  if (hudExportLastToggle) {
    hudExportLastToggle.addEventListener("change", saveHud);
  }
  if (hudChecklistToggle) {
    hudChecklistToggle.addEventListener("change", saveHud);
  }
  if (hudChecklistConn) {
    hudChecklistConn.addEventListener("click", function () {
      openArea("settings");
    });
  }
  if (hudChecklistPlans) {
    hudChecklistPlans.addEventListener("click", function () {
      openArea("plans");
    });
  }
  if (hudTesterLastOpen) {
    hudTesterLastOpen.addEventListener("click", function () {
      if (testerHudLastPlanId) openPlansOnCase(testerHudLastPlanId, "", "");
    });
  }
  if (hudMgrPassOpen) {
    hudMgrPassOpen.addEventListener("click", function () {
      openArea("reports");
    });
  }
  if (hudExportLastOpen) {
    hudExportLastOpen.addEventListener("click", function () {
      openArea("reports");
    });
  }
  if (hudRelEnvOpen) {
    hudRelEnvOpen.addEventListener("click", openReleaseReadiness);
  }
  if (hudRelLastOpen) {
    hudRelLastOpen.addEventListener("click", openReleaseReadiness);
  }
  if (hudCovStoryOpen) {
    hudCovStoryOpen.addEventListener("click", function () {
      if (coverageHudPlanId) openPlansOnCase(coverageHudPlanId, "", "");
    });
  }
  loadHud();
  loadHudReports();
  loadSecurityStatus();
  refreshLabHome();
  loadTesterHud();
  loadManagerHud();
  loadReleaseHud();
  loadCoverageHud();
  loadExportPackHud();
  loadHomeChecklistHud();
  applyAreaLayout(loadAreaLayout());

  if (hudLabConn) {
    hudLabConn.addEventListener("click", async function () {
      if (hudLabStatus) hudLabStatus.textContent = "Checking connection…";
      try {
        const res = await fetch("/api/connection-health");
        const payload = await res.json();
        applyConnectionHealth(payload);
        if (hudLabStatus) {
          hudLabStatus.textContent =
            payload.message || "Health: " + (payload.overall || "unknown");
        }
        // Deep-link into Settings without replacing the home canvas permanently.
        openArea("settings");
      } catch (err) {
        if (hudLabStatus) hudLabStatus.textContent = "Connection check failed.";
      }
    });
  }

  if (hudLabDraft) {
    hudLabDraft.addEventListener("click", async function () {
      const key = hudLabIssue && hudLabIssue.value ? hudLabIssue.value.trim() : "";
      if (!key) {
        if (hudLabStatus) hudLabStatus.textContent = "Enter a story key first.";
        return;
      }
      if (hudLabStatus) hudLabStatus.textContent = "Drafting from " + key + "…";
      try {
        const res = await fetch("/api/plans/draft", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ issue_key: key }),
        });
        const payload = await res.json();
        if (payload.status !== "ok" || !payload.plan) {
          if (hudLabStatus) {
            hudLabStatus.textContent = payload.message || "Draft failed.";
          }
          return;
        }
        if (planIssueKey) planIssueKey.value = key;
        await loadPlanList(payload.plan.id);
        openPlanId = payload.plan.id;
        renderPlanCases(payload.plan);
        await refreshLabHome();
        if (hudLabStatus) {
          hudLabStatus.textContent = payload.message || "Drafted.";
        }
        openArea("plans");
      } catch (err) {
        if (hudLabStatus) hudLabStatus.textContent = "Draft request failed.";
      }
    });
  }

  if (hudLabStarter) {
    hudLabStarter.addEventListener("click", async function () {
      if (hudLabStatus) hudLabStatus.textContent = "Creating starter template…";
      try {
        const res = await fetch("/api/plans/starter", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "Starter plan" }),
        });
        const payload = await res.json();
        if (payload.status !== "ok" || !payload.plan) {
          if (hudLabStatus) {
            hudLabStatus.textContent = payload.message || "Starter failed.";
          }
          return;
        }
        await loadPlanList(payload.plan.id);
        openPlanId = payload.plan.id;
        renderPlanCases(payload.plan);
        await refreshLabHome();
        if (hudLabStatus) {
          hudLabStatus.textContent = payload.message || "Starter created.";
        }
        openArea("plans");
      } catch (err) {
        if (hudLabStatus) hudLabStatus.textContent = "Starter request failed.";
      }
    });
  }

  function formatJiraRead(payload) {
    if (!payload || typeof payload !== "object") {
      return "No response";
    }
    if (payload.status && payload.status !== "ok") {
      return (
        (payload.status || "error") +
        ": " +
        (payload.message || payload.error || "request failed")
      );
    }
    const lines = [
      (payload.key || "?") + " — " + (payload.summary || "(no summary)"),
      "Type: " + (payload.type || "—") + " · Status: " + (payload.issue_status || "—"),
      "",
      "Acceptance criteria:",
      payload.has_acceptance_criteria
        ? payload.acceptance_criteria || "(empty)"
        : "(none found in description)",
      "",
      "Description:",
      payload.description || "(empty)",
    ];
    return lines.join("\n");
  }

  if (jiraReadBtn) {
    jiraReadBtn.addEventListener("click", async function () {
      const key = jiraReadKey && jiraReadKey.value ? jiraReadKey.value.trim() : "";
      if (jiraReadStatus) jiraReadStatus.textContent = "Reading…";
      if (jiraReadOut) {
        jiraReadOut.hidden = true;
        jiraReadOut.textContent = "";
      }
      if (!key) {
        if (jiraReadStatus) jiraReadStatus.textContent = "Enter an issue key (e.g. KAN-89).";
        return;
      }
      try {
        const res = await fetch(
          "/api/jira-issue/" + encodeURIComponent(key.toUpperCase())
        );
        const payload = await res.json();
        const text = formatJiraRead(payload);
        if (jiraReadOut) {
          jiraReadOut.hidden = false;
          jiraReadOut.textContent = text;
        }
        if (jiraReadStatus) {
          jiraReadStatus.textContent =
            payload && payload.status === "ok"
              ? "Loaded " + (payload.key || key)
              : payload && payload.message
                ? payload.message
                : "Read failed";
        }
      } catch (err) {
        if (jiraReadStatus) {
          jiraReadStatus.textContent = "Read failed: " + (err && err.message ? err.message : err);
        }
      }
    });
  }

  if (setSave) {
    setSave.addEventListener("click", async function () {
      if (setStatus) setStatus.textContent = "Saving…";
      try {
        const res = await fetch("/api/app-settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            jira_url: setJiraUrl && setJiraUrl.value ? setJiraUrl.value.trim() : "",
            jira_project:
              setJiraProject && setJiraProject.value
                ? setJiraProject.value.trim()
                : "",
            target_url:
              setTargetUrl && setTargetUrl.value ? setTargetUrl.value.trim() : "",
            target_app_path:
              setTargetExe && setTargetExe.value ? setTargetExe.value.trim() : "",
            api_endpoint:
              setApiEndpoint && setApiEndpoint.value
                ? setApiEndpoint.value.trim()
                : "",
            test_framework:
              setTestFramework && setTestFramework.value
                ? setTestFramework.value
                : "playwright",
            playwright_mode:
              setPlaywrightMode && setPlaywrightMode.value
                ? setPlaywrightMode.value
                : "headed",
            ollama_model:
              setOllamaModel && setOllamaModel.value
                ? setOllamaModel.value.trim()
                : "",
            run_finish_notify_enabled: !!(
              setRunFinishNotify && setRunFinishNotify.checked
            ),
          }),
        });
        const payload = await res.json();
        applyAppSettings(payload);
        await loadOllamaModels();
        if (setStatus) {
          setStatus.textContent =
            payload.message ||
            (payload.status === "updated" ? "Saved." : "Save failed.");
        }
        if (ollamaModelStatus && payload.status === "error") {
          ollamaModelStatus.textContent = payload.message || "Model save refused.";
        }
      } catch (err) {
        if (setStatus) setStatus.textContent = "Could not save app settings.";
      }
    });
  }

  if (setSecondPcPack) {
    setSecondPcPack.addEventListener("click", async function () {
      if (setSecondPcStatus) {
        setSecondPcStatus.textContent = "Building second-PC install pack…";
      }
      try {
        const res = await fetch("/api/installer/second-pc-pack", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "desktop" }),
        });
        const data = await res.json();
        if (!data || data.status !== "ok") {
          if (setSecondPcStatus) {
            setSecondPcStatus.textContent =
              (data && (data.message || data.error)) ||
              "Install pack failed.";
          }
          return;
        }
        if (setSecondPcStatus) {
          setSecondPcStatus.textContent =
            "Pack " +
            (data.folder_name || "") +
            " · " +
            (data.path || "") +
            " · secrets: none · cloud: no · telemetry default: off. Copy folder to the second PC, run SetupSecondPC.ps1, then RunDesktop.cmd.";
        }
      } catch (err) {
        if (setSecondPcStatus) {
          setSecondPcStatus.textContent = "Could not build install pack.";
        }
      }
    });
  }

  if (setEnvSave) {
    setEnvSave.addEventListener("click", async function () {
      if (envStatus) envStatus.textContent = "Saving environment…";
      try {
        const selectedId =
          setEnvActive && setEnvActive.value ? setEnvActive.value : "";
        const nameVal =
          setEnvName && setEnvName.value ? setEnvName.value.trim() : "";
        const selectedLabel =
          setEnvActive && setEnvActive.selectedOptions && setEnvActive.selectedOptions[0]
            ? String(setEnvActive.selectedOptions[0].textContent || "")
                .split(" — ")[0]
                .trim()
            : "";
        // Same name as selected → update; otherwise create a new named target.
        const envId =
          selectedId && selectedLabel.toLowerCase() === nameVal.toLowerCase()
            ? selectedId
            : null;
        const res = await fetch("/api/environments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: nameVal,
            target_url:
              setTargetUrl && setTargetUrl.value ? setTargetUrl.value.trim() : "",
            target_app_path:
              setTargetExe && setTargetExe.value ? setTargetExe.value.trim() : "",
            api_endpoint:
              setApiEndpoint && setApiEndpoint.value
                ? setApiEndpoint.value.trim()
                : "",
            env_id: envId,
            activate: true,
          }),
        });
        const payload = await res.json();
        applyEnvironments(payload);
        await loadAppSettings();
        if (envStatus) {
          envStatus.textContent =
            payload.message ||
            (payload.status === "ok" ? "Environment saved." : "Save failed.");
        }
      } catch (err) {
        if (envStatus) envStatus.textContent = "Could not save environment.";
      }
    });
  }

  async function activateSelectedEnvironment(selectEl, statusEl) {
    const envId = selectEl && selectEl.value ? selectEl.value : "";
    if (!envId) {
      if (statusEl) statusEl.textContent = "Pick an environment first.";
      return;
    }
    if (statusEl) statusEl.textContent = "Activating…";
    try {
      const res = await fetch("/api/environments/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ env_id: envId }),
      });
      const payload = await res.json();
      applyEnvironments(payload);
      await loadAppSettings();
      if (statusEl) {
        statusEl.textContent =
          payload.message ||
          (payload.status === "ok" ? "Activated." : "Activate failed.");
      }
    } catch (err) {
      if (statusEl) statusEl.textContent = "Could not activate environment.";
    }
  }

  if (setEnvActivate) {
    setEnvActivate.addEventListener("click", function () {
      activateSelectedEnvironment(setEnvActive, envStatus);
    });
  }

  if (planEnvActivate) {
    planEnvActivate.addEventListener("click", function () {
      activateSelectedEnvironment(planEnvActive, planEnvStatus);
    });
  }

  if (planEnvRefresh) {
    planEnvRefresh.addEventListener("click", function () {
      loadEnvironments();
    });
  }

  function selectedSandboxId() {
    if (!planSandboxSelect) return "";
    return (planSandboxSelect.value || "").trim();
  }

  function updatePlanSandboxStatus() {
    if (!planSandboxStatus) return;
    const sid = selectedSandboxId();
    if (!sid) {
      planSandboxStatus.textContent = "Sandbox: default profile";
      return;
    }
    const opt = planSandboxSelect.options[planSandboxSelect.selectedIndex];
    const label = opt ? opt.textContent : sid;
    planSandboxStatus.textContent = "Sandbox: " + label;
  }

  async function loadPlanRunSandboxes() {
    if (!planSandboxSelect) return;
    const previous = selectedSandboxId();
    try {
      const res = await fetch("/api/plans/run-sandboxes");
      const payload = await res.json();
      planSandboxSelect.innerHTML = "";
      const def = document.createElement("option");
      def.value = "";
      def.textContent = "Normal browser profile (default)";
      planSandboxSelect.appendChild(def);
      const enabled = !!payload.plugin_enabled;
      const boxes = payload.sandboxes || [];
      if (!enabled) {
        planSandboxSelect.disabled = true;
        if (planSandboxStatus) {
          planSandboxStatus.textContent =
            payload.message ||
            "Sandbox plugin disabled — using normal browser profile.";
        }
        return;
      }
      planSandboxSelect.disabled = false;
      boxes.forEach(function (box) {
        if (!box || !box.id) return;
        const opt = document.createElement("option");
        opt.value = box.id;
        opt.textContent =
          (box.label || box.id) +
          (box.url ? " — " + box.url : "") +
          (box.status ? " [" + box.status + "]" : "");
        planSandboxSelect.appendChild(opt);
      });
      if (previous) {
        planSandboxSelect.value = previous;
        if (planSandboxSelect.value !== previous) {
          planSandboxSelect.value = "";
        }
      }
      updatePlanSandboxStatus();
      if (planSandboxStatus && payload.message && !selectedSandboxId()) {
        planSandboxStatus.textContent =
          "Sandbox: default profile — " + payload.message;
      }
    } catch (err) {
      if (planSandboxStatus) {
        planSandboxStatus.textContent = "Could not load run sandboxes.";
      }
    }
  }

  if (planSandboxRefresh) {
    planSandboxRefresh.addEventListener("click", function () {
      loadPlanRunSandboxes();
    });
  }

  if (planSandboxSelect) {
    planSandboxSelect.addEventListener("change", updatePlanSandboxStatus);
  }

  if (setEnvNew) {
    setEnvNew.addEventListener("click", function () {
      if (setEnvActive) setEnvActive.value = "";
      focusEnvironmentDetail(
        { id: "", name: "", target_url: "", target_app_path: "", api_endpoint: "" },
        { isNew: true, focusField: true }
      );
      if (setEnvScanBody) {
        setEnvScanBody.querySelectorAll(".settings-scan-row").forEach(function (row) {
          row.classList.remove("is-focus");
        });
      }
      if (envStatus) envStatus.textContent = "Drafting a new named environment.";
    });
  }

  if (setEnvDelete) {
    setEnvDelete.addEventListener("click", function () {
      const envId = setEnvActive && setEnvActive.value ? setEnvActive.value : "";
      if (!envId) {
        if (envStatus) envStatus.textContent = "Pick an environment to delete.";
        resetEnvDeleteConfirm();
        return;
      }
      if (setEnvDeleteConfirm) setEnvDeleteConfirm.disabled = false;
      if (envStatus) envStatus.textContent = "Confirm delete in the detail pane.";
    });
  }

  if (setEnvDeleteConfirm) {
    setEnvDeleteConfirm.addEventListener("click", async function () {
      const envId = setEnvActive && setEnvActive.value ? setEnvActive.value : "";
      if (!envId) {
        if (envStatus) envStatus.textContent = "Pick an environment to delete.";
        resetEnvDeleteConfirm();
        return;
      }
      if (envStatus) envStatus.textContent = "Deleting…";
      try {
        const res = await fetch(
          "/api/environments/" + encodeURIComponent(envId) + "/delete",
          { method: "POST" }
        );
        const payload = await res.json();
        applyEnvironments(payload);
        await loadAppSettings();
        if (envStatus) {
          envStatus.textContent =
            payload.message ||
            (payload.status === "ok" ? "Deleted." : "Delete failed.");
        }
      } catch (err) {
        if (envStatus) envStatus.textContent = "Could not delete environment.";
      } finally {
        resetEnvDeleteConfirm();
      }
    });
  }

  if (setEnvActive) {
    setEnvActive.addEventListener("change", function () {
      const id = setEnvActive.value;
      loadEnvironments().then(function (payload) {
        if (!payload) return;
        const envs = payload.environments || payload.named_environments || [];
        const match = envs.find(function (e) {
          return e.id === id;
        });
        if (!match) return;
        focusEnvironmentDetail(match, { focusField: true });
      });
    });
  }

  if (ollamaRefreshBtn) {
    ollamaRefreshBtn.addEventListener("click", function () {
      loadOllamaModels();
    });
  }

  if (planDraftBtn) {
    planDraftBtn.addEventListener("click", async function () {
      if (planStatus) planStatus.textContent = "Drafting…";
      try {
        const res = await fetch("/api/plans/draft", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            issue_key: planIssueKey && planIssueKey.value ? planIssueKey.value.trim() : "",
            document_text: planDocText && planDocText.value ? planDocText.value : "",
            document_name: planDocName && planDocName.value ? planDocName.value.trim() : "",
          }),
        });
        const payload = await res.json();
        if (payload.status !== "ok" || !payload.plan) {
          if (planStatus) {
            planStatus.textContent = payload.message || "Draft failed.";
          }
          return;
        }
        await loadPlanList(payload.plan.id);
        openPlanId = payload.plan.id;
        renderPlanCases(payload.plan);
        if (typeof refreshLabHome === "function") await refreshLabHome();
        if (planStatus) {
          planStatus.textContent = payload.message || "Drafted.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Draft request failed.";
      }
    });
  }

  if (planDraftProjectBtn) {
    planDraftProjectBtn.addEventListener("click", async function () {
      if (planStatus) planStatus.textContent = "Drafting from project…";
      let batch = 5;
      if (planBatchSize && planBatchSize.value !== "") {
        const n = parseInt(planBatchSize.value, 10);
        if (!isNaN(n)) batch = n;
      }
      try {
        const res = await fetch("/api/plans/draft-project", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ batch_size: batch }),
        });
        const payload = await res.json();
        if (payload.status !== "ok" || !payload.plan) {
          if (planStatus) {
            planStatus.textContent = payload.message || "Project draft failed.";
          }
          return;
        }
        if (
          planBatchSize &&
          payload.batch_size != null &&
          !isNaN(Number(payload.batch_size))
        ) {
          planBatchSize.value = String(payload.batch_size);
        }
        await loadPlanList(payload.plan.id);
        openPlanId = payload.plan.id;
        renderPlanCases(payload.plan);
        if (payload.coverage_gaps && payload.coverage_gaps.status === "ok") {
          renderCoverageGaps(payload.coverage_gaps);
        } else {
          await refreshCoverageGaps();
        }
        await refreshTraceabilityMatrix();
        if (typeof refreshLabHome === "function") await refreshLabHome();
        if (planStatus) {
          planStatus.textContent = payload.message || "Project draft ready — review before run.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Project draft request failed.";
      }
    });
  }

  async function importPlaywrightIntoPlan(attachToOpen) {
    const pathValue =
      planPwPath && planPwPath.value ? planPwPath.value.trim() : "";
    if (!pathValue) {
      if (planStatus) {
        planStatus.textContent =
          "Enter a Playwright project path (or set one under Suites).";
      }
      return;
    }
    if (attachToOpen && !openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) {
      planStatus.textContent = attachToOpen
        ? "Adding Playwright cases to open plan…"
        : "Importing Playwright project into suite…";
    }
    try {
      const body = { suite_path: pathValue };
      if (attachToOpen) body.plan_id = openPlanId;
      const res = await fetch("/api/plans/import-playwright", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Playwright import failed.";
        }
        return;
      }
      await loadPlanList(payload.plan.id);
      openPlanId = payload.plan.id;
      renderPlanCases(payload.plan);
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          payload.message ||
          "Playwright cases imported. External files unchanged.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Playwright import request failed.";
    }
  }

  if (planImportPwBtn) {
    planImportPwBtn.addEventListener("click", function () {
      importPlaywrightIntoPlan(false);
    });
  }
  if (planImportPwAddBtn) {
    planImportPwAddBtn.addEventListener("click", function () {
      importPlaywrightIntoPlan(true);
    });
  }

  async function addDesktopCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding desktop case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/desktop",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add desktop case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Desktop case added — runs via desktop plugin against connected exe.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Desktop case request failed.";
    }
  }

  if (planAddDesktopBtn) {
    planAddDesktopBtn.addEventListener("click", function () {
      addDesktopCaseToOpenPlan();
    });
  }

  async function addApiCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding API/messaging case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/api",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add API/messaging case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "API/messaging case added — calls saved endpoint; body redacted in log.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "API/messaging case request failed.";
    }
  }

  if (planAddApiBtn) {
    planAddApiBtn.addEventListener("click", function () {
      addApiCaseToOpenPlan();
    });
  }

  async function addContractCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding mock/contract case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/contract",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add mock/contract case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Mock/contract case added — local fixture; run record marked mock.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Mock/contract case request failed.";
    }
  }

  if (planAddContractBtn) {
    planAddContractBtn.addEventListener("click", function () {
      addContractCaseToOpenPlan();
    });
  }

  async function addSeedCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding seed/fixture case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/seed",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add seed/fixture case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Seed/fixture case added — named local fixture; run stores name.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Seed/fixture case request failed.";
    }
  }

  if (planAddSeedBtn) {
    planAddSeedBtn.addEventListener("click", function () {
      addSeedCaseToOpenPlan();
    });
  }

  async function addVisualCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding visual baseline case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/visual",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add visual baseline case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Visual baseline case added — opt-in compare; update-baseline is explicit.";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Visual baseline case request failed.";
    }
  }

  if (planAddVisualBtn) {
    planAddVisualBtn.addEventListener("click", function () {
      addVisualCaseToOpenPlan();
    });
  }

  async function addA11yCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding accessibility check case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/a11y",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add accessibility check case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Accessibility check case added — opt-in; violations attach without replacing functional result.";
      }
    } catch (err) {
      if (planStatus) {
        planStatus.textContent = "Accessibility check case request failed.";
      }
    }
  }

  if (planAddA11yBtn) {
    planAddA11yBtn.addEventListener("click", function () {
      addA11yCaseToOpenPlan();
    });
  }

  async function addPerfCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Adding performance budget case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/perf",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add performance budget case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent =
          "Performance budget case added — over budget fails that case; local timing only.";
      }
    } catch (err) {
      if (planStatus) {
        planStatus.textContent = "Performance budget case request failed.";
      }
    }
  }

  if (planAddPerfBtn) {
    planAddPerfBtn.addEventListener("click", function () {
      addPerfCaseToOpenPlan();
    });
  }

  function isStubFramework(fw) {
    const key = String(fw || "")
      .trim()
      .toLowerCase();
    return key === "selenium" || key === "cypress";
  }

  function selectedCaseFrameworkId() {
    const cid =
      planCaseId && planCaseId.value ? String(planCaseId.value).trim() : "";
    if (!cid || !openPlanCases.length) return "";
    for (let i = 0; i < openPlanCases.length; i++) {
      const c = openPlanCases[i];
      if (!c || c.id !== cid) continue;
      const kind = (c.source && c.source.kind) || "";
      if (kind !== "framework") return "";
      const ref = String((c.source && c.source.ref) || "")
        .trim()
        .toLowerCase();
      if (ref.indexOf("{") === 0) {
        try {
          const parsed = JSON.parse(ref);
          return String(
            (parsed && (parsed.framework || parsed.test_framework || parsed.id)) ||
              ""
          )
            .trim()
            .toLowerCase();
        } catch (err) {
          return ref.slice(0, 40);
        }
      }
      return ref.slice(0, 40);
    }
    return "";
  }

  function syncFrameworkStubHonestyUi() {
    if (planFrameworkSelect) {
      const cur = String(planFrameworkSelect.value || "")
        .trim()
        .toLowerCase();
      if (!cur || (cur !== "playwright" && cur !== "selenium" && cur !== "cypress")) {
        planFrameworkSelect.value = "playwright";
      }
    }
    if (setTestFramework) {
      activeSettingsFramework = String(setTestFramework.value || "playwright")
        .trim()
        .toLowerCase();
    }
    const caseFw = selectedCaseFrameworkId();
    const settingsStub = isStubFramework(activeSettingsFramework);
    const caseStub = isStubFramework(caseFw);
    const blockRun = caseStub || settingsStub;
    if (planCaseRun) {
      planCaseRun.disabled = !!blockRun;
      planCaseRun.setAttribute(
        "aria-disabled",
        blockRun ? "true" : "false"
      );
      planCaseRun.title = blockRun
        ? caseStub
          ? "Run disabled — " +
            caseFw +
            " is not implemented (never pass). Switch case or use Playwright."
          : "Run disabled — Settings test framework is " +
            activeSettingsFramework +
            " (not implemented — never pass). Switch back to Playwright."
        : "Run selected case (headed)";
    }
    if (planFrameworkRunHint) {
      if (blockRun) {
        planFrameworkRunHint.hidden = false;
        planFrameworkRunHint.textContent = caseStub
          ? "Stub honesty: selected case uses " +
            caseFw +
            " — not implemented; Run disabled; never pass."
          : "Stub honesty: Settings framework is " +
            activeSettingsFramework +
            " — not implemented; Run disabled; never pass. Switch to Playwright to run.";
      } else {
        planFrameworkRunHint.hidden = true;
        planFrameworkRunHint.textContent = "";
      }
    }
  }

  async function addFrameworkCaseToOpenPlan() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    const fw =
      planFrameworkSelect && planFrameworkSelect.value
        ? String(planFrameworkSelect.value).trim().toLowerCase()
        : "playwright";
    if (planStatus) planStatus.textContent = "Adding framework case…";
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/cases/framework",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ framework: fw || "playwright" }),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok" || !payload.plan) {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not add framework case.";
        }
        return;
      }
      renderPlanCases(payload.plan);
      if (payload.case && planCaseId) {
        planCaseId.value = payload.case.id || "";
      }
      syncFrameworkStubHonestyUi();
      if (typeof refreshLabHome === "function") await refreshLabHome();
      if (planStatus) {
        planStatus.textContent = isStubFramework(fw)
          ? "Framework stub case added — " +
            fw +
            " is not implemented; Run stays disabled and never passes. Default remains Playwright."
          : "Framework case added — Playwright (ready).";
      }
    } catch (err) {
      if (planStatus) {
        planStatus.textContent = "Framework case request failed.";
      }
    }
  }

  if (planAddFrameworkBtn) {
    planAddFrameworkBtn.addEventListener("click", function () {
      addFrameworkCaseToOpenPlan();
    });
  }

  if (planFrameworkSelect) {
    planFrameworkSelect.addEventListener("change", function () {
      syncFrameworkStubHonestyUi();
    });
  }

  if (setTestFramework) {
    setTestFramework.addEventListener("change", function () {
      activeSettingsFramework = String(setTestFramework.value || "playwright")
        .trim()
        .toLowerCase();
      syncFrameworkStubHonestyUi();
    });
  }

  syncFrameworkStubHonestyUi();

  async function updateVisualBaselineForSelectedCase() {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    const cid = planCaseId && planCaseId.value ? planCaseId.value.trim() : "";
    if (!cid) {
      if (planStatus) planStatus.textContent = "Select a visual case first.";
      return;
    }
    if (planStatus) planStatus.textContent = "Updating visual baseline (explicit)…";
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/cases/" +
          encodeURIComponent(cid) +
          "/visual-baseline",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Could not update visual baseline.";
        }
        return;
      }
      if (payload.plan) renderPlanCases(payload.plan);
      if (planStatus) {
        planStatus.textContent =
          "Visual baseline updated explicitly (not auto on mismatch).";
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Update visual baseline failed.";
    }
  }

  if (planUpdateBaselineBtn) {
    planUpdateBaselineBtn.addEventListener("click", function () {
      updateVisualBaselineForSelectedCase();
    });
  }

  if (planSearchBtn) {
    planSearchBtn.addEventListener("click", function () {
      runPlanSearch();
    });
  }
  if (planSearchQ) {
    planSearchQ.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        runPlanSearch();
      }
    });
  }

  if (planCoverageBtn) {
    planCoverageBtn.addEventListener("click", function () {
      refreshCoverageGaps();
    });
  }
  if (planDriftCheckBtn) {
    planDriftCheckBtn.addEventListener("click", function () {
      postAcceptanceDrift("/acceptance-drift");
    });
  }
  if (planDriftKeepBtn) {
    planDriftKeepBtn.addEventListener("click", function () {
      postAcceptanceDrift("/acceptance-drift/keep");
    });
  }
  if (planDriftRefreshBtn) {
    planDriftRefreshBtn.addEventListener("click", function () {
      postAcceptanceDrift("/acceptance-drift/refresh");
    });
  }
  if (planCoverageFilter) {
    planCoverageFilter.addEventListener("change", function () {
      refreshCoverageGaps();
    });
    planCoverageFilter.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        refreshCoverageGaps();
      }
    });
  }
  if (planTraceBtn) {
    planTraceBtn.addEventListener("click", function () {
      refreshTraceabilityMatrix();
    });
  }
  if (planTraceFilter) {
    planTraceFilter.addEventListener("change", function () {
      refreshTraceabilityMatrix();
    });
    planTraceFilter.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        refreshTraceabilityMatrix();
      }
    });
  }
  if (planHistoryBtn) {
    planHistoryBtn.addEventListener("click", function () {
      refreshSuiteHistory();
    });
  }
  if (planCompareBtn) {
    planCompareBtn.addEventListener("click", function () {
      runSuiteCompare();
    });
  }

  if (planRefreshBtn) {
    planRefreshBtn.addEventListener("click", function () {
      loadPlanList(openPlanId);
    });
  }

  if (planLoadBtn) {
    planLoadBtn.addEventListener("click", function () {
      const id = planList && planList.value ? planList.value : "";
      openPlan(id);
    });
  }

  if (planDocAddBtn) {
    planDocAddBtn.addEventListener("click", async function () {
      if (!openPlanId) {
        if (planStatus) planStatus.textContent = "Open a plan first.";
        return;
      }
      if (planStatus) planStatus.textContent = "Adding document cases…";
      try {
        const res = await fetch(
          "/api/plans/" + encodeURIComponent(openPlanId) + "/draft-document",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              document_text: planDocText && planDocText.value ? planDocText.value : "",
              document_name:
                planDocName && planDocName.value
                  ? planDocName.value.trim()
                  : "uploaded-document",
              jira_key:
                planIssueKey && planIssueKey.value ? planIssueKey.value.trim() : "",
            }),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent = payload.message || "Document draft failed.";
          }
          return;
        }
        if (payload.plan) renderPlanCases(payload.plan);
        else await openPlan(openPlanId);
        if (planStatus) {
          planStatus.textContent = payload.message || "Document cases added.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Document draft request failed.";
      }
    });
  }

  if (planCaseSave) {
    planCaseSave.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Pick a case id first.";
        return;
      }
      if (planStatus) planStatus.textContent = "Saving case…";
      try {
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: planCaseName ? planCaseName.value : null,
              note: planCaseNote ? planCaseNote.value : null,
              enabled: planCaseEnabled ? !!planCaseEnabled.checked : true,
              archived: planCaseArchived ? !!planCaseArchived.checked : false,
              tags: planCaseTags
                ? planCaseTags.value
                    .split(",")
                    .map(function (t) {
                      return t.trim();
                    })
                    .filter(Boolean)
                : [],
              priority: planCasePriority
                ? parseInt(planCasePriority.value || "0", 10) || 0
                : 0,
              step_timeout_ms: planCaseStepTimeout
                ? parseInt(planCaseStepTimeout.value || "10000", 10) || 10000
                : 10000,
            }),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent = payload.message || "Case save failed.";
          }
          return;
        }
        if (payload.plan) renderPlanCases(payload.plan);
        if (planStatus) {
          const archivedNow = !!(payload.case && payload.case.archived);
          planStatus.textContent = archivedNow
            ? "Case archived (runs kept; hidden from default list)."
            : "Case saved locally.";
        }
        await refreshCaseDetail();
      } catch (err) {
        if (planStatus) planStatus.textContent = "Case save request failed.";
      }
    });
  }

  if (planShowArchived) {
    planShowArchived.addEventListener("change", function () {
      if (!openPlanId) return;
      renderPlanCases({
        suite: { cases: openPlanCases },
        intent: planIntent && !planIntent.hidden ? planIntent.textContent : "",
      });
    });
  }

  if (planFlakeRefresh) {
    planFlakeRefresh.addEventListener("click", async function () {
      if (!openPlanId) {
        if (planStatus) planStatus.textContent = "Open a plan first.";
        return;
      }
      await refreshFlakeReport();
      renderPlanCases({
        suite: { cases: openPlanCases },
        intent: planIntent && !planIntent.hidden ? planIntent.textContent : "",
      });
      await refreshCaseDetail();
      if (planStatus) planStatus.textContent = "Flake scores refreshed.";
    });
  }

  if (planQuarantineSet) {
    planQuarantineSet.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Pick a case id first.";
        return;
      }
      const reason =
        planQuarantineReason && planQuarantineReason.value
          ? planQuarantineReason.value.trim()
          : "";
      const expires =
        planQuarantineExpires && planQuarantineExpires.value
          ? planQuarantineExpires.value.trim()
          : "";
      if (!reason || !expires) {
        if (planStatus) {
          planStatus.textContent =
            "Quarantine requires a reason and an expiry (ISO datetime).";
        }
        return;
      }
      if (planStatus) planStatus.textContent = "Quarantining case…";
      try {
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()) +
            "/quarantine",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reason: reason, expires_at: expires }),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent = payload.message || "Quarantine failed.";
          }
          return;
        }
        if (payload.plan) {
          await refreshFlakeReport();
          renderPlanCases(payload.plan);
        }
        await refreshCaseDetail();
        if (planStatus) {
          planStatus.textContent =
            payload.message ||
            "Case quarantined (skipped on run, not counted as pass).";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Quarantine request failed.";
      }
    });
  }

  if (planQuarantineClear) {
    planQuarantineClear.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Pick a case id first.";
        return;
      }
      if (planStatus) planStatus.textContent = "Clearing quarantine…";
      try {
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()) +
            "/quarantine/clear",
          { method: "POST" }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent =
              payload.message || "Clear quarantine failed.";
          }
          return;
        }
        if (payload.plan) {
          await refreshFlakeReport();
          renderPlanCases(payload.plan);
        }
        await refreshCaseDetail();
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Quarantine cleared — case selectable again.";
        }
      } catch (err) {
        if (planStatus) {
          planStatus.textContent = "Clear quarantine request failed.";
        }
      }
    });
  }

  function selectedParallelCount() {
    if (!planParallelCount) return 1;
    const n = parseInt(planParallelCount.value, 10);
    return Number.isFinite(n) && n >= 1 ? n : 1;
  }

  async function runPlanByTag(tagValue) {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    const tag = (tagValue || "").trim().toLowerCase();
    if (!tag) {
      if (planStatus) planStatus.textContent = "Enter a tag (e.g. smoke or regression).";
      return;
    }
    const parallel = selectedParallelCount();
    if (planRunTag) planRunTag.value = tag;
    if (planStatus) {
      planStatus.textContent =
        "Running tag " +
        tag +
        (parallel <= 1 ? " (sequential)…" : " (parallel=" + parallel + ")…");
    }
    if (planTagRunOut) {
      planTagRunOut.hidden = false;
      planTagRunOut.textContent = "Running…";
    }
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/run-by-tag",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tag: tag,
            parallel: parallel,
            sandbox_id: selectedSandboxId(),
          }),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        if (planStatus) {
          planStatus.textContent = payload.message || "Tag run failed.";
        }
        if (planTagRunOut) {
          planTagRunOut.textContent = payload.message || "Tag run failed.";
        }
        return;
      }
      if (payload.suite_run_id) lastSuiteRunId = payload.suite_run_id;
      if (payload.plan) renderPlanCases(payload.plan);
      showLocalRunNotice(payload.local_notice);
      const skipped = payload.skipped || [];
      const notSelected = payload.not_selected || [];
      const results = payload.case_results || [];
      const lines = [
        payload.message || "Tag run finished.",
        "Suite run: " + (payload.suite_run_id || "—"),
        "Tag: " + (payload.tag || tag),
        "Parallel count: " + (payload.parallel_count != null ? payload.parallel_count : parallel),
        "Sequential: " + (payload.sequential ? "yes" : "no"),
        payload.pass != null
          ? "Pass/fail: " + payload.pass + " / " + (payload.fail != null ? payload.fail : 0)
          : null,
        "",
        "Executed:",
        results.length
          ? results
              .map(function (r) {
                return (
                  "- " +
                  (r.case_id || "?") +
                  " → " +
                  (r.result || r.status || "?")
                );
              })
              .join("\n")
          : "(none)",
        "",
        "Skipped:",
        skipped.length
          ? skipped
              .map(function (s) {
                return "- " + (s.case_id || "?") + " — " + (s.reason || "");
              })
              .join("\n")
          : "(none)",
        "",
        "Not selected (untagged for this run):",
        notSelected.length
          ? notSelected
              .map(function (s) {
                return "- " + (s.case_id || "?");
              })
              .join("\n")
          : "(none)",
      ].filter(function (line) {
        return line !== null;
      });
      if (planTagRunOut) {
        planTagRunOut.hidden = false;
        planTagRunOut.textContent = lines.join("\n");
      }
      if (planStatus) {
        planStatus.textContent =
          (payload.message || "Tag run finished.") +
          " Tag=" +
          (payload.tag || tag);
      }
      await refreshCaseDetail();
    } catch (err) {
      if (planStatus) planStatus.textContent = "Tag run request failed.";
      if (planTagRunOut) {
        planTagRunOut.hidden = false;
        planTagRunOut.textContent = "Tag run request failed.";
      }
    }
  }

  if (planRunByTag) {
    planRunByTag.addEventListener("click", function () {
      runPlanByTag(planRunTag ? planRunTag.value : "");
    });
  }
  if (planRunTagSmoke) {
    planRunTagSmoke.addEventListener("click", function () {
      runPlanByTag("smoke");
    });
  }
  if (planRunTagRegression) {
    planRunTagRegression.addEventListener("click", function () {
      runPlanByTag("regression");
    });
  }

  function renderScheduleInfo(payload) {
    if (!payload) return;
    const sch = payload.schedule;
    if (planScheduleStatus) {
      if (payload.enabled && sch) {
        planScheduleStatus.textContent =
          "Schedule: " +
          (sch.tag || "?") +
          " at " +
          (sch.time_local || "?") +
          " (sequential" +
          (payload.has_saved_connection ? ", connection saved" : ", no saved connection") +
          ")";
      } else {
        planScheduleStatus.textContent = "Schedule: off";
      }
    }
    if (sch && planScheduleTag && !planScheduleTag.value) {
      planScheduleTag.value = sch.tag || "";
    }
    if (sch && planScheduleTime && sch.time_local) {
      planScheduleTime.value = sch.time_local;
    }
    if (planScheduleOut) {
      const hist = payload.history || [];
      const miss = payload.recorded_misses || [];
      const lines = [
        payload.message || "",
        payload.action ? "Action: " + payload.action : null,
        payload.fired ? "Fired: yes" : null,
        payload.run && payload.run.suite_run_id
          ? "Suite run: " + payload.run.suite_run_id
          : null,
        "",
        "Recent history:",
        hist.length
          ? hist
              .slice()
              .reverse()
              .slice(0, 5)
              .map(function (h) {
                return (
                  "- " +
                  (h.due_at || "?") +
                  " → " +
                  (h.outcome || "?") +
                  (h.reason ? " (" + h.reason + ")" : "")
                );
              })
              .join("\n")
          : "(none)",
        miss.length
          ? "\nJust recorded as not run:\n" +
            miss
              .map(function (h) {
                return "- " + (h.due_at || "?") + " (" + (h.reason || "") + ")";
              })
              .join("\n")
          : null,
      ].filter(function (line) {
        return line !== null;
      });
      planScheduleOut.hidden = false;
      planScheduleOut.textContent = lines.join("\n");
    }
  }

  async function refreshPlanSchedule() {
    try {
      const res = await fetch("/api/plans/schedule");
      const payload = await res.json();
      if (payload.status === "ok") {
        renderScheduleInfo(payload);
      }
    } catch (err) {
      if (planScheduleStatus) {
        planScheduleStatus.textContent = "Schedule: (unavailable)";
      }
    }
  }

  if (planScheduleSave) {
    planScheduleSave.addEventListener("click", async function () {
      if (!openPlanId) {
        if (planStatus) planStatus.textContent = "Open a plan first.";
        return;
      }
      const tag = (planScheduleTag && planScheduleTag.value
        ? planScheduleTag.value
        : planRunTag
          ? planRunTag.value
          : ""
      ).trim();
      const timeLocal = planScheduleTime ? planScheduleTime.value : "";
      if (planStatus) planStatus.textContent = "Saving local schedule…";
      try {
        const res = await fetch("/api/plans/schedule", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            plan_id: openPlanId,
            tag: tag,
            time_local: timeLocal,
          }),
        });
        const payload = await res.json();
        renderScheduleInfo(payload);
        if (planStatus) {
          planStatus.textContent = payload.message || "Schedule saved.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Schedule save failed.";
      }
    });
  }

  if (planScheduleClear) {
    planScheduleClear.addEventListener("click", async function () {
      if (planStatus) planStatus.textContent = "Clearing schedule…";
      try {
        const res = await fetch("/api/plans/schedule/clear", { method: "POST" });
        const payload = await res.json();
        renderScheduleInfo(payload);
        if (planStatus) {
          planStatus.textContent = payload.message || "Schedule cleared.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Schedule clear failed.";
      }
    });
  }

  if (planScheduleTick) {
    planScheduleTick.addEventListener("click", async function () {
      if (planStatus) planStatus.textContent = "Checking schedule…";
      try {
        const res = await fetch("/api/plans/schedule/tick", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fire: true }),
        });
        const payload = await res.json();
        renderScheduleInfo(payload);
        if (payload.plan) {
          /* no-op: tick may not return plan */
        }
        if (payload.run && payload.run.suite_run_id) {
          lastSuiteRunId = payload.run.suite_run_id;
        }
        showLocalRunNotice(payload.local_notice || (payload.run && payload.run.local_notice));
        if (planStatus) {
          planStatus.textContent = payload.message || "Schedule checked.";
        }
        if (openPlanId) {
          try {
            const pref = await fetch("/api/plans/" + encodeURIComponent(openPlanId));
            const prefPayload = await pref.json();
            if (prefPayload.status === "ok" && prefPayload.plan) {
              renderPlanCases(prefPayload.plan);
            }
          } catch (e2) {
            /* ignore refresh errors */
          }
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Schedule check failed.";
      }
    });
  }

  // Background tick while the desktop shell is open (local only).
  setInterval(function () {
    fetch("/api/plans/schedule/tick", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fire: true }),
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (payload) {
        if (payload && payload.status === "ok") {
          if (payload.fired || (payload.recorded_misses || []).length) {
            renderScheduleInfo(payload);
          }
        }
      })
      .catch(function () {
        /* ignore background tick errors */
      });
  }, 60000);
  refreshPlanSchedule();

  if (planNotesSave) {
    planNotesSave.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Pick a case id first.";
        return;
      }
      if (planStatus) planStatus.textContent = "Saving notes…";
      try {
        const body = {
          case_note: planCaseNote ? planCaseNote.value : "",
        };
        if (lastCaseRunId) {
          body.run_id = lastCaseRunId;
          body.run_note = planRunNote ? planRunNote.value : "";
        } else if (planRunNote && planRunNote.value.trim()) {
          body.run_note = planRunNote.value;
        }
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()) +
            "/notes",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent = payload.message || "Notes save failed.";
          }
          return;
        }
        if (payload.plan) renderPlanCases(payload.plan);
        await refreshCaseDetail();
        if (planStatus) {
          planStatus.textContent =
            payload.message || "Notes saved locally (level-scoped).";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Notes save request failed.";
      }
    });
  }

  async function moveSelectedCase(delta) {
    if (!openPlanId) {
      if (planStatus) planStatus.textContent = "Open a plan first.";
      return;
    }
    const idx = selectedCaseIndex();
    if (idx < 0) {
      if (planStatus) planStatus.textContent = "Enter a case id from the list.";
      return;
    }
    const next = idx + delta;
    if (next < 0 || next >= openPlanCases.length) return;
    const ids = openPlanCases.map(function (c) {
      return c.id;
    });
    const tmp = ids[idx];
    ids[idx] = ids[next];
    ids[next] = tmp;
    try {
      const res = await fetch(
        "/api/plans/" + encodeURIComponent(openPlanId) + "/reorder",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ case_ids: ids }),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        if (planStatus) {
          planStatus.textContent = payload.message || "Reorder failed.";
        }
        return;
      }
      if (payload.plan) renderPlanCases(payload.plan);
      if (planStatus) planStatus.textContent = "Reordered locally.";
    } catch (err) {
      if (planStatus) planStatus.textContent = "Reorder request failed.";
    }
  }

  if (planCaseUp) {
    planCaseUp.addEventListener("click", function () {
      moveSelectedCase(-1);
    });
  }
  if (planCaseDown) {
    planCaseDown.addEventListener("click", function () {
      moveSelectedCase(1);
    });
  }

  if (planCaseId) {
    planCaseId.addEventListener("change", function () {
      syncPlanCaseRowFocus();
      refreshCaseDetail();
    });
    planCaseId.addEventListener("blur", function () {
      syncPlanCaseRowFocus();
      refreshCaseDetail();
    });
  }

  function setPauseActionsVisible(visible) {
    if (planPauseActions) planPauseActions.hidden = !visible;
  }

  function applyPlanRunPayload(payload) {
    if (payload.plan) renderPlanCases(payload.plan);
    if (payload.run && payload.run.id) lastCaseRunId = payload.run.id;
    if (payload.pause_state === "paused" || payload.status === "paused") {
      activePauseId = payload.pause_id || "";
      setPauseActionsVisible(!!activePauseId);
      if (planStatus) {
        planStatus.textContent =
          payload.message ||
          "Paused on fail — headed browser left open. Continue or Stop.";
      }
      return;
    }
    activePauseId = "";
    setPauseActionsVisible(false);
    showLocalRunNotice(payload.local_notice);
    const run = payload.run || {};
    if (planStatus) {
      planStatus.textContent =
        (payload.message || "Finished.") +
        (run.result ? " Result: " + run.result : "") +
        (run.duration_ms != null ? " (" + run.duration_ms + "ms)" : "");
    }
  }

  function caseLastResultIsFail(caseObj) {
    const runs = (caseObj && caseObj.runs) || [];
    if (!runs.length) return false;
    const r = String((runs[runs.length - 1] && runs[runs.length - 1].result) || "")
      .toLowerCase();
    return r === "fail" || r === "error";
  }

  function failedCaseIndexesInOpenPlan() {
    const out = [];
    for (let i = 0; i < openPlanCases.length; i++) {
      const c = openPlanCases[i];
      if (!c || c.archived) continue;
      if (caseLastResultIsFail(c)) out.push(i);
    }
    return out;
  }

  async function runSelectedCaseFromKeyboard() {
    if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
      if (planStatus) {
        planStatus.textContent =
          "Alt+R: open a plan and select a case id first.";
      }
      return;
    }
    syncFrameworkStubHonestyUi();
    if (planCaseRun && planCaseRun.disabled) {
      const caseFw = selectedCaseFrameworkId();
      if (planStatus) {
        planStatus.textContent = isStubFramework(caseFw)
          ? "Run blocked — " +
            caseFw +
            " is not implemented (never pass). Choose Playwright or another ready case."
          : "Run blocked — Settings framework " +
            activeSettingsFramework +
            " is not implemented (never pass). Switch to Playwright in Settings.";
      }
      return;
    }
    if (openAreaName !== "plans") {
      openArea("plans");
    }
    const pauseOn = !!(planPauseOnFail && planPauseOnFail.checked);
    activePauseId = "";
    setPauseActionsVisible(false);
    if (planStatus) {
      planStatus.textContent = pauseOn
        ? "Running case (headed, pause on fail)…"
        : "Running case (headed)…";
    }
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/cases/" +
          encodeURIComponent(planCaseId.value.trim()) +
          "/run",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pause_on_fail: pauseOn,
            sandbox_id: selectedSandboxId(),
          }),
        }
      );
      const payload = await res.json();
      if (
        payload.status !== "ok" &&
        payload.status !== "paused" &&
        payload.pause_state !== "paused"
      ) {
        if (planStatus) {
          planStatus.textContent = payload.message || "Run failed.";
        }
        return;
      }
      applyPlanRunPayload(payload);
      if (payload.pause_state !== "paused" && payload.status !== "paused") {
        await refreshCaseDetail();
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Run request failed.";
    }
  }

  async function selectNextFailureFromKeyboard() {
    if (openPlanId && openPlanCases.length) {
      const fails = failedCaseIndexesInOpenPlan();
      if (fails.length) {
        const cur = selectedCaseIndex();
        let pick = fails[0];
        for (let j = 0; j < fails.length; j++) {
          if (fails[j] > cur) {
            pick = fails[j];
            break;
          }
        }
        const caseObj = openPlanCases[pick];
        if (openAreaName !== "plans") openArea("plans");
        if (planCaseId) planCaseId.value = caseObj.id || "";
        if (planCaseName) planCaseName.value = caseObj.name || "";
        await refreshCaseDetail();
        if (planStatus) {
          planStatus.textContent =
            "Next failure → " +
            (caseObj.name || caseObj.id || "?") +
            " (" +
            (pick + 1) +
            "/" +
            openPlanCases.length +
            ")";
        }
        return;
      }
    }

    const hudFails =
      (testerHudCache && testerHudCache.failed_cases) || [];
    if (!hudFails.length) {
      if (planStatus) {
        planStatus.textContent =
          "Alt+N: no failed cases on the open plan or last run.";
      }
      return;
    }
    const curId =
      planCaseId && planCaseId.value ? planCaseId.value.trim() : "";
    let idx = -1;
    for (let i = 0; i < hudFails.length; i++) {
      if (hudFails[i] && hudFails[i].case_id === curId) {
        idx = i;
        break;
      }
    }
    const next = hudFails[(idx + 1) % hudFails.length];
    await openPlansOnCase(next.plan_id, next.case_id, next.case_name);
    if (planStatus) {
      planStatus.textContent =
        "Next failure → " + (next.case_name || next.case_id || "?");
    }
  }

  if (planCaseRun) {
    planCaseRun.addEventListener("click", function () {
      runSelectedCaseFromKeyboard();
    });
  }

  if (planStartManual) {
    planStartManual.addEventListener("click", function () {
      openManualFromPlansDeepLink();
    });
  }
  if (manualClearContext) {
    manualClearContext.addEventListener("click", function () {
      clearManualLinkedContext();
    });
  }
  if (manualOpenPlans) {
    manualOpenPlans.addEventListener("click", function () {
      openArea("plans");
    });
  }
  if (manualRefreshSessions) {
    manualRefreshSessions.addEventListener("click", function () {
      refreshManualSessions();
    });
  }
  if (manualSessionList) {
    function activateManualScanRow(row) {
      if (!row) return;
      const sid = row.getAttribute("data-session-id") || "";
      if (!sid) return;
      const reviewable = row.getAttribute("data-reviewable") === "1";
      const charterCell =
        row.cells && row.cells[1] ? row.cells[1].textContent : "";
      focusManualSessionRow({
        id: sid,
        charter: charterCell,
        reviewable: reviewable,
        status: row.getAttribute("data-session-status") || "",
      });
      if (!reviewable) {
        if (manualStatus) {
          manualStatus.textContent =
            "Session focused — not reviewable (row does not start capture)";
        }
        return;
      }
      reopenManualFromLibrary(sid);
    }
    manualSessionList.addEventListener("click", function (ev) {
      const t = ev.target;
      if (!t || !t.closest) return;
      const row = t.closest("tr.manual-scan-row");
      if (!row) return;
      activateManualScanRow(row);
    });
    manualSessionList.addEventListener("keydown", function (ev) {
      const t = ev.target;
      if (!t || !t.closest) return;
      const row = t.closest("tr.manual-scan-row");
      if (!row) return;
      onScanRowKeydown(ev, {
        row: row,
        rows: function () {
          return Array.prototype.slice.call(
            manualSessionList.querySelectorAll(".manual-scan-row")
          );
        },
        activate: activateManualScanRow,
      });
    });
  }
  if (manualStart) {
    manualStart.addEventListener("click", function () {
      startManualSession();
    });
  }
  if (manualProposeBug) {
    manualProposeBug.addEventListener("click", function () {
      proposeManual("create_bug");
    });
  }
  if (manualProposeComment) {
    manualProposeComment.addEventListener("click", function () {
      proposeManual("comment_on_story");
    });
  }
  if (manualProposeNote) {
    manualProposeNote.addEventListener("click", function () {
      proposeManual("attach_local_case_note");
    });
  }
  if (manualProposeSteps) {
    manualProposeSteps.addEventListener("click", function () {
      proposeManual("test_step_update_preview");
    });
  }
  if (manualConfirmYes) {
    manualConfirmYes.addEventListener("click", function () {
      confirmManualProposal(true);
    });
  }
  if (manualConfirmNo) {
    manualConfirmNo.addEventListener("click", function () {
      confirmManualProposal(false);
    });
  }
  if (charterNoteAdd) {
    charterNoteAdd.addEventListener("click", function () {
      addCharterNoteFromDock();
    });
  }
  if (charterNoteInput) {
    charterNoteInput.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        addCharterNoteFromDock();
      }
    });
  }
  if (charterStillAdd) {
    charterStillAdd.addEventListener("click", async function () {
      if (!manualOpenSessionId) return;
      try {
        const res = await fetch(
          "/api/manual-sessions/" +
            encodeURIComponent(manualOpenSessionId) +
            "/stills",
          { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }
        );
        const data = await res.json();
        if (data.status === "ok" && data.session) {
          if (data.still && data.still.id) manualLastStillId = data.still.id;
          updateCharterFrameChip(data.session);
        } else if (charterFrameChip) {
          charterFrameChip.textContent = data.message || "Still failed";
        }
      } catch (_err) {
        if (charterFrameChip) charterFrameChip.textContent = "Still failed";
      }
    });
  }
  if (charterAnnotateStill) {
    charterAnnotateStill.addEventListener("click", async function () {
      if (!manualOpenSessionId) return;
      const text = charterNoteInput ? charterNoteInput.value.trim() : "";
      if (!text) {
        if (charterFrameChip) {
          charterFrameChip.textContent = "Type annotation text, then Annotate";
        }
        return;
      }
      let stillId = manualLastStillId;
      if (!stillId) {
        if (charterFrameChip) {
          charterFrameChip.textContent = "Capture a Still first, then Annotate";
        }
        return;
      }
      try {
        const res = await fetch(
          "/api/manual-sessions/" +
            encodeURIComponent(manualOpenSessionId) +
            "/stills/" +
            encodeURIComponent(stillId) +
            "/annotate",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ annotation: text }),
          }
        );
        const data = await res.json();
        if (data.status === "ok" && data.session) {
          if (charterNoteInput) charterNoteInput.value = "";
          updateCharterFrameChip(data.session);
          if (charterFrameChip) {
            charterFrameChip.textContent =
              (charterFrameChip.textContent || "") + " · annotated";
          }
        } else if (charterFrameChip) {
          charterFrameChip.textContent = data.message || "Annotate failed";
        }
      } catch (_err) {
        if (charterFrameChip) charterFrameChip.textContent = "Annotate failed";
      }
    });
  }
  if (charterPageRefresh) {
    charterPageRefresh.addEventListener("click", async function () {
      if (!manualOpenSessionId) return;
      try {
        const res = await fetch(
          "/api/manual-sessions/" +
            encodeURIComponent(manualOpenSessionId) +
            "/page-context/refresh",
          { method: "POST" }
        );
        const data = await res.json();
        if (data.status === "ok" && data.session) {
          updateCharterFrameChip(data.session);
        } else if (charterFrameChip) {
          charterFrameChip.textContent = data.message || "Page refresh failed";
        }
      } catch (_err) {
        if (charterFrameChip) charterFrameChip.textContent = "Page refresh failed";
      }
    });
  }
  if (charterSnapMonitor) {
    charterSnapMonitor.addEventListener("click", function () {
      openCharterSnapPicker("monitor");
    });
  }
  if (charterSnapWindow) {
    charterSnapWindow.addEventListener("click", function () {
      openCharterSnapPicker("window");
    });
  }
  if (charterSnapPickerCancel) {
    charterSnapPickerCancel.addEventListener("click", function () {
      hideCharterSnapPicker();
    });
  }
  if (charterSnapPickerList) {
    charterSnapPickerList.addEventListener("click", function (ev) {
      const btn = ev.target && ev.target.closest
        ? ev.target.closest(".charter-snap-option")
        : null;
      if (!btn) return;
      applyCharterSnap(btn.dataset.targetId || "");
    });
  }
  if (charterEnd) {
    charterEnd.addEventListener("click", function () {
      endManualSessionFromFrame();
    });
  }
  if (charterCancel) {
    charterCancel.addEventListener("click", function () {
      requestCancelManualSession();
    });
  }
  if (charterCancelYes) {
    charterCancelYes.addEventListener("click", function () {
      cancelManualSessionFromFrame();
    });
  }
  if (charterCancelNo) {
    charterCancelNo.addEventListener("click", function () {
      showCharterCancelConfirm(false);
    });
  }
  if (charterAssistLive) {
    charterAssistLive.addEventListener("change", async function () {
      if (!manualOpenSessionId) return;
      await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(manualOpenSessionId) +
          "/toggles",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_assist: !!charterAssistLive.checked }),
        }
      );
    });
  }
  if (charterMistLive) {
    charterMistLive.addEventListener("change", async function () {
      if (!manualOpenSessionId) return;
      setCharterMistVisible(!!charterMistLive.checked);
      await fetch(
        "/api/manual-sessions/" +
          encodeURIComponent(manualOpenSessionId) +
          "/toggles",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ armed_mist: !!charterMistLive.checked }),
        }
      );
    });
  }
  if (charterFrameRoot) {
    charterFrameRoot.addEventListener("pointerdown", onCharterPointerDown);
    window.addEventListener("pointermove", onCharterPointerMove);
    window.addEventListener("pointerup", onCharterPointerUp);
  }
  refreshManualSessions();

  if (planRerunFailed) {
    planRerunFailed.addEventListener("click", async function () {
      if (!openPlanId) {
        if (planStatus) planStatus.textContent = "Open a plan first.";
        return;
      }
      const parallel = selectedParallelCount();
      if (planStatus) {
        planStatus.textContent =
          parallel <= 1
            ? "Rerunning failed cases (sequential)…"
            : "Rerunning failed cases (parallel=" + parallel + ")…";
      }
      if (planRerunOut) {
        planRerunOut.hidden = false;
        planRerunOut.textContent = "Rerunning…";
      }
      try {
        const res = await fetch(
          "/api/plans/" + encodeURIComponent(openPlanId) + "/rerun-failed",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              source_suite_run_id: lastSuiteRunId || "",
              parallel: parallel,
              sandbox_id: selectedSandboxId(),
            }),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) {
            planStatus.textContent = payload.message || "Rerun failed.";
          }
          if (planRerunOut) {
            planRerunOut.textContent = payload.message || "Rerun failed.";
          }
          return;
        }
        if (payload.suite_run_id) lastSuiteRunId = payload.suite_run_id;
        if (payload.plan) renderPlanCases(payload.plan);
        showLocalRunNotice(payload.local_notice);
        const skipped = payload.skipped || [];
        const results = payload.case_results || [];
        const lines = [
          payload.message || "Rerun finished.",
          "Suite run: " + (payload.suite_run_id || "—"),
          payload.source_suite_run_id
            ? "Source suite run: " + payload.source_suite_run_id
            : "Source: last failed case results",
          "Parallel count: " + (payload.parallel_count != null ? payload.parallel_count : parallel),
          "Sequential: " + (payload.sequential ? "yes" : "no"),
          payload.pass != null
            ? "Pass/fail: " + payload.pass + " / " + (payload.fail != null ? payload.fail : 0)
            : null,
          "",
          "Executed:",
          results.length
            ? results
                .map(function (r) {
                  return (
                    "- " +
                    (r.case_id || "?") +
                    " → " +
                    (r.result || r.status || "?")
                  );
                })
                .join("\n")
            : "(none)",
          "",
          "Skipped:",
          skipped.length
            ? skipped
                .map(function (s) {
                  return "- " + (s.case_id || "?") + " — " + (s.reason || "");
                })
                .join("\n")
            : "(none)",
        ].filter(function (line) {
          return line !== null;
        });
        if (planRerunOut) {
          planRerunOut.hidden = false;
          planRerunOut.textContent = lines.join("\n");
        }
        if (planStatus) {
          planStatus.textContent =
            (payload.message || "Rerun finished.") +
            (skipped.length
              ? " Skipped: " +
                skipped
                  .map(function (s) {
                    return (s.case_id || "?") + " (" + (s.reason || "") + ")";
                  })
                  .join(", ")
              : "");
        }
        await refreshCaseDetail();
      } catch (err) {
        if (planStatus) planStatus.textContent = "Rerun request failed.";
        if (planRerunOut) {
          planRerunOut.hidden = false;
          planRerunOut.textContent = "Rerun request failed.";
        }
      }
    });
  }

  async function postPauseDecision(kind) {
    if (!activePauseId) {
      if (planStatus) planStatus.textContent = "No active pause.";
      return;
    }
    if (planStatus) {
      planStatus.textContent =
        kind === "continue" ? "Continuing after pause…" : "Stopping — recording fail…";
    }
    try {
      const res = await fetch(
        "/api/plans/pause/" + encodeURIComponent(activePauseId) + "/" + kind,
        { method: "POST" }
      );
      const payload = await res.json();
      if (
        payload.status !== "ok" &&
        payload.status !== "paused" &&
        payload.pause_state !== "paused"
      ) {
        if (planStatus) {
          planStatus.textContent = payload.message || "Pause action failed.";
        }
        return;
      }
      applyPlanRunPayload(payload);
      if (payload.pause_state !== "paused" && payload.status !== "paused") {
        await refreshCaseDetail();
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Pause action request failed.";
    }
  }

  if (planPauseContinue) {
    planPauseContinue.addEventListener("click", function () {
      postPauseDecision("continue");
    });
  }
  if (planPauseStop) {
    planPauseStop.addEventListener("click", function () {
      postPauseDecision("stop");
    });
  }

  if (planRunFailureSave) {
    planRunFailureSave.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim() || !lastCaseRunId) {
        if (planStatus) planStatus.textContent = "Run a case first.";
        return;
      }
      try {
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()) +
            "/runs/" +
            encodeURIComponent(lastCaseRunId) +
            "/failure-class",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              failure_class: planRunFailureClass ? planRunFailureClass.value : "",
            }),
          }
        );
        const payload = await res.json();
        if (payload.status !== "ok") {
          if (planStatus) planStatus.textContent = payload.message || "Could not save class.";
          return;
        }
        if (payload.plan) renderPlanCases(payload.plan);
        if (planStatus) {
          planStatus.textContent =
            "Failure class saved." +
            (payload.create_bug_allowed
              ? " Product bug — create-bug path allowed."
              : " Jira create-bug stays blocked for this class.");
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Failure class save failed.";
      }
    });
  }

  if (planTriageOpenHeal) {
    planTriageOpenHeal.addEventListener("click", function () {
      openArea("heal");
    });
  }
  if (planTriageOpenReports) {
    planTriageOpenReports.addEventListener("click", function () {
      openArea("reports");
    });
  }

  async function postKnownIssue(clear) {
    if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
      if (planStatus) planStatus.textContent = "Enter a case id.";
      return;
    }
    try {
      const res = await fetch(
        "/api/plans/" +
          encodeURIComponent(openPlanId) +
          "/cases/" +
          encodeURIComponent(planCaseId.value.trim()) +
          "/known-issue",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            note: planKnownNote ? planKnownNote.value : "",
            jira_key: planKnownJira ? planKnownJira.value : "",
            run_id: lastCaseRunId || "",
            clear: !!clear,
          }),
        }
      );
      const payload = await res.json();
      if (payload.status !== "ok") {
        if (planStatus) planStatus.textContent = payload.message || "Could not save known issue.";
        return;
      }
      if (payload.plan) renderPlanCases(payload.plan);
      await refreshCaseDetail();
      if (planStatus) {
        planStatus.textContent =
          payload.message ||
          (clear ? "Known issue cleared." : "Known issue linked (labelled known).");
      }
    } catch (err) {
      if (planStatus) planStatus.textContent = "Known issue save failed.";
    }
  }

  if (planKnownSave) {
    planKnownSave.addEventListener("click", function () {
      postKnownIssue(false);
    });
  }
  if (planKnownClear) {
    planKnownClear.addEventListener("click", function () {
      postKnownIssue(true);
    });
  }

  if (planDefectPreview) {
    planDefectPreview.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Enter a case id.";
        return;
      }
      if (planDefectOut) {
        planDefectOut.hidden = false;
        planDefectOut.textContent = "Building preview…";
      }
      try {
        const qs = lastCaseRunId ? "?run_id=" + encodeURIComponent(lastCaseRunId) : "";
        const res = await fetch(
          "/api/plans/" +
            encodeURIComponent(openPlanId) +
            "/cases/" +
            encodeURIComponent(planCaseId.value.trim()) +
            "/defect-preview" +
            qs
        );
        const payload = await res.json();
        if (payload.status !== "ok" || !payload.packet) {
          if (planDefectOut) {
            planDefectOut.textContent = payload.message || "No preview.";
          }
          return;
        }
        const p = payload.packet;
        const lines = [
          payload.message || "",
          "",
          "Symptom: " + p.symptom,
          "Expected: " + p.expected,
          "Actual: " + p.actual,
          "",
          "Environment:",
          p.environment,
          "",
          "Replication:",
          (p.replication_steps || []).map(function (s, i) {
            return i + 1 + ". " + s;
          }).join("\n"),
          "",
          "Evidence:",
          (p.evidence_paths || []).join("\n") || "(none)",
        ];
        if (planDefectOut) planDefectOut.textContent = lines.join("\n");
      } catch (err) {
        if (planDefectOut) planDefectOut.textContent = "Preview request failed.";
      }
    });
  }

  if (connHealthBtn) {
    connHealthBtn.addEventListener("click", async function () {
      if (connHealthStatus) connHealthStatus.textContent = "Checking…";
      try {
        const res = await fetch("/api/connection-health");
        const payload = await res.json();
        applyConnectionHealth(payload);
      } catch (err) {
        if (connHealthStatus) {
          connHealthStatus.textContent =
            "Health check failed: " +
            (err && err.message ? err.message : err);
        }
      }
    });
  }

  if (credTestBtn) {
    credTestBtn.addEventListener("click", async function () {
      if (credStatus) credStatus.textContent = "Testing connection…";
      if (credTestOut) {
        credTestOut.hidden = false;
        credTestOut.textContent = "…";
      }
      try {
        const res = await fetch("/api/credentials/test-connection", {
          method: "POST",
        });
        const payload = await res.json();
        const check = payload.check || {};
        const line =
          (payload.result || check.state || "unknown") +
          " — " +
          (payload.message || check.message || "");
        if (credTestOut) {
          credTestOut.hidden = false;
          credTestOut.textContent = line;
        }
        if (credStatus) {
          credStatus.textContent =
            payload.message || "Test connection finished.";
        }
      } catch (err) {
        if (credStatus) credStatus.textContent = "Test connection failed.";
      }
    });
  }

  if (credSaveTargetBtn) {
    credSaveTargetBtn.addEventListener("click", async function () {
      const value = setTargetSecret ? setTargetSecret.value : "";
      if (credStatus) credStatus.textContent = "Saving target secret…";
      try {
        const res = await fetch("/api/credentials/target-secret", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ value: value, confirm: true }),
        });
        const payload = await res.json();
        applyCredentialStatus(payload);
        if (credStatus) {
          credStatus.textContent =
            payload.message ||
            (payload.status === "updated" ? "Target secret saved." : "Save failed.");
        }
        await loadAppSettings();
      } catch (err) {
        if (credStatus) credStatus.textContent = "Could not save target secret.";
      }
    });
  }

  [
    credClearEmailBtn,
    credClearTokenBtn,
    credClearTargetBtn,
  ].forEach(function (btn) {
    if (!btn) return;
    btn.addEventListener("click", function () {
      proposeClearSecret(btn.getAttribute("data-clear-key") || "");
    });
  });

  if (credClearConfirmBtn) {
    credClearConfirmBtn.addEventListener("click", function () {
      confirmClearSecret();
    });
  }

  function suitePathValue() {
    return suitePath && suitePath.value ? suitePath.value.trim() : "";
  }

  function recordSuiteLast(opts, payload, ok) {
    const file = (opts && opts.test_file) || "";
    const grep = (opts && opts.grep) || "";
    if (!file && !grep) return;
    const key = suiteRowKey(file, grep);
    if (!ok) {
      suiteLastByKey[key] =
        "Fail · " + (payload && (payload.error || payload.message)
          ? String(payload.error || payload.message).slice(0, 80)
          : "request failed");
      return;
    }
    const failed = Number((payload && payload.failed) || 0);
    const passed = Number((payload && payload.passed) || 0);
    if (payload && payload.status === "pass" && failed === 0) {
      suiteLastByKey[key] = "Pass · " + passed + " passed";
    } else {
      suiteLastByKey[key] =
        "Fail · " +
        failed +
        " failed, " +
        passed +
        " passed";
    }
    if (suiteScanBody) {
      suiteScanBody.querySelectorAll(".suite-scan-row").forEach(function (tr) {
        if (
          (tr.dataset.testFile || "") === file &&
          (tr.dataset.grep || "") === grep
        ) {
          const lastCell = tr.querySelector("td:last-child .suite-pill");
          if (lastCell) {
            const last = suiteLastByKey[key];
            if (/^Pass/i.test(last)) {
              lastCell.className = "suite-pill ok";
              lastCell.textContent = "Pass";
            } else {
              lastCell.className = "suite-pill warn";
              lastCell.textContent = "Fail";
            }
          }
          if (tr.classList.contains("is-focus") && suiteDetailLast) {
            suiteDetailLast.textContent = "Last result: " + suiteLastByKey[key];
            fillEvidenceFirst(evidenceFirstRoot("suite-evidence-first"), {
              force: true,
              summary: "Last result: " + suiteLastByKey[key],
              hasScreenshot: false,
            });
          }
        }
      });
    }
  }

  async function postSuiteRun(opts) {
    const body = {
      suite_path: suitePathValue(),
      timeout_s: 300,
      test_file: (opts && opts.test_file) || "",
      grep: (opts && opts.grep) || "",
    };
    const res = await fetch("/api/playwright-suite/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let payload = {};
    try {
      payload = await res.json();
    } catch (err) {
      payload = {};
    }
    if (!res.ok) {
      recordSuiteLast(opts, payload, false);
      if (suiteStatus) suiteStatus.textContent = "Suite run request failed.";
      return payload;
    }
    if (payload.status === "pass") {
      recordSuiteLast(opts, payload, true);
      if (suiteStatus) {
        suiteStatus.textContent =
          payload.message ||
          "Pass: " +
            (payload.passed || 0) +
            " passed, " +
            (payload.failed || 0) +
            " failed.";
      }
      return payload;
    }
    recordSuiteLast(opts, payload, true);
    if (suiteStatus) {
      suiteStatus.textContent =
        payload.error || payload.message || "Suite run failed.";
    }
    return payload;
  }

  if (suiteDiscover) {
    suiteDiscover.addEventListener("click", async function () {
      if (suiteStatus) suiteStatus.textContent = "Discovering…";
      try {
        const res = await fetch("/api/playwright-suite/discover", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ suite_path: suitePathValue() }),
        });
        const payload = await res.json();
        if (!res.ok || payload.status !== "ok") {
          if (suiteStatus) {
            suiteStatus.textContent =
              payload.error || payload.message || "Discover failed.";
          }
          return;
        }
        const specs = Array.isArray(payload.specs) ? payload.specs : [];
        renderSuiteList(
          specs.map(function (s) {
            return { title: s, file: s, line: null };
          }),
          "discover"
        );
        if (suiteStatus) {
          suiteStatus.textContent =
            payload.message ||
            "OK — " + (payload.spec_count || specs.length || 0) + " spec file(s).";
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite discover API.";
      }
    });
  }

  if (suiteListBtn) {
    suiteListBtn.addEventListener("click", async function () {
      if (suiteStatus) suiteStatus.textContent = "Listing tests…";
      try {
        const res = await fetch("/api/playwright-suite/list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ suite_path: suitePathValue() }),
        });
        const payload = await res.json();
        if (!res.ok || payload.status !== "ok") {
          if (suiteStatus) {
            suiteStatus.textContent =
              payload.error || payload.message || "List failed.";
          }
          return;
        }
        renderSuiteList(payload.tests || [], payload.source || "list");
        if (suiteStatus) {
          suiteStatus.textContent =
            payload.message ||
            "Listed " + ((payload.tests && payload.tests.length) || 0) + " test(s).";
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite list API.";
      }
    });
  }

  if (suiteImport) {
    suiteImport.addEventListener("click", async function () {
      if (suiteStatus) suiteStatus.textContent = "Importing…";
      try {
        const res = await fetch("/api/playwright-suite/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ suite_path: suitePathValue(), confirm: true }),
        });
        const payload = await res.json();
        if (!res.ok || payload.status === "fail") {
          if (suiteStatus) {
            suiteStatus.textContent =
              payload.error || payload.message || "Import failed.";
          }
          return;
        }
        applyPlaywrightSuite(payload);
        if (!suiteSavedPath) suiteSavedPath = suitePathValue();
        if (suiteStatus) {
          suiteStatus.textContent =
            payload.message || ("Suite path saved. " + suiteReadyStatusText());
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite import API.";
      }
    });
  }

  if (suiteRun) {
    suiteRun.addEventListener("click", async function () {
      const checked = getSuiteCheckedRows();
      if (!checked.length) {
        if (suiteStatus) {
          suiteStatus.textContent =
            "Check one or more tests in the Sel column, or use Run all.";
        }
        return;
      }
      if (suiteStatus) {
        suiteStatus.textContent =
          "Running selected (" + checked.length + ")…";
      }
      try {
        for (let i = 0; i < checked.length; i += 1) {
          const row = checked[i];
          if (suiteStatus && checked.length > 1) {
            suiteStatus.textContent =
              "Running selected " + (i + 1) + "/" + checked.length + "…";
          }
          await postSuiteRun({
            test_file: row.test_file,
            grep: row.grep,
          });
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite run API.";
      }
    });
  }

  if (suiteRunFocused) {
    suiteRunFocused.addEventListener("click", async function () {
      if (!suiteSelected.test_file && !suiteSelected.grep) {
        if (suiteStatus) {
          suiteStatus.textContent = "Focus a row first, then Run this test.";
        }
        return;
      }
      if (suiteStatus) suiteStatus.textContent = "Running focused test…";
      try {
        await postSuiteRun({
          test_file: suiteSelected.test_file,
          grep: suiteSelected.grep,
        });
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite run API.";
      }
    });
  }

  if (suiteCopyPath) {
    suiteCopyPath.addEventListener("click", async function () {
      const path = suiteSelected.test_file || "";
      if (!path) return;
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(path);
          if (suiteStatus) suiteStatus.textContent = "Copied path.";
        } else if (suiteDetailFile) {
          suiteDetailFile.select();
          document.execCommand("copy");
          if (suiteStatus) suiteStatus.textContent = "Copied path.";
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not copy path.";
      }
    });
  }

  if (suiteRunAll) {
    suiteRunAll.addEventListener("click", async function () {
      if (suiteStatus) suiteStatus.textContent = "Running suite…";
      try {
        await postSuiteRun({ test_file: "", grep: "" });
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite run API.";
      }
    });
  }

  if (msSave) {
    msSave.addEventListener("click", async function () {
      if (msStatus) msStatus.textContent = "Saving…";
      try {
        const res = await fetch("/api/multi-sandbox-plugin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            plugin_multi_sandbox_enabled: !!(msEnabled && msEnabled.checked),
          }),
        });
        const payload = await res.json();
        if (!res.ok) {
          if (msStatus) msStatus.textContent = "Save failed.";
          return;
        }
        applyMultiSandboxPlugin(payload);
        await loadPluginRegistry();
        if (msStatus) {
          msStatus.textContent = payload.plugin_multi_sandbox_enabled
            ? "Multi-sandbox plugin enabled."
            : "Multi-sandbox plugin disabled.";
        }
      } catch (err) {
        if (msStatus) msStatus.textContent = "Could not reach multi-sandbox API.";
      }
    });
  }

  if (msRun) {
    msRun.addEventListener("click", async function () {
      if (msStatus) msStatus.textContent = "Orchestrating…";
      try {
        const action =
          msAction && msAction.value ? msAction.value.trim() : "list";
        const payload = await runMultiSandboxAction(action);
        if (payload.status === "disabled") {
          if (msStatus) {
            msStatus.textContent =
              payload.message ||
              payload.error ||
              "Plugin disabled — enable and Save.";
          }
          return;
        }
        if (payload.status === "ok") {
          const n = (payload.sandboxes || []).length;
          if (msStatus) {
            msStatus.textContent =
              (payload.message || "OK") + " (" + n + " sandbox(es))";
          }
          return;
        }
        if (msStatus) {
          msStatus.textContent =
            payload.error || payload.message || "Orchestration failed.";
        }
      } catch (err) {
        if (msStatus) msStatus.textContent = "Could not reach orchestrate API.";
      }
    });
  }

  if (msUpsert) {
    msUpsert.addEventListener("click", async function () {
      if (msStatus) msStatus.textContent = "Saving sandbox…";
      try {
        const payload = await runMultiSandboxAction("upsert");
        if (payload.status === "disabled") {
          if (msStatus) {
            msStatus.textContent =
              payload.message || "Plugin disabled — enable and Save.";
          }
          return;
        }
        if (payload.status === "ok") {
          if (msStatus) msStatus.textContent = payload.message || "Sandbox saved.";
          return;
        }
        if (msStatus) {
          msStatus.textContent =
            payload.error || payload.message || "Save sandbox failed.";
        }
      } catch (err) {
        if (msStatus) msStatus.textContent = "Could not reach orchestrate API.";
      }
    });
  }

  if (msRemove) {
    msRemove.addEventListener("click", function () {
      const sid = msId && msId.value ? msId.value.trim() : "";
      if (!sid) {
        if (msStatus) msStatus.textContent = "Select a sandbox (or enter id) before Remove.";
        resetMsRemoveConfirm();
        return;
      }
      if (msRemoveConfirm) {
        msRemoveConfirm.disabled = false;
      }
      if (msStatus) {
        msStatus.textContent =
          "Confirm remove enabled for “" + sid + "”. Row still listed until Confirm.";
      }
    });
  }

  if (msRemoveConfirm) {
    msRemoveConfirm.addEventListener("click", async function () {
      if (msRemoveConfirm.disabled) return;
      if (msStatus) msStatus.textContent = "Removing sandbox…";
      try {
        const payload = await runMultiSandboxAction("remove");
        if (payload.status === "disabled") {
          if (msStatus) {
            msStatus.textContent =
              payload.message || "Plugin disabled — enable and Save.";
          }
          resetMsRemoveConfirm();
          return;
        }
        if (payload.status === "ok") {
          msFocusedId = "";
          if (msStatus) msStatus.textContent = payload.message || "Sandbox removed.";
          resetMsRemoveConfirm();
          return;
        }
        if (msStatus) {
          msStatus.textContent =
            payload.error || payload.message || "Remove failed.";
        }
        resetMsRemoveConfirm();
      } catch (err) {
        if (msStatus) msStatus.textContent = "Could not reach orchestrate API.";
        resetMsRemoveConfirm();
      }
    });
  }

  if (msId) {
    msId.addEventListener("input", function () {
      resetMsRemoveConfirm();
    });
  }

  if (deskEnabled) {
    deskEnabled.addEventListener("click", function (ev) {
      ev.stopPropagation();
    });
    deskEnabled.addEventListener("mousedown", function (ev) {
      ev.stopPropagation();
    });
  }

  if (deskScanRow) {
    deskScanRow.addEventListener("click", function (ev) {
      if (
        ev.target &&
        ev.target.closest &&
        ev.target.closest('[data-desk-checkbox-stop="1"]')
      ) {
        return;
      }
      focusDesktopDetail();
    });
    deskScanRow.addEventListener("keydown", function (ev) {
      onScanRowKeydown(ev, {
        row: deskScanRow,
        checkboxStop: '[data-desk-checkbox-stop="1"]',
        rows: function () {
          return [deskScanRow];
        },
        activate: function () {
          focusDesktopDetail();
        },
      });
    });
  }

  if (deskSave) {
    deskSave.addEventListener("click", async function () {
      if (deskStatus) deskStatus.textContent = "Saving…";
      try {
        const res = await fetch("/api/desktop-plugin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            plugin_desktop_enabled: !!(deskEnabled && deskEnabled.checked),
          }),
        });
        const payload = await res.json();
        if (!res.ok) {
          if (deskStatus) deskStatus.textContent = "Save failed.";
          return;
        }
        applyDesktopPlugin(payload);
        if (deskStatus) {
          deskStatus.textContent = payload.plugin_desktop_enabled
            ? "Desktop plugin enabled."
            : "Desktop plugin disabled.";
        }
      } catch (err) {
        if (deskStatus) deskStatus.textContent = "Could not reach desktop plugin API.";
      }
    });
  }

  function summarizeDesktopRun(payload, label) {
    if (payload.status === "disabled") {
      return payload.message || payload.error || "Plugin disabled — enable and Save.";
    }
    if (payload.status === "pass") {
      const n = Array.isArray(payload.steps) ? payload.steps.length : 0;
      const stepBit = n ? " · " + n + " steps" : "";
      return (
        "Pass (" +
        label +
        "): " +
        (payload.exe_path || "app") +
        " (pid " +
        (payload.pid || "—") +
        ")" +
        stepBit
      );
    }
    return payload.error || payload.message || label + " failed.";
  }

  function recordDeskLastSmoke(payload, label) {
    const summary = summarizeDesktopRun(payload, label);
    if (payload.status === "pass") {
      deskLastSmokeText = "Pass · " + label;
      setDeskScanStatus("Ready", "ok");
    } else if (payload.status === "disabled") {
      deskLastSmokeText = "Disabled";
      setDeskScanStatus("Disabled", "warn");
    } else {
      deskLastSmokeText = "Fail · " + label;
      setDeskScanStatus("Fail", "warn");
    }
    if (deskLastSmoke) deskLastSmoke.textContent = deskLastSmokeText;
    fillEvidenceFirst(evidenceFirstRoot("desk-evidence-first"), {
      force: true,
      summary: deskLastSmokeText || "—",
      hasScreenshot: false,
    });
    return summary;
  }

  if (deskSmoke) {
    deskSmoke.addEventListener("click", async function () {
      if (deskStatus) deskStatus.textContent = "Running smoke…";
      try {
        const override = deskExe && deskExe.value ? deskExe.value.trim() : "";
        const res = await fetch("/api/desktop-smoke", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ exe_path: override, timeout_s: 1.5 }),
        });
        const payload = await res.json();
        if (!res.ok) {
          if (deskStatus) deskStatus.textContent = "Smoke request failed.";
          return;
        }
        if (deskStatus) deskStatus.textContent = recordDeskLastSmoke(payload, "smoke");
      } catch (err) {
        if (deskStatus) deskStatus.textContent = "Could not reach desktop smoke API.";
      }
    });
  }

  if (deskSteps) {
    deskSteps.addEventListener("click", async function () {
      if (deskStatus) deskStatus.textContent = "Running demo steps…";
      try {
        const override = deskExe && deskExe.value ? deskExe.value.trim() : "";
        const res = await fetch("/api/desktop-smoke", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            exe_path: override,
            timeout_s: 8,
            demo: true,
          }),
        });
        const payload = await res.json();
        if (!res.ok) {
          if (deskStatus) deskStatus.textContent = "Steps request failed.";
          return;
        }
        if (deskStatus) deskStatus.textContent = recordDeskLastSmoke(payload, "steps");
      } catch (err) {
        if (deskStatus) deskStatus.textContent = "Could not reach desktop steps API.";
      }
    });
  }

  if (secPropose) {
    secPropose.addEventListener("click", async function () {
      const level = secLevel ? secLevel.value : "";
      if (!level) return;
      if (secStatus) secStatus.textContent = "Proposing switch…";
      try {
        const { ok, payload } = await postSecurityLevel(level, false);
        if (!ok) {
          if (secStatus) secStatus.textContent = "Switch request failed.";
          return;
        }
        if (payload.status === "unchanged") {
          applySecurityStatus(payload);
          pendingSecurityLevel = "";
          if (secConfirm) secConfirm.disabled = true;
          if (secStatus) secStatus.textContent = "Already on " + level + ".";
          return;
        }
        if (payload.status === "confirmation_required") {
          pendingSecurityLevel = (payload.proposed && payload.proposed.security_level) || level;
          if (secConfirm) secConfirm.disabled = false;
          if (secProfile && payload.browser_profile) {
            secProfile.textContent =
              "Proposed browser profile: " + payload.browser_profile;
          }
          if (secStatus) {
            secStatus.textContent =
              payload.message || "Confirm to apply the security level switch.";
          }
          return;
        }
        applySecurityStatus(payload);
        if (secStatus) secStatus.textContent = "Updated.";
      } catch (err) {
        if (secStatus) secStatus.textContent = "Could not reach security API.";
      }
    });
  }

  if (secConfirm) {
    secConfirm.addEventListener("click", async function () {
      const level = pendingSecurityLevel || (secLevel ? secLevel.value : "");
      if (!level) return;
      if (secStatus) secStatus.textContent = "Confirming switch…";
      try {
        const { ok, payload } = await postSecurityLevel(level, true);
        if (!ok || payload.status === "error") {
          if (secStatus) {
            secStatus.textContent = (payload && payload.message) || "Confirm failed.";
          }
          return;
        }
        applySecurityStatus(payload);
        pendingSecurityLevel = "";
        if (secConfirm) secConfirm.disabled = true;
        clearManualUiForLevelSwitch();
        refreshManualSessions();
        if (secStatus) {
          secStatus.textContent =
            "Switched to " + (payload.security_level || level) + ".";
        }
      } catch (err) {
        if (secStatus) secStatus.textContent = "Could not confirm switch.";
      }
    });
  }

  if (privPropose) {
    privPropose.addEventListener("click", async function () {
      const categories = selectedPrivacyCategories();
      if (!categories.length) {
        if (privStatus) privStatus.textContent = "Select at least one category.";
        return;
      }
      if (privStatus) privStatus.textContent = "Proposing delete…";
      try {
        const { ok, payload } = await postPrivacyDelete(categories, false);
        if (!ok) {
          if (privStatus) privStatus.textContent = "Delete request failed.";
          return;
        }
        if (payload.status === "confirmation_required") {
          pendingPrivacyCategories =
            (payload.proposed && payload.proposed.categories) || categories;
          if (privConfirm) privConfirm.disabled = false;
          if (payload.inventory) {
            applyPrivacyStatus({
              telemetry_enabled: false,
              categories: payload.inventory,
            });
          }
          if (privStatus) {
            privStatus.textContent =
              payload.message ||
              "Confirm to permanently delete: " +
                (pendingPrivacyCategories || []).join(", ");
          }
          return;
        }
        if (privStatus) {
          privStatus.textContent = payload.message || payload.status || "Done.";
        }
      } catch (err) {
        if (privStatus) privStatus.textContent = "Could not reach privacy API.";
      }
    });
  }

  if (privConfirm) {
    privConfirm.addEventListener("click", async function () {
      const categories = pendingPrivacyCategories || selectedPrivacyCategories();
      if (!categories || !categories.length) {
        if (privStatus) privStatus.textContent = "Nothing pending to delete.";
        return;
      }
      if (privStatus) privStatus.textContent = "Deleting…";
      try {
        const { ok, payload } = await postPrivacyDelete(categories, true);
        if (!ok || payload.status === "error") {
          if (privStatus) {
            privStatus.textContent =
              (payload && payload.message) || "Delete failed.";
          }
          return;
        }
        pendingPrivacyCategories = null;
        if (privConfirm) privConfirm.disabled = true;
        if (payload.inventory_after) {
          applyPrivacyStatus({
            telemetry_enabled: false,
            categories: payload.inventory_after,
          });
        } else {
          await loadPrivacyStatus();
        }
        if (privStatus) {
          privStatus.textContent =
            payload.message || "Local artifacts deleted.";
        }
        await loadLocalAudit();
      } catch (err) {
        if (privStatus) privStatus.textContent = "Could not confirm delete.";
      }
    });
  }

  if (localAuditRefresh) {
    localAuditRefresh.addEventListener("click", function () {
      loadLocalAudit();
    });
  }

  if (backupRefresh) {
    backupRefresh.addEventListener("click", function () {
      if (backupStatus) backupStatus.textContent = "Refreshing…";
      loadBackupStatus().then(function () {
        if (backupStatus) backupStatus.textContent = "Ready";
      });
    });
  }

  if (backupCreate) {
    backupCreate.addEventListener("click", async function () {
      if (backupStatus) backupStatus.textContent = "Creating backup…";
      try {
        const res = await fetch("/api/backup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            include_settings: !!(backupIncludeSettings && backupIncludeSettings.checked),
            include_secrets: !!(backupIncludeSecrets && backupIncludeSecrets.checked),
          }),
        });
        const payload = await res.json();
        if (!res.ok || payload.status === "error") {
          if (backupStatus) {
            backupStatus.textContent =
              (payload && payload.message) || "Backup failed.";
          }
          return;
        }
        if (backupStatus) {
          backupStatus.textContent = payload.message || "Backup created.";
        }
        await loadBackupStatus();
        if (payload.path && backupSelect) {
          backupSelect.value = payload.path;
        }
      } catch (err) {
        if (backupStatus) backupStatus.textContent = "Could not create backup.";
      }
    });
  }

  if (backupRestorePropose) {
    backupRestorePropose.addEventListener("click", async function () {
      const path = (backupSelect && backupSelect.value) || "";
      if (!path) {
        if (backupStatus) backupStatus.textContent = "Select a backup first.";
        return;
      }
      if (backupStatus) backupStatus.textContent = "Proposing restore…";
      try {
        const res = await fetch("/api/backup/restore", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: path, confirm: false }),
        });
        const payload = await res.json();
        if (payload.status === "confirmation_required") {
          pendingBackupPath = path;
          if (backupRestoreConfirm) backupRestoreConfirm.disabled = false;
          const prev = payload.preview || {};
          if (backupStatus) {
            backupStatus.textContent =
              (payload.message || "Confirm restore?") +
              " Plans in backup: " +
              (prev.plans_in_backup || 0) +
              "; evidence indexes: " +
              (prev.evidence_indexes_in_backup || 0) +
              ".";
          }
          return;
        }
        if (backupStatus) {
          backupStatus.textContent =
            (payload && payload.message) || payload.status || "Restore blocked.";
        }
        pendingBackupPath = "";
        if (backupRestoreConfirm) backupRestoreConfirm.disabled = true;
      } catch (err) {
        if (backupStatus) backupStatus.textContent = "Could not propose restore.";
      }
    });
  }

  if (backupRestoreConfirm) {
    backupRestoreConfirm.addEventListener("click", async function () {
      const path =
        pendingBackupPath || (backupSelect && backupSelect.value) || "";
      if (!path) {
        if (backupStatus) backupStatus.textContent = "Nothing pending to restore.";
        return;
      }
      if (backupStatus) backupStatus.textContent = "Restoring…";
      try {
        const res = await fetch("/api/backup/restore", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: path, confirm: true }),
        });
        const payload = await res.json();
        if (!res.ok || payload.status === "error") {
          if (backupStatus) {
            backupStatus.textContent =
              (payload && payload.message) || "Restore failed.";
          }
          return;
        }
        pendingBackupPath = "";
        if (backupRestoreConfirm) backupRestoreConfirm.disabled = true;
        if (backupStatus) {
          backupStatus.textContent = payload.message || "Restored.";
        }
        await loadBackupStatus();
        await loadPrivacyStatus();
      } catch (err) {
        if (backupStatus) backupStatus.textContent = "Could not confirm restore.";
      }
    });
  }

  function renderDocProposal(payload) {
    docProposalId = payload.proposal_id || "";
    showDocPanel("propose");
    const diff = payload.settings_diff || {};
    const keys = Object.keys(diff);
    if (docDiff) {
      docDiff.innerHTML = "";
      keys.forEach(function (key) {
        const entry = diff[key] || {};
        const tr = document.createElement("tr");
        tr.className = "doc-scan-row";
        tr.setAttribute("data-key", key);
        tr.tabIndex = 0;

        const tdKeep = document.createElement("td");
        tdKeep.className = "doc-hit";
        tdKeep.setAttribute("data-doc-keep-cell", "1");
        const box = document.createElement("input");
        box.type = "checkbox";
        box.checked = true;
        box.dataset.key = key;
        box.setAttribute("aria-label", "Keep " + key);
        box.setAttribute("data-doc-keep-stop", "1");
        box.addEventListener("click", function (ev) {
          ev.stopPropagation();
        });
        box.addEventListener("mousedown", function (ev) {
          ev.stopPropagation();
        });
        tdKeep.appendChild(box);

        const tdKey = document.createElement("td");
        tdKey.textContent = key;
        const tdFrom = document.createElement("td");
        tdFrom.textContent = entry.from || "(empty)";
        const tdTo = document.createElement("td");
        tdTo.textContent = entry.to || "";

        tr.appendChild(tdKeep);
        tr.appendChild(tdKey);
        tr.appendChild(tdFrom);
        tr.appendChild(tdTo);
        tr.addEventListener("click", function (ev) {
          if (
            ev.target &&
            ev.target.closest &&
            ev.target.closest('[data-doc-keep-stop="1"]')
          ) {
            return;
          }
          focusDocDiffKey(key, entry);
        });
        tr.addEventListener("keydown", function (ev) {
          onScanRowKeydown(ev, {
            row: tr,
            checkboxStop: '[data-doc-keep-stop="1"]',
            rows: function () {
              return Array.prototype.slice.call(
                docDiff.querySelectorAll(".doc-scan-row")
              );
            },
            activate: function (rowEl) {
              const k = rowEl.getAttribute("data-key") || "";
              focusDocDiffKey(k, diff[k] || {});
            },
          });
        });
        docDiff.appendChild(tr);
      });
      if (keys.length) {
        const firstKey = keys[0];
        focusDocDiffKey(firstKey, diff[firstKey] || {});
      } else {
        focusDocDiffKey("", null);
      }
    }
    if (docIdeas) {
      docIdeas.innerHTML = "";
      const ideas = payload.test_ideas || [];
      if (!ideas.length) {
        const li = document.createElement("li");
        li.textContent = "None extracted.";
        docIdeas.appendChild(li);
      } else {
        ideas.forEach(function (idea) {
          const li = document.createElement("li");
          li.textContent = idea;
          docIdeas.appendChild(li);
        });
      }
    }
    if (docProposal) {
      docProposal.hidden = !(keys.length || (payload.test_ideas && payload.test_ideas.length));
    }
  }

  if (docParse) {
    docParse.addEventListener("click", async function () {
      const text = (docText && docText.value) || "";
      if (!text.trim()) {
        if (docStatus) docStatus.textContent = "Paste a Markdown or text spec first.";
        return;
      }
      if (docStatus) docStatus.textContent = "Parsing…";
      try {
        const res = await fetch("/api/doc-ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: text,
            filename: "paste.md",
            session_id: "desktop",
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error("parse failed");
        if (data.status === "error" || data.status === "empty") {
          if (docProposal) docProposal.hidden = true;
          if (docStatus) docStatus.textContent = data.message || "Nothing to propose.";
          return;
        }
        renderDocProposal(data);
        if (docStatus) {
          const uploadBit = data.upload
            ? " Upload recorded (" +
              (data.upload.filename || "file") +
              ", consent " +
              (data.upload.consent ? "yes" : "no") +
              ")."
            : "";
          docStatus.textContent =
            (data.note ||
              (data.status === "ideas_only"
                ? "Test ideas only — settings unchanged."
                : "Review the diff, then Confirm or Decline.")) + uploadBit;
        }
        loadDocUploads();
      } catch (err) {
        if (docStatus) docStatus.textContent = "Could not parse the document.";
      }
    });
  }

  if (docUploadsRefresh) {
    docUploadsRefresh.addEventListener("click", function () {
      loadDocUploads();
    });
  }

  if (docConfirm) {
    docConfirm.addEventListener("click", async function () {
      if (!docProposalId) {
        if (docStatus) docStatus.textContent = "Parse a document first.";
        return;
      }
      const keys = [];
      if (docDiff) {
        docDiff.querySelectorAll("input[type=checkbox][data-key]").forEach(function (box) {
          if (box.checked) keys.push(box.dataset.key);
        });
      }
      if (!keys.length) {
        if (docStatus) docStatus.textContent = "Select at least one proposed key, or Decline.";
        return;
      }
      try {
        const res = await fetch("/api/doc-ingest/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            proposal_id: docProposalId,
            keys: keys,
            confirm: true,
            session_id: "desktop",
          }),
        });
        const data = await res.json();
        if (data.status !== "applied") {
          if (docStatus) docStatus.textContent = data.message || "Could not apply.";
          return;
        }
        docProposalId = "";
        if (docProposal) docProposal.hidden = true;
        if (docDiff) docDiff.innerHTML = "";
        focusDocDiffKey("", null);
        if (docStatus) {
          const updated = Object.keys(data.updated || {});
          docStatus.textContent =
            "Stored: " +
            (updated.length ? updated.join(", ") : "nothing") +
            (data.consent ? " · upload consent yes." : ".");
        }
        loadDocUploads();
      } catch (err) {
        if (docStatus) docStatus.textContent = "Could not apply settings.";
      }
    });
  }

  if (docDecline) {
    docDecline.addEventListener("click", async function () {
      if (!docProposalId) {
        if (docStatus) docStatus.textContent = "Nothing to decline.";
        return;
      }
      try {
        await fetch("/api/doc-ingest/decline", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            proposal_id: docProposalId,
            session_id: "desktop",
          }),
        });
        docProposalId = "";
        if (docProposal) docProposal.hidden = true;
        if (docDiff) docDiff.innerHTML = "";
        focusDocDiffKey("", null);
        if (docStatus) docStatus.textContent = "Declined. Settings file unchanged.";
      } catch (err) {
        if (docStatus) docStatus.textContent = "Could not decline proposal.";
      }
    });
  }

  if (healRefresh) {
    healRefresh.addEventListener("click", function () {
      loadHealProposals();
    });
  }
  if (healApproveBtn) {
    healApproveBtn.addEventListener("click", function () {
      approveFocusedHeal();
    });
  }
  if (healRejectBtn) {
    healRejectBtn.addEventListener("click", function () {
      rejectFocusedHeal();
    });
  }
  if (healBulkApprove) {
    healBulkApprove.addEventListener("click", function () {
      bulkApproveSelectedHeals();
    });
  }

  if (rptRunRefresh) {
    rptRunRefresh.addEventListener("click", function () {
      loadExportableRuns();
      if (rptStatus) rptStatus.textContent = "Run list refreshed.";
    });
  }
  if (rptExportRun) {
    rptExportRun.addEventListener("click", function () {
      exportChosenRun();
    });
  }
  if (rptExportPack) {
    rptExportPack.addEventListener("click", function () {
      exportChosenPack();
    });
  }
  if (healRunFilter) {
    healRunFilter.addEventListener("change", function () {
      loadHealProposals();
    });
  }
  if (rptSave) {
    rptSave.addEventListener("click", async function () {
      const body = reportSectionBody();
      try {
        const res = await fetch("/api/report-sections", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error("save failed");
        const saved = await res.json();
        applyReportSections(saved);
        const enabled = Object.keys(saved).filter(function (k) {
          return saved[k];
        });
        const msg =
          "Saved. Next export includes: " +
          (enabled.length ? enabled.join(", ") : "(none)") +
          ".";
        if (rptSectionsStatus) rptSectionsStatus.textContent = msg;
      } catch (err) {
        if (rptSectionsStatus) rptSectionsStatus.textContent = "Could not save section profile.";
      }
    });
  }
  if (rptLibraryRefresh) {
    rptLibraryRefresh.addEventListener("click", function () {
      loadReportLibrary();
    });
  }
  if (rptOpenSettings) {
    rptOpenSettings.addEventListener("click", function () {
      openReportSettings();
    });
  }
  const settingsSectionRail = document.getElementById("settings-section-rail");
  if (settingsSectionRail) {
    settingsSectionRail.addEventListener("click", function (ev) {
      const btn =
        ev.target && ev.target.closest
          ? ev.target.closest(".settings-section-btn[data-settings-section]")
          : null;
      if (!btn || !settingsSectionRail.contains(btn)) return;
      ev.preventDefault();
      setSettingsSection(btn.getAttribute("data-settings-section"));
    });
  }
  const secSectionRail = document.getElementById("sec-section-rail");
  if (secSectionRail) {
    secSectionRail.addEventListener("click", function (ev) {
      const btn =
        ev.target && ev.target.closest
          ? ev.target.closest(".sec-section-btn[data-sec-section]")
          : null;
      if (!btn || !secSectionRail.contains(btn)) return;
      ev.preventDefault();
      setSecuritySection(btn.getAttribute("data-sec-section"));
    });
  }
  document.querySelectorAll("#sec-privacy-scan .sec-scan-row").forEach(function (row) {
    row.addEventListener("click", function (ev) {
      if (
        ev.target &&
        ev.target.closest &&
        ev.target.closest('[data-sec-checkbox-stop="1"]')
      ) {
        return;
      }
      focusPrivArtifact(row.getAttribute("data-priv-artifact") || "reports");
    });
    row.addEventListener("keydown", function (ev) {
      onScanRowKeydown(ev, {
        row: row,
        checkboxStop: '[data-sec-checkbox-stop="1"]',
        rows: function () {
          return Array.prototype.slice.call(
            document.querySelectorAll("#sec-privacy-scan .sec-scan-row")
          );
        },
        activate: function (rowEl) {
          focusPrivArtifact(rowEl.getAttribute("data-priv-artifact") || "reports");
        },
      });
    });
  });
  document.querySelectorAll('[data-sec-checkbox-stop="1"]').forEach(function (input) {
    input.addEventListener("click", function (ev) {
      ev.stopPropagation();
    });
    input.addEventListener("mousedown", function (ev) {
      ev.stopPropagation();
    });
  });
  setSecuritySection("privacy");
  focusPrivArtifact("reports");
  document.querySelectorAll("#set-rpt-scan .settings-scan-row").forEach(function (row) {
    row.addEventListener("click", function (ev) {
      if (ev.target && ev.target.closest && ev.target.closest('[data-settings-checkbox-stop="1"]')) {
        return;
      }
      focusReportBlock(row.getAttribute("data-report-block") || "summary");
    });
    row.addEventListener("keydown", function (ev) {
      onScanRowKeydown(ev, {
        row: row,
        checkboxStop: '[data-settings-checkbox-stop="1"]',
        rows: function () {
          return Array.prototype.slice.call(
            document.querySelectorAll("#set-rpt-scan .settings-scan-row")
          );
        },
        activate: function (rowEl) {
          focusReportBlock(rowEl.getAttribute("data-report-block") || "summary");
        },
      });
    });
  });
  document.querySelectorAll('[data-settings-checkbox-stop="1"]').forEach(function (input) {
    input.addEventListener("click", function (ev) {
      ev.stopPropagation();
    });
    input.addEventListener("change", function () {
      syncReportBlockPills();
    });
  });
  syncReportBlockPills();
  focusReportBlock("summary");

  window.addEventListener("resize", function () {
    restoreLayout();
  });

  async function boot() {
    const hadStyleStore = !!localStorage.getItem(ORB_STYLES_KEY);
    let activeStyle = loadStyleConfigs();
    try {
      const res = await fetch("/api/orb");
      if (res.ok) {
        const apiCfg = orbConfigFromApi(await res.json());
        if (apiCfg && WEBGL_STYLES.includes(apiCfg.style)) {
          activeStyle = apiCfg.style;
          if (!hadStyleStore) {
            styleConfigs[apiCfg.style] = Object.assign(
              defaultStyleConfig(apiCfg.style),
              apiCfg,
              { style: apiCfg.style }
            );
          }
        }
      }
    } catch (err) {
      /* use store defaults */
    }
    const cfg = styleConfigs[activeStyle] || defaultStyleConfig(activeStyle);
    applyControlsFromConfig(cfg);
    applyConfigToNode(cfg);
    saveStyleConfigs(activeStyle);
    restoreLayout();
    if (window.__orbWebGL && host) {
      window.__orbWebGL.attach(host);
    }
    loadReportSections();
  }

  boot();
})();
