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
    /* Compact ▦ panel beside the toggle — not a full-height side rail (KAN-253). */
    if (!appDrawer || !appToggle) return;
    const edge = appToggle.dataset.edge || "left";
    const tr = appToggle.getBoundingClientRect();
    const W = window.innerWidth;
    const H = window.innerHeight;
    const panelW = Math.min(280, W - 24);
    const gap = 8;
    clearPos(appDrawer);
    appDrawer.classList.remove("edge-left", "edge-right", "edge-top", "edge-bottom");
    appDrawer.classList.add("edge-" + edge);
    appDrawer.style.width = panelW + "px";
    appDrawer.style.maxHeight = Math.min(H - 48, 520) + "px";
    if (edge === "left") {
      appDrawer.style.left = clamp(tr.right + gap, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.top, 12, Math.max(12, H - 120)) + "px";
      return;
    }
    if (edge === "right") {
      appDrawer.style.left = clamp(tr.left - gap - panelW, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.top, 12, Math.max(12, H - 120)) + "px";
      return;
    }
    if (edge === "top") {
      appDrawer.style.left = clamp(tr.left, 12, Math.max(12, W - panelW - 12)) + "px";
      appDrawer.style.top = clamp(tr.bottom + gap, 12, Math.max(12, H - 120)) + "px";
      return;
    }
    appDrawer.style.left = clamp(tr.left, 12, Math.max(12, W - panelW - 12)) + "px";
    appDrawer.style.bottom = clamp(H - tr.top + gap, 12, Math.max(12, H - 120)) + "px";
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

  function restoreLayout() {
    [appToggle, screenToggle].forEach(function (el) {
      const saved = layout.toggles[el.id];
      const edge = (saved && saved.edge) || el.getAttribute("data-default-edge") || "left";
      const along = saved && typeof saved.along === "number" ? saved.along : null;
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
  const sandboxesNav = appDrawer
    ? appDrawer.querySelector('.app-nav-item[data-section="sandboxes"]')
    : null;
  const healList = document.getElementById("heal-list");
  const healStatus = document.getElementById("heal-status");
  const healRefresh = document.getElementById("heal-refresh");
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
  const planRefreshBtn = document.getElementById("plan-refresh-btn");
  const planList = document.getElementById("plan-list");
  const planLoadBtn = document.getElementById("plan-load-btn");
  const planDocAddBtn = document.getElementById("plan-doc-add-btn");
  const planIntent = document.getElementById("plan-intent");
  const planCases = document.getElementById("plan-cases");
  const planCoverageFilter = document.getElementById("plan-coverage-filter");
  const planCoverageBtn = document.getElementById("plan-coverage-btn");
  const planCoverageNoCase = document.getElementById("plan-coverage-no-case");
  const planCoverageDisabled = document.getElementById("plan-coverage-disabled");
  const planDriftCheckBtn = document.getElementById("plan-drift-check-btn");
  const planDriftKeepBtn = document.getElementById("plan-drift-keep-btn");
  const planDriftRefreshBtn = document.getElementById("plan-drift-refresh-btn");
  const planDriftOut = document.getElementById("plan-drift-out");
  const planCaseId = document.getElementById("plan-case-id");
  const planCaseName = document.getElementById("plan-case-name");
  const planCaseNote = document.getElementById("plan-case-note");
  const planRunNote = document.getElementById("plan-run-note");
  const planNotesSave = document.getElementById("plan-notes-save");
  const planCaseEnabled = document.getElementById("plan-case-enabled");
  const planCaseSave = document.getElementById("plan-case-save");
  const planCaseUp = document.getElementById("plan-case-up");
  const planCaseDown = document.getElementById("plan-case-down");
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
  const planKnownNote = document.getElementById("plan-known-note");
  const planKnownJira = document.getElementById("plan-known-jira");
  const planKnownSave = document.getElementById("plan-known-save");
  const planKnownClear = document.getElementById("plan-known-clear");
  const planRunFailureSave = document.getElementById("plan-run-failure-save");
  const planCaseDetail = document.getElementById("plan-case-detail");
  const planDefectOut = document.getElementById("plan-defect-out");
  const planDegradedHint = document.getElementById("plan-degraded-hint");
  const planStatus = document.getElementById("plan-status");
  let openPlanId = "";
  let openPlanCases = [];
  let lastCaseRunId = "";
  let lastSuiteRunId = "";
  const jiraReadKey = document.getElementById("jira-read-key");
  const jiraReadBtn = document.getElementById("jira-read-btn");
  const jiraReadOut = document.getElementById("jira-read-out");
  const jiraReadStatus = document.getElementById("jira-read-status");
  const setTargetUrl = document.getElementById("set-target-url");
  const setTargetExe = document.getElementById("set-target-exe");
  const setApiEndpoint = document.getElementById("set-api-endpoint");
  const setTestFramework = document.getElementById("set-test-framework");
  const setPlaywrightMode = document.getElementById("set-playwright-mode");
  const setStorePath = document.getElementById("set-store-path");
  const setCreds = document.getElementById("set-creds");
  const setSummary = document.getElementById("set-summary");
  const setSave = document.getElementById("set-save");
  const setStatus = document.getElementById("set-status");
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
  const suiteSaved = document.getElementById("suite-saved");
  const suitePath = document.getElementById("suite-path");
  const suiteDiscover = document.getElementById("suite-discover");
  const suiteImport = document.getElementById("suite-import");
  const suiteRun = document.getElementById("suite-run");
  const suiteStatus = document.getElementById("suite-status");
  const msEnabled = document.getElementById("ms-enabled");
  const msPlugins = document.getElementById("ms-plugins");
  const msList = document.getElementById("ms-list");
  const msAction = document.getElementById("ms-action");
  const msId = document.getElementById("ms-id");
  const msLabel = document.getElementById("ms-label");
  const msUrl = document.getElementById("ms-url");
  const msSave = document.getElementById("ms-save");
  const msRun = document.getElementById("ms-run");
  const msUpsert = document.getElementById("ms-upsert");
  const msRemove = document.getElementById("ms-remove");
  const msStatus = document.getElementById("ms-status");
  const sandboxesSection = document.getElementById("app-section-sandboxes");
  const rptStatus = document.getElementById("rpt-status");
  const rptSectionsStatus = document.getElementById("rpt-sections-status");
  const rptChecks = {
    summary: document.getElementById("rpt-summary"),
    stories: document.getElementById("rpt-stories"),
    bugs: document.getElementById("rpt-bugs"),
    evidence: document.getElementById("rpt-evidence"),
    known_issues: document.getElementById("rpt-known-issues"),
  };
  const rptSave = document.getElementById("rpt-save");
  const rptLibrarySelect = document.getElementById("rpt-library-select");
  const rptLibraryRefresh = document.getElementById("rpt-library-refresh");
  const rptOpenSettings = document.getElementById("rpt-open-settings");
  const rptEmpty = document.getElementById("rpt-empty");
  const rptMarkdown = document.getElementById("rpt-markdown");
  const rptScreenshot = document.getElementById("rpt-screenshot");
  const rptJson = document.getElementById("rpt-json");
  const reportSettingsHeading = document.getElementById("report-settings-heading");
  const rptRunSelect = document.getElementById("rpt-run-select");
  const rptRunRefresh = document.getElementById("rpt-run-refresh");
  const rptExportRun = document.getElementById("rpt-export-run");
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
    browser_profiles: document.getElementById("priv-profiles"),
  };
  const privPropose = document.getElementById("priv-propose");
  const privConfirm = document.getElementById("priv-confirm");
  const privStatus = document.getElementById("priv-status");
  let pendingPrivacyCategories = null;
  const docText = document.getElementById("doc-text");
  const docParse = document.getElementById("doc-parse");
  const docProposal = document.getElementById("doc-proposal");
  const docDiff = document.getElementById("doc-diff");
  const docIdeas = document.getElementById("doc-ideas");
  const docConfirm = document.getElementById("doc-confirm");
  const docDecline = document.getElementById("doc-decline");
  const docStatus = document.getElementById("doc-status");
  let docProposalId = "";

  function applyReportSections(flags) {
    Object.keys(rptChecks).forEach(function (key) {
      if (rptChecks[key]) rptChecks[key].checked = !!flags[key];
    });
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

  function clearReportViewer(message) {
    if (rptMarkdown) rptMarkdown.textContent = message || "Select a report to read its markdown.";
    if (rptJson) rptJson.textContent = "No JSON found";
    if (rptScreenshot) {
      rptScreenshot.hidden = true;
      rptScreenshot.removeAttribute("src");
    }
  }

  async function loadReportDetail(reportId) {
    if (!reportId) {
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
      const previous = rptLibrarySelect ? rptLibrarySelect.value || "" : "";
      if (rptLibrarySelect) {
        rptLibrarySelect.innerHTML = "";
        if (!rows.length) {
          const blank = document.createElement("option");
          blank.value = "";
          blank.textContent = "— no reports yet —";
          rptLibrarySelect.appendChild(blank);
        } else {
          rows.forEach(function (row) {
            const opt = document.createElement("option");
            opt.value = row.id || "";
            opt.textContent = row.label || row.id || "report";
            rptLibrarySelect.appendChild(opt);
          });
          if (previous && Array.from(rptLibrarySelect.options).some(function (o) {
            return o.value === previous;
          })) {
            rptLibrarySelect.value = previous;
          }
        }
      }
      if (rptEmpty) rptEmpty.hidden = rows.length > 0;
      const chosen = rptLibrarySelect ? rptLibrarySelect.value : "";
      if (chosen) {
        await loadReportDetail(chosen);
      } else {
        clearReportViewer(
          (data && data.empty_hint) ||
            "No saved reports yet. Run a plan case or export a run."
        );
      }
    } catch (err) {
      if (rptEmpty) rptEmpty.hidden = false;
      clearReportViewer("Could not load the report library.");
    }
  }

  let settingsCategoryPending = null;

  function setSettingsCategory(cat) {
    const chosen = cat === "report" ? "report" : "app";
    const buttons = document.querySelectorAll(".settings-cat-btn[data-settings-cat]");
    const panels = document.querySelectorAll(".settings-cat-panel[data-settings-cat-panel]");
    buttons.forEach(function (btn) {
      const on = btn.getAttribute("data-settings-cat") === chosen;
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach(function (panel) {
      const on = panel.getAttribute("data-settings-cat-panel") === chosen;
      panel.hidden = !on;
    });
    if (chosen === "report" && reportSettingsHeading && typeof reportSettingsHeading.scrollIntoView === "function") {
      window.setTimeout(function () {
        reportSettingsHeading.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 40);
    }
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
        rptStatus.textContent =
          "Exported run " +
          runId +
          ". " +
          n +
          " pending heal(s) for this run — open Heal review to approve/reject (no auto-commit).";
      }
      if (healRunFilter) {
        healRunFilter.value = [planId, caseId, runId].join("|");
      }
      loadReportLibrary();
    } catch (err) {
      if (rptStatus) rptStatus.textContent = "Could not export chosen run.";
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
    if (setTargetUrl) {
      setTargetUrl.value = payload.target_url || "";
    }
    if (setTargetExe) {
      setTargetExe.value = payload.target_app_path || "";
    }
    if (setApiEndpoint) {
      setApiEndpoint.value = payload.api_endpoint || "";
    }
    if (setTestFramework) {
      const fw = (payload.test_framework || "playwright").toLowerCase();
      setTestFramework.value =
        fw === "selenium" || fw === "cypress" ? fw : "playwright";
    }
    if (setPlaywrightMode) {
      const mode = (payload.playwright_mode || "").toLowerCase();
      setPlaywrightMode.value =
        mode === "headless" || payload.playwright_headless ? "headless" : "headed";
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

  async function loadAppSettings() {
    try {
      const res = await fetch("/api/app-settings");
      if (!res.ok) return;
      applyAppSettings(await res.json());
      await loadOllamaModels();
      if (setStatus) setStatus.textContent = "Ready";
    } catch (err) {
      if (setStatus) setStatus.textContent = "Could not load app settings.";
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

  function renderPlanCases(plan) {
    openPlanCases = (plan && plan.suite && plan.suite.cases) || [];
    if (planIntent) {
      const intent = (plan && plan.intent) || "";
      planIntent.hidden = !intent;
      planIntent.textContent = intent || "";
    }
    if (!planCases) return;
    if (!openPlanCases.length) {
      planCases.textContent = "Cases: (none)";
      return;
    }
    planCases.innerHTML = openPlanCases
      .map(function (c, idx) {
        const en = c.enabled === false ? "OFF" : "ON";
        const src = (c.source && c.source.ref) || "";
        const kind = (c.source && c.source.kind) || "manual-draft";
        return (
          idx +
          1 +
          ". [" +
          en +
          "] " +
          (c.id || "?") +
          " — " +
          (c.name || "") +
          (c.jira_key ? " · Jira " + c.jira_key : "") +
          (kind === "manual-draft" && !c.jira_key ? " · manual-draft" : "") +
          (isKnownLabel(c) ? " · known" : "") +
          (src ? "\n   source: " + src : "") +
          (c.note ? "\n   note: " + c.note : "") +
          (c.known_issue && c.known_issue.note
            ? "\n   known: " + c.known_issue.note
            : "") +
          lastRunLine(c)
        );
      })
      .join("\n");
  }

  function renderCoverageGaps(payload) {
    function linesFor(list, emptyLabel) {
      const rows = list || [];
      if (!rows.length) return emptyLabel;
      return rows
        .map(function (r, idx) {
          return (
            idx +
            1 +
            ". " +
            (r.key || "?") +
            (r.summary ? " — " + r.summary : "") +
            " · cases " +
            (r.case_count != null ? r.case_count : 0)
          );
        })
        .join("\n");
    }
    if (planCoverageNoCase) {
      planCoverageNoCase.textContent =
        "No case:\n" + linesFor(payload && payload.no_case, "(none)");
    }
    if (planCoverageDisabled) {
      planCoverageDisabled.textContent =
        "All cases disabled:\n" +
        linesFor(payload && payload.all_disabled, "(none)");
    }
  }

  async function refreshCoverageGaps() {
    if (!openPlanId) {
      renderCoverageGaps({ no_case: [], all_disabled: [] });
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
        if (planCoverageNoCase) {
          planCoverageNoCase.textContent =
            payload.message || "Coverage gaps unavailable.";
        }
        if (planCoverageDisabled) planCoverageDisabled.textContent = "";
        return;
      }
      renderCoverageGaps(payload);
    } catch (err) {
      if (planCoverageNoCase) {
        planCoverageNoCase.textContent = "Could not load coverage gaps.";
      }
      if (planCoverageDisabled) planCoverageDisabled.textContent = "";
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
  }

  async function refreshCaseDetail() {
    if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
      if (planCaseDetail) planCaseDetail.hidden = true;
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
      const lines = [
        "Case: " + (payload.name || ""),
        "Jira: " + (payload.jira_key || "—"),
        "Source: " + (payload.source_kind || "manual-draft") + " — " + (payload.source_ref || "—"),
        payload.manual_draft ? "Marked manual-draft (no Jira/doc source)" : "",
        payload.note ? "Case note: " + payload.note : "",
        payload.tester_note ? "Run note: " + payload.tester_note : "",
        payload.known_label ? "Label: known (not a new regression)" : "",
        ki.note ? "Known note: " + ki.note : "",
        ki.jira_key ? "Known Jira: " + ki.jira_key : "",
        payload.last_run_summary ? "Last run: " + payload.last_run_summary : "Last run: (none)",
      ].filter(Boolean);
      planCaseDetail.hidden = false;
      planCaseDetail.textContent = lines.join("\n");
      if (planCaseNote && payload.note != null) planCaseNote.value = payload.note || "";
      if (planRunNote) planRunNote.value = payload.tester_note || "";
      if (planKnownNote) planKnownNote.value = ki.note || "";
      if (planKnownJira) planKnownJira.value = ki.jira_key || "";
      if (payload.last_run && payload.last_run.id) {
        lastCaseRunId = payload.last_run.id;
        if (planRunFailureClass && payload.last_run.failure_class) {
          planRunFailureClass.value = payload.last_run.failure_class;
        }
      }
    } catch (err) {
      if (planCaseDetail) planCaseDetail.hidden = true;
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
      renderPlanCases(payload.plan);
      await refreshCoverageGaps();
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

  function applyDesktopPlugin(payload) {
    if (!payload) return;
    if (deskEnabled) {
      deskEnabled.checked = !!payload.plugin_desktop_enabled;
    }
    if (deskPath) {
      deskPath.textContent =
        "App path: " + (payload.target_app_path || "(not set — pass a path on Run smoke)");
    }
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

  function applyPlaywrightSuite(payload) {
    if (!payload) return;
    const saved = payload.playwright_suite_path || "";
    if (suiteSaved) {
      suiteSaved.textContent = "Saved path: " + (saved || "(not set)");
    }
    if (suitePath && saved && !suitePath.value) {
      suitePath.value = saved;
    }
  }

  async function loadPlaywrightSuite() {
    try {
      const res = await fetch("/api/playwright-suite");
      if (!res.ok) return;
      applyPlaywrightSuite(await res.json());
      if (suiteStatus) suiteStatus.textContent = "Ready";
    } catch (err) {
      if (suiteStatus) suiteStatus.textContent = "Could not load Playwright suite settings.";
    }
  }

  function renderSandboxList(sandboxes) {
    if (!msList) return;
    const rows = Array.isArray(sandboxes) ? sandboxes : [];
    if (!rows.length) {
      msList.textContent = "Sandboxes: (none configured)";
      return;
    }
    msList.textContent =
      "Sandboxes: " +
      rows
        .map(function (s) {
          return (
            (s.id || "?") +
            "[" +
            (s.status || "idle") +
            "]" +
            (s.url ? " " + s.url : "")
          );
        })
        .join(" · ");
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
  const hudSecurityPanel = document.getElementById("hud-security");
  const hudReportsPanel = document.getElementById("hud-reports");
  const hudLabPanel = document.getElementById("hud-lab");
  const hudSecurityLevel = document.getElementById("hud-security-level");
  const hudReportsBody = document.getElementById("hud-reports-body");
  const hudLabMessage = document.getElementById("hud-lab-message");
  const hudLabStatus = document.getElementById("hud-lab-status");
  const hudLabConn = document.getElementById("hud-lab-conn");
  const hudLabDraft = document.getElementById("hud-lab-draft");
  const hudLabStarter = document.getElementById("hud-lab-starter");
  const hudLabIssue = document.getElementById("hud-lab-issue");
  let areaLayout = "overlay";
  let openAreaName = "";
  let hudFlags = { security: false, reports: false, lab: false };
  let labHomeEmpty = false;
  let hubCloseTimer = 0;

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
    }
    if (name === "heal") {
      loadExportableRuns().then(function () {
        loadHealProposals();
      });
    }
    if (name === "desktop") loadDesktopPlugin();
    if (name === "suites") loadPlaywrightSuite();
    if (name === "plans") loadPlanList(openPlanId);
    if (name === "sandboxes") loadMultiSandboxPlugin();
  }

  function selectedHealRunId() {
    if (!healRunFilter || !healRunFilter.value) return "";
    const parts = healRunFilter.value.split("|");
    return parts[2] || "";
  }

  function renderHealProposals(payload) {
    if (!healList) return;
    healList.innerHTML = "";
    const pending = (payload && payload.pending) || [];
    if (!pending.length) {
      const empty = document.createElement("p");
      empty.className = "heal-empty drawer-hint";
      empty.textContent = selectedHealRunId()
        ? "No pending heal proposals for this run."
        : "No pending heal proposals.";
      healList.appendChild(empty);
      return;
    }
    pending.forEach(function (item) {
      const card = document.createElement("article");
      card.className = "heal-card";
      card.dataset.id = item.id || "";
      const meta = document.createElement("p");
      meta.className = "heal-card-meta";
      meta.textContent = [
        item.kind || "locator",
        item.classification || "unclassified",
        item.run_id ? "run " + item.run_id : "",
        item.timestamp || "",
      ]
        .filter(Boolean)
        .join(" · ");
      const diff = document.createElement("pre");
      diff.className = "heal-diff";
      diff.textContent = item.proposal || item.message || "(no diff)";
      const row = document.createElement("div");
      row.className = "btn-row";
      const approveBtn = document.createElement("button");
      approveBtn.type = "button";
      approveBtn.className = "save-btn heal-approve";
      approveBtn.textContent = "Approve";
      approveBtn.dataset.id = item.id || "";
      const rejectBtn = document.createElement("button");
      rejectBtn.type = "button";
      rejectBtn.className = "save-btn secondary heal-reject";
      rejectBtn.textContent = "Reject";
      rejectBtn.dataset.id = item.id || "";
      row.appendChild(approveBtn);
      row.appendChild(rejectBtn);
      card.appendChild(meta);
      card.appendChild(diff);
      card.appendChild(row);
      healList.appendChild(card);
    });
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
    if (!id) return;
    if (healStatus) {
      healStatus.textContent = action === "approve" ? "Approving…" : "Rejecting…";
    }
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
        return;
      }
      await loadHealProposals();
      if (healStatus) {
        healStatus.textContent =
          action === "approve"
            ? "Approved — approver recorded; suite not auto-committed."
            : "Rejected — heal not treated as accepted.";
      }
    } catch (err) {
      if (healStatus) healStatus.textContent = "Could not update heal proposal.";
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

  document.querySelectorAll(".app-nav-item[data-section], .hub-spoke[data-section]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      openArea(btn.getAttribute("data-section"));
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
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    const hubOpen = isHubOpen();
    const appOpen = !!(appDrawer && appDrawer.classList.contains("open"));
    const screenOpen = !!(screenDrawer && screenDrawer.classList.contains("open"));
    if (!hubOpen && !openAreaName && !appOpen && !screenOpen) return;
    if (ev.target && (ev.target.tagName === "INPUT" || ev.target.tagName === "TEXTAREA")) {
      ev.target.blur();
    }
    if (hubOpen) {
      setHubOpen(false);
      ev.preventDefault();
      return;
    }
    if (openAreaName) {
      closeArea();
      ev.preventDefault();
      return;
    }
    if (appOpen) {
      setDrawer(appDrawer, appToggle, false);
      ev.preventDefault();
      return;
    }
    if (screenOpen) {
      setDrawer(screenDrawer, screenToggle, false);
      ev.preventDefault();
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
    };
    if (hudSecurityToggle) hudSecurityToggle.checked = hudFlags.security;
    if (hudReportsToggle) hudReportsToggle.checked = hudFlags.reports;
    if (hudLabToggle) hudLabToggle.checked = hudFlags.lab;
    const home = !openAreaName;
    if (hudSecurityPanel) hudSecurityPanel.hidden = !(home && hudFlags.security);
    if (hudReportsPanel) hudReportsPanel.hidden = !(home && hudFlags.reports);
    // Empty lab auto-shows checklist on home; toggle keeps it available when plans exist.
    if (hudLabPanel) {
      hudLabPanel.hidden = !(home && (labHomeEmpty || hudFlags.lab));
    }
  }

  function loadHud() {
    try {
      const raw = localStorage.getItem(HUD_KEY);
      applyHud(raw ? JSON.parse(raw) : { security: false, reports: false, lab: false });
    } catch (err) {
      applyHud({ security: false, reports: false, lab: false });
    }
  }

  function saveHud() {
    const flags = {
      security: !!(hudSecurityToggle && hudSecurityToggle.checked),
      reports: !!(hudReportsToggle && hudReportsToggle.checked),
      lab: !!(hudLabToggle && hudLabToggle.checked),
    };
    applyHud(flags);
    try {
      localStorage.setItem(HUD_KEY, JSON.stringify(flags));
    } catch (err) {
      console.warn("hud save failed", err);
    }
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
    } catch (err) {
      labHomeEmpty = false;
      if (hudLabStatus) hudLabStatus.textContent = "Could not load lab home status.";
      applyHud(hudFlags);
    }
  }

  if (hudSecurityToggle) hudSecurityToggle.addEventListener("change", saveHud);
  if (hudReportsToggle) hudReportsToggle.addEventListener("change", saveHud);
  if (hudLabToggle) hudLabToggle.addEventListener("change", saveHud);
  loadHud();
  loadHudReports();
  loadSecurityStatus();
  refreshLabHome();
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
        if (typeof refreshLabHome === "function") await refreshLabHome();
        if (planStatus) {
          planStatus.textContent = payload.message || "Project draft ready — review before run.";
        }
      } catch (err) {
        if (planStatus) planStatus.textContent = "Project draft request failed.";
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
        if (planStatus) planStatus.textContent = "Case saved locally.";
      } catch (err) {
        if (planStatus) planStatus.textContent = "Case save request failed.";
      }
    });
  }

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
      refreshCaseDetail();
    });
    planCaseId.addEventListener("blur", function () {
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
    const run = payload.run || {};
    if (planStatus) {
      planStatus.textContent =
        (payload.message || "Finished.") +
        (run.result ? " Result: " + run.result : "") +
        (run.duration_ms != null ? " (" + run.duration_ms + "ms)" : "");
    }
  }

  if (planCaseRun) {
    planCaseRun.addEventListener("click", async function () {
      if (!openPlanId || !planCaseId || !planCaseId.value.trim()) {
        if (planStatus) planStatus.textContent = "Enter a case id to run.";
        return;
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
            body: JSON.stringify({ pause_on_fail: pauseOn }),
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
    });
  }

  if (planRerunFailed) {
    planRerunFailed.addEventListener("click", async function () {
      if (!openPlanId) {
        if (planStatus) planStatus.textContent = "Open a plan first.";
        return;
      }
      if (planStatus) {
        planStatus.textContent = "Rerunning failed cases (sequential)…";
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
        const skipped = payload.skipped || [];
        const results = payload.case_results || [];
        const lines = [
          payload.message || "Rerun finished.",
          "Suite run: " + (payload.suite_run_id || "—"),
          payload.source_suite_run_id
            ? "Source suite run: " + payload.source_suite_run_id
            : "Source: last failed case results",
          "Sequential: " + (payload.sequential ? "yes" : "no"),
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
        ];
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

  function suitePathValue() {
    return suitePath && suitePath.value ? suitePath.value.trim() : "";
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
        if (suiteStatus) {
          suiteStatus.textContent =
            payload.message ||
            "OK — " + (payload.spec_count || 0) + " spec file(s).";
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite discover API.";
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
        if (suiteStatus) {
          suiteStatus.textContent = payload.message || "Suite path saved.";
        }
      } catch (err) {
        if (suiteStatus) suiteStatus.textContent = "Could not reach suite import API.";
      }
    });
  }

  if (suiteRun) {
    suiteRun.addEventListener("click", async function () {
      if (suiteStatus) suiteStatus.textContent = "Running suite…";
      try {
        const res = await fetch("/api/playwright-suite/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ suite_path: suitePathValue(), timeout_s: 300 }),
        });
        const payload = await res.json();
        if (!res.ok) {
          if (suiteStatus) suiteStatus.textContent = "Suite run request failed.";
          return;
        }
        if (payload.status === "pass") {
          if (suiteStatus) {
            suiteStatus.textContent =
              payload.message ||
              "Pass: " +
                (payload.passed || 0) +
                " passed, " +
                (payload.failed || 0) +
                " failed.";
          }
          return;
        }
        if (suiteStatus) {
          suiteStatus.textContent =
            payload.error || payload.message || "Suite run failed.";
        }
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
    msRemove.addEventListener("click", async function () {
      if (msStatus) msStatus.textContent = "Removing sandbox…";
      try {
        const payload = await runMultiSandboxAction("remove");
        if (payload.status === "disabled") {
          if (msStatus) {
            msStatus.textContent =
              payload.message || "Plugin disabled — enable and Save.";
          }
          return;
        }
        if (payload.status === "ok") {
          if (msStatus) msStatus.textContent = payload.message || "Sandbox removed.";
          return;
        }
        if (msStatus) {
          msStatus.textContent =
            payload.error || payload.message || "Remove failed.";
        }
      } catch (err) {
        if (msStatus) msStatus.textContent = "Could not reach orchestrate API.";
      }
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
        if (deskStatus) deskStatus.textContent = summarizeDesktopRun(payload, "smoke");
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
        if (deskStatus) deskStatus.textContent = summarizeDesktopRun(payload, "steps");
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
      } catch (err) {
        if (privStatus) privStatus.textContent = "Could not confirm delete.";
      }
    });
  }

  function renderDocProposal(payload) {
    docProposalId = payload.proposal_id || "";
    if (docDiff) {
      docDiff.innerHTML = "";
      const diff = payload.settings_diff || {};
      const keys = Object.keys(diff);
      if (!keys.length) {
        docDiff.textContent = "No settings changes proposed.";
      } else {
        keys.forEach(function (key) {
          const row = document.createElement("label");
          row.className = "check-row doc-diff-row";
          const box = document.createElement("input");
          box.type = "checkbox";
          box.checked = true;
          box.dataset.key = key;
          const span = document.createElement("span");
          const entry = diff[key] || {};
          span.textContent =
            key + ": " + (entry.from || "(empty)") + " → " + (entry.to || "");
          row.appendChild(box);
          row.appendChild(span);
          docDiff.appendChild(row);
        });
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
      docProposal.hidden = !(payload.settings_diff && Object.keys(payload.settings_diff).length);
      if (payload.test_ideas && payload.test_ideas.length && docProposal.hidden) {
        docProposal.hidden = false;
      }
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
          docStatus.textContent =
            data.note ||
            (data.status === "ideas_only"
              ? "Test ideas only — settings unchanged."
              : "Review the diff, then Confirm or Decline.");
        }
      } catch (err) {
        if (docStatus) docStatus.textContent = "Could not parse the document.";
      }
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
        if (docStatus) {
          const updated = Object.keys(data.updated || {});
          docStatus.textContent =
            "Stored: " + (updated.length ? updated.join(", ") : "nothing") + ".";
        }
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
  if (healList) {
    healList.addEventListener("click", function (ev) {
      const target = ev.target;
      if (!target || !target.classList) return;
      const id = target.getAttribute("data-id") || "";
      if (target.classList.contains("heal-approve")) {
        resolveHealProposal(id, "approve");
      } else if (target.classList.contains("heal-reject")) {
        resolveHealProposal(id, "reject");
      }
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
  if (rptLibrarySelect) {
    rptLibrarySelect.addEventListener("change", function () {
      loadReportDetail(rptLibrarySelect.value || "");
    });
  }
  if (rptOpenSettings) {
    rptOpenSettings.addEventListener("click", function () {
      openReportSettings();
    });
  }
  document.querySelectorAll(".settings-cat-btn[data-settings-cat]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setSettingsCategory(btn.getAttribute("data-settings-cat"));
    });
  });

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
