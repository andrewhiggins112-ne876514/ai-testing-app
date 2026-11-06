(function () {
  const node = document.getElementById("orb-config");
  const host = document.getElementById("energy-orb-host");
  const chatPanel = document.getElementById("chat-panel");
  const chatLog = document.getElementById("chat-log");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const drawer = document.getElementById("side-drawer");
  const drawerToggle = document.getElementById("drawer-toggle");
  const orbControls = document.getElementById("orb-controls");

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

  function applyConfigToNode(cfg) {
    if (!node || !cfg) return;
    node.setAttribute("data-style", cfg.style || "mystic");
    node.setAttribute("data-calm-color", cfg.calm_color || "#50cdff");
    node.setAttribute("data-thinking-color", cfg.thinking_color || "#b388ff");
    node.setAttribute("data-size", String(cfg.size || 360));
    node.setAttribute("data-shape", cfg.shape || "sphere");
    node.setAttribute("data-spin-speed", String(cfg.spin_speed ?? 1));
    node.setAttribute("data-turbulence", String(cfg.turbulence ?? 1));
    node.setAttribute("data-pulse", String(cfg.pulse ?? 1));
    node.setAttribute("data-glow", String(cfg.glow ?? 1));
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
  }

  function liveFromControls() {
    applyConfigToNode({
      style: ctrls.style.value,
      calm_color: ctrls.calm.value,
      thinking_color: ctrls.thinking.value,
      size: parseInt(ctrls.size.value, 10),
      shape: "sphere",
      spin_speed: parseFloat(ctrls.spin.value),
      turbulence: parseFloat(ctrls.turbulence.value),
      pulse: parseFloat(ctrls.pulse.value),
      glow: parseFloat(ctrls.glow.value),
    });
  }

  Object.values(ctrls).forEach(function (el) {
    el.addEventListener("input", liveFromControls);
    el.addEventListener("change", liveFromControls);
  });

  document.getElementById("ctrl-save").addEventListener("click", async function () {
    liveFromControls();
    const body = {
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

  function setDrawerOpen(open) {
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    drawerToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  drawerToggle.addEventListener("click", function () {
    setDrawerOpen(!drawer.classList.contains("open"));
  });

  drawer.querySelectorAll("[data-action]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const action = btn.getAttribute("data-action");
      if (action === "toggle-chat") {
        chatPanel.classList.toggle("hidden");
        btn.classList.toggle("active", !chatPanel.classList.contains("hidden"));
      } else if (action === "toggle-orb") {
        const show = orbControls.hasAttribute("hidden");
        if (show) orbControls.removeAttribute("hidden");
        else orbControls.setAttribute("hidden", "");
        btn.classList.toggle("active", show);
      }
    });
  });

  async function boot() {
    try {
      const res = await fetch("/api/orb");
      if (res.ok) {
        const cfg = await res.json();
        if (cfg.style !== "mystic" && cfg.style !== "aether" && cfg.style !== "neural") {
          cfg.style = "mystic";
        }
        applyConfigToNode(cfg);
      }
    } catch (err) {
      applyConfigToNode({ style: "mystic" });
    }
    syncControlsFromNode();
    if (window.__orbWebGL && host) {
      window.__orbWebGL.attach(host);
    }
  }

  boot();
})();
