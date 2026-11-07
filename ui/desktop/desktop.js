(function () {
  const LAYOUT_KEY = "desktop-shell-layout-v1";
  const ORB_STYLES_KEY = "desktop-orb-styles-v1";
  const WEBGL_STYLES = ["mystic", "aether", "neural", "apex"];
  const EDGE_PAD = 16;
  const DRAG_THRESHOLD = 6;
  const BTN = 42;
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

  function appendMsg(who, text) {
    const row = document.createElement("div");
    row.className = "msg " + who;
    const label = document.createElement("span");
    label.className = "who";
    label.textContent = who === "user" ? "You" : "Agent";
    const body = document.createElement("div");
    body.textContent = text;
    row.appendChild(label);
    row.appendChild(body);
    chatLog.appendChild(row);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  chatForm.addEventListener("submit", async function (ev) {
    ev.preventDefault();
    const message = (chatInput.value || "").trim();
    if (!message) return;
    chatInput.value = "";
    appendMsg("user", message);
    window.__energyOrbMode = "thinking";
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, session_id: "desktop" }),
      });
      const data = await res.json();
      appendMsg("agent", data.reply || "(no reply)");
    } catch (err) {
      appendMsg("agent", "Could not reach the local agent. Is the server running?");
    } finally {
      window.__energyOrbMode = "calm";
    }
  });

  function setDrawer(drawer, toggle, open) {
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
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
        return { toggles: {}, widgets: {}, appearance: defaultAppearance() };
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
        appearance: normalizeAppearance(appearanceSrc),
      };
    } catch (err) {
      return { toggles: {}, widgets: {}, appearance: defaultAppearance() };
    }
  }

  function accentForStyle(style) {
    return STYLE_ACCENTS[style] || STYLE_ACCENTS.mystic;
  }

  function applyAccentVars(hex) {
    const c = hexToRgb(normalizeHex(hex, DEFAULT_APPEARANCE.border));
    const root = document.documentElement;
    root.style.setProperty("--cyan", normalizeHex(hex, DEFAULT_APPEARANCE.border));
    root.style.setProperty(
      "--cyan-dim",
      "rgba(" + c.r + ", " + c.g + ", " + c.b + ", 0.22)"
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
    const edge = toggle.dataset.edge || "left";
    drawer.classList.remove("edge-left", "edge-right", "edge-top", "edge-bottom");
    drawer.classList.add("edge-" + edge);
    clearPos(drawer);

    const tr = toggle.getBoundingClientRect();
    const W = window.innerWidth;
    const H = window.innerHeight;

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

  function placeWidget(el, left, top) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const rect = el.getBoundingClientRect();
    const w = rect.width || 320;
    const h = rect.height || 280;
    const x = clamp(left, 8, Math.max(8, W - w - 8));
    const y = clamp(top, 8, Math.max(8, H - h - 8));
    el.style.left = x + "px";
    el.style.top = y + "px";
    el.style.right = "auto";
    el.style.bottom = "auto";
    return { left: x, top: y };
  }

  function persistWidget(el) {
    layout.widgets[el.dataset.widget || el.id] = {
      left: parseFloat(el.style.left) || 0,
      top: parseFloat(el.style.top) || 0,
    };
    saveLayout(layout);
  }

  function restoreLayout() {
    [appToggle, screenToggle].forEach(function (el) {
      const saved = layout.toggles[el.id];
      const edge = (saved && saved.edge) || el.getAttribute("data-default-edge") || "left";
      const along = saved && typeof saved.along === "number" ? saved.along : null;
      placeToggle(el, edge, along);
      syncDrawerEdge(el, toggleDrawerMap.get(el));
    });

    document.querySelectorAll("[data-widget]").forEach(function (el) {
      const key = el.dataset.widget || el.id;
      const saved = layout.widgets[key];
      if (saved && typeof saved.left === "number" && typeof saved.top === "number") {
        placeWidget(el, saved.left, saved.top);
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
      pointerId = null;
      el.classList.remove("dragging");

      if (wasDrag) {
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
        syncDrawerEdge(el, toggleDrawerMap.get(el));
        persistToggle(el);
      } else {
        el.classList.add("edge-snap");
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
      if (ev.target.closest && ev.target.closest("button, a, input, textarea, select")) return;
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

  bindEdgeSnapToggle(appToggle);
  bindEdgeSnapToggle(screenToggle);
  document.querySelectorAll("[data-widget]").forEach(bindWidgetDrag);

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
  }

  boot();
})();
