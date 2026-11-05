"""Minimal local Gradio chat client. Talks to the FastAPI agent on port 8000."""
import json
import os
import re
import sys
import uuid
from pathlib import Path

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr
import httpx
from reports.exporter import reports_dir
from settings.store import load_settings, update_setting, write_settings

CHAT_URL = "http://127.0.0.1:8000/chat"
LEVELS = ("OFFICIAL", "SECRET")
VOID = "#05070d"
ORB_STYLES = (
    "lightning",
    "mist",
    "nebula",
    "nebula+lightning",
    "mystic sphere",
    "aether ring",
    "neural mesh",
)
ORB_SHAPES = ("sphere", "oval", "ring")
ORB_DEFAULTS = {
    "style": "lightning",
    "calm_color": "#50cdff",
    "thinking_color": "#b388ff",
    "size": 360,
    "shape": "sphere",
    "spin_speed": 1.0,
    "turbulence": 1.0,
    "pulse": 1.0,
    "glow": 1.0,
}
_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PRESET_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,39}$")


def normalize_orb_config(raw) -> dict:
    raw = raw or {}
    style = raw.get("style")
    if style not in ORB_STYLES:
        style = ORB_DEFAULTS["style"]
    calm = str(raw.get("calm_color") or "").strip()
    calm = calm.lower() if _HEX_COLOR.match(calm) else ORB_DEFAULTS["calm_color"]
    thinking = str(raw.get("thinking_color") or "").strip()
    thinking = thinking.lower() if _HEX_COLOR.match(thinking) else ORB_DEFAULTS["thinking_color"]
    try:
        size = int(round(float(raw.get("size"))))
    except (TypeError, ValueError):
        size = ORB_DEFAULTS["size"]
    size = max(200, min(480, size))
    shape = raw.get("shape")
    if shape not in ORB_SHAPES:
        shape = ORB_DEFAULTS["shape"]
    return {
        "style": style,
        "calm_color": calm,
        "thinking_color": thinking,
        "size": size,
        "shape": shape,
        "spin_speed": _unit_amount(raw.get("spin_speed")),
        "turbulence": _unit_amount(raw.get("turbulence")),
        "pulse": _unit_amount(raw.get("pulse")),
        "glow": _unit_amount(raw.get("glow")),
    }


def _unit_amount(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 1.0
    return max(0.0, min(2.0, number))


def current_orb_config() -> dict:
    data = load_settings()
    return normalize_orb_config({
        "style": data.get("orb_style"),
        "calm_color": data.get("orb_calm_color"),
        "thinking_color": data.get("orb_thinking_color"),
        "size": data.get("orb_size"),
        "shape": data.get("orb_shape"),
        "spin_speed": data.get("orb_spin_speed"),
        "turbulence": data.get("orb_turbulence"),
        "pulse": data.get("orb_pulse"),
        "glow": data.get("orb_glow"),
    })


def orb_config_markup(cfg: dict) -> str:
    cfg = normalize_orb_config(cfg)
    return (
        '<div id="orb-config" hidden'
        f' data-style="{cfg["style"]}"'
        f' data-calm-color="{cfg["calm_color"]}"'
        f' data-thinking-color="{cfg["thinking_color"]}"'
        f' data-size="{cfg["size"]}"'
        f' data-shape="{cfg["shape"]}"'
        f' data-spin-speed="{cfg["spin_speed"]}"'
        f' data-turbulence="{cfg["turbulence"]}"'
        f' data-pulse="{cfg["pulse"]}"'
        f' data-glow="{cfg["glow"]}"></div>'
    )


def save_orb_config(style, calm_color, thinking_color, size, shape="sphere", spin_speed=1, turbulence=1, pulse=1, glow=1):
    cfg = normalize_orb_config({
        "style": style,
        "calm_color": calm_color,
        "thinking_color": thinking_color,
        "size": size,
        "shape": shape,
        "spin_speed": spin_speed,
        "turbulence": turbulence,
        "pulse": pulse,
        "glow": glow,
    })
    update_setting("orb_style", cfg["style"], confirm=True)
    update_setting("orb_calm_color", cfg["calm_color"], confirm=True)
    update_setting("orb_thinking_color", cfg["thinking_color"], confirm=True)
    update_setting("orb_size", cfg["size"], confirm=True)
    update_setting("orb_shape", cfg["shape"], confirm=True)
    update_setting("orb_spin_speed", cfg["spin_speed"], confirm=True)
    update_setting("orb_turbulence", cfg["turbulence"], confirm=True)
    update_setting("orb_pulse", cfg["pulse"], confirm=True)
    update_setting("orb_glow", cfg["glow"], confirm=True)
    return orb_config_markup(cfg)


def current_orb_inputs():
    cfg = current_orb_config()
    return (
        cfg["style"],
        cfg["calm_color"],
        cfg["thinking_color"],
        cfg["size"],
        cfg["shape"],
        cfg["spin_speed"],
        cfg["turbulence"],
        cfg["pulse"],
        cfg["glow"],
    )


def normalize_preset_name(name) -> str:
    text = str(name or "").strip()
    if not _PRESET_NAME.match(text):
        return ""
    return text


def _orb_presets_map() -> dict:
    raw = load_settings().get("orb_presets") or {}
    if not isinstance(raw, dict):
        return {}
    cleaned = {}
    for key, value in raw.items():
        name = normalize_preset_name(key)
        if not name or not isinstance(value, dict):
            continue
        cleaned[name] = normalize_orb_config(value)
    return cleaned


def list_orb_preset_names() -> list:
    return sorted(_orb_presets_map().keys())


def _apply_orb_cfg(cfg: dict) -> str:
    return save_orb_config(
        cfg["style"],
        cfg["calm_color"],
        cfg["thinking_color"],
        cfg["size"],
        cfg["shape"],
        cfg["spin_speed"],
        cfg["turbulence"],
        cfg["pulse"],
        cfg["glow"],
    )


def _preset_dropdown_update(names=None, value=None):
    names = list(names if names is not None else list_orb_preset_names())
    if not names:
        return gr.update(choices=["(none yet)"], value="(none yet)")
    if value not in names:
        value = names[0]
    return gr.update(choices=names, value=value)


def save_orb_preset(name, style, calm_color, thinking_color, size, shape, spin_speed, turbulence, pulse, glow):
    preset = normalize_preset_name(name)
    cfg = normalize_orb_config({
        "style": style,
        "calm_color": calm_color,
        "thinking_color": thinking_color,
        "size": size,
        "shape": shape,
        "spin_speed": spin_speed,
        "turbulence": turbulence,
        "pulse": pulse,
        "glow": glow,
    })
    markup = _apply_orb_cfg(cfg)
    if not preset:
        return markup, _preset_dropdown_update(), "Preset name must be 1–40 letters, numbers, spaces, _ or -."
    settings = load_settings()
    presets = _orb_presets_map()
    presets[preset] = cfg
    settings["orb_presets"] = presets
    settings["orb_active_preset"] = preset
    write_settings(settings)
    return markup, _preset_dropdown_update(sorted(presets.keys()), preset), f"Saved preset '{preset}'."


def load_orb_preset(name):
    if str(name or "").strip() in ("", "(none yet)"):
        cfg = current_orb_config()
        return (
            orb_config_markup(cfg),
            cfg["style"],
            cfg["calm_color"],
            cfg["thinking_color"],
            cfg["size"],
            cfg["shape"],
            cfg["spin_speed"],
            cfg["turbulence"],
            cfg["pulse"],
            cfg["glow"],
            "No preset selected yet — save one first.",
        )
    preset = normalize_preset_name(name)
    presets = _orb_presets_map()
    if not preset or preset not in presets:
        cfg = current_orb_config()
        return (
            orb_config_markup(cfg),
            cfg["style"],
            cfg["calm_color"],
            cfg["thinking_color"],
            cfg["size"],
            cfg["shape"],
            cfg["spin_speed"],
            cfg["turbulence"],
            cfg["pulse"],
            cfg["glow"],
            f"Unknown preset '{name}'.",
        )
    cfg = presets[preset]
    markup = _apply_orb_cfg(cfg)
    update_setting("orb_active_preset", preset, confirm=True)
    return (
        markup,
        cfg["style"],
        cfg["calm_color"],
        cfg["thinking_color"],
        cfg["size"],
        cfg["shape"],
        cfg["spin_speed"],
        cfg["turbulence"],
        cfg["pulse"],
        cfg["glow"],
        f"Loaded preset '{preset}'.",
    )


def delete_orb_preset(name):
    preset = normalize_preset_name(name)
    settings = load_settings()
    presets = _orb_presets_map()
    if not preset or preset not in presets:
        return _preset_dropdown_update(), f"Unknown preset '{name}'."
    del presets[preset]
    settings["orb_presets"] = presets
    if settings.get("orb_active_preset") == preset:
        settings["orb_active_preset"] = ""
    write_settings(settings)
    return _preset_dropdown_update(sorted(presets.keys())), f"Deleted preset '{preset}'."


def toggle_orb_settings(is_open: bool):
    nxt = not bool(is_open)
    return nxt, gr.update(visible=nxt)


ORB_HTML = """
<div class="energy-orb" data-state="calm">
  <canvas width="680" height="800" aria-label="energy orb"></canvas>
  <div class="orb-state">CALM</div>
</div>
"""

ORB_JS = r"""
const canvas = element.querySelector("canvas");
const label = element.querySelector(".orb-state");
if (!canvas) return;
const ctx = canvas.getContext("2d");
let viewW = 360;
let viewH = 360;
let appliedSize = 0;
let glowRgb = { r: 80, g: 205, b: 255 };

function applySize(size) {
  const next = size || 360;
  if (next === appliedSize) return;
  appliedSize = next;
  viewW = next;
  viewH = next;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(viewW * dpr);
  canvas.height = Math.round(viewH * dpr);
  canvas.style.width = viewW + "px";
  canvas.style.height = viewH + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const orb = element.querySelector(".energy-orb");
  if (orb) orb.style.minHeight = (next + 28) + "px";
}

function hexToRgb(hex) {
  const h = String(hex || "").replace("#", "").trim();
  if (!/^[0-9a-fA-F]{6}/.test(h)) return { r: 80, g: 205, b: 255 };
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

function rgba(rgb, alpha) {
  return "rgba(" + rgb.r + "," + rgb.g + "," + rgb.b + "," + alpha + ")";
}

function mixWhite(rgb, amount) {
  return {
    r: Math.round(rgb.r + (255 - rgb.r) * amount),
    g: Math.round(rgb.g + (255 - rgb.g) * amount),
    b: Math.round(rgb.b + (255 - rgb.b) * amount),
  };
}

function shade(rgb, amount) {
  return {
    r: Math.round(rgb.r * amount),
    g: Math.round(rgb.g * amount),
    b: Math.round(rgb.b * amount),
  };
}

function mixRgb(a, b, t) {
  return {
    r: Math.round(a.r + (b.r - a.r) * t),
    g: Math.round(a.g + (b.g - a.g) * t),
    b: Math.round(a.b + (b.b - a.b) * t),
  };
}

function rgbToHex(rgb) {
  function part(n) {
    const hex = Math.max(0, Math.min(255, Math.round(n))).toString(16);
    return hex.length === 1 ? "0" + hex : hex;
  }
  return "#" + part(rgb.r) + part(rgb.g) + part(rgb.b);
}

function readConfig() {
  const node = document.getElementById("orb-config");
  let style = node ? (node.getAttribute("data-style") || "lightning") : "lightning";
  const calm = node ? (node.getAttribute("data-calm-color") || "#50cdff") : "#50cdff";
  const thinkingColor = node ? (node.getAttribute("data-thinking-color") || "#b388ff") : "#b388ff";
  let size = node ? parseInt(node.getAttribute("data-size") || "360", 10) : 360;
  if (!size || size < 200) size = 200;
  if (size > 480) size = 480;
  const allowedStyles = {
    lightning: 1,
    mist: 1,
    nebula: 1,
    "nebula+lightning": 1,
    "mystic sphere": 1,
    "aether ring": 1,
    "neural mesh": 1,
  };
  if (!allowedStyles[style]) style = "lightning";
  let shape = node ? (node.getAttribute("data-shape") || "sphere") : "sphere";
  if (shape !== "sphere" && shape !== "oval" && shape !== "ring") shape = "sphere";
  function unit(raw) {
    let amount = parseFloat(raw);
    if (isNaN(amount)) amount = 1;
    if (amount < 0) amount = 0;
    if (amount > 2) amount = 2;
    return amount;
  }
  const spin = unit(node ? node.getAttribute("data-spin-speed") : "1");
  const turbulence = unit(node ? node.getAttribute("data-turbulence") : "1");
  const pulseAmt = unit(node ? node.getAttribute("data-pulse") : "1");
  const glowAmt = unit(node ? node.getAttribute("data-glow") : "1");
  return {
    style: style,
    calm: calm,
    thinking: thinkingColor,
    size: size,
    shape: shape,
    spin: spin,
    turbulence: turbulence,
    pulseAmt: pulseAmt,
    glowAmt: glowAmt,
  };
}

function driftSpin(scene, drift) {
  return scene.angle * scene.swirl * (1 + (drift - 1) * scene.turbulence);
}

function jitter(scene, index) {
  return Math.sin(scene.now * 0.004 + index) * 0.22 * scene.turbulence;
}

if (element._orbStop) element._orbStop();
window.__energyOrbBoots = (window.__energyOrbBoots || 0) + 1;
let stopped = false;
let frame = 0;
let watchTimer = 0;
let angle = element._orbAngle || 0;
let lastTime = 0;
let mood = 0;
element._orbStop = function () {
  stopped = true;
  cancelAnimationFrame(frame);
  if (watchTimer) {
    clearTimeout(watchTimer);
    watchTimer = 0;
  }
  if (element._orbInterval) {
    clearInterval(element._orbInterval);
    element._orbInterval = 0;
  }
  if (element._orbObserver) {
    element._orbObserver.disconnect();
    element._orbObserver = null;
  }
  element._orbAngle = angle;
};

let mode = "calm";
let sawLoading = false;
let armedAt = 0;

function chatRoot() {
  return document.getElementById("agent-chat");
}

function loading() {
  const root = chatRoot();
  return !!(root && root.querySelector('[aria-label="Loading response"]'));
}

function setMode(next) {
  if (next === mode && window.__energyOrbMode === next) return;
  mode = next;
  window.__energyOrbMode = next;
  const liveOrb = document.querySelector("#energy-orb-host .energy-orb");
  if (liveOrb) liveOrb.setAttribute("data-state", next);
}

function armThinking() {
  sawLoading = false;
  armedAt = Date.now();
  setMode("thinking");
}

function tick() {
  if (loading()) {
    sawLoading = true;
    setMode("thinking");
    return;
  }
  if (sawLoading) {
    sawLoading = false;
    armedAt = 0;
    setMode("calm");
    return;
  }
  if (mode === "thinking" && armedAt && Date.now() - armedAt > 8000) {
    armedAt = 0;
    setMode("calm");
  }
}

if (!window.__energyOrbInputBound) {
  window.__energyOrbInputBound = true;
  document.addEventListener("keydown", function (event) {
    try {
      if (event.key !== "Enter" || event.shiftKey) return;
      const root = chatRoot();
      if (!root || !event.target || !root.contains(event.target)) return;
      if (event.target.tagName !== "TEXTAREA") return;
      if (!String(event.target.value || "").trim()) return;
      armThinking();
    } catch (err) {}
  }, true);
  document.addEventListener("click", function (event) {
    try {
      const root = chatRoot();
      if (!root || !event.target || !event.target.closest) return;
      const button = event.target.closest('[data-testid="submit-button"]');
      if (!button || !root.contains(button)) return;
      const box = root.querySelector("textarea");
      if (!box || !String(box.value || "").trim()) return;
      armThinking();
    } catch (err) {}
  }, true);
}

function watchChat() {
  const root = chatRoot();
  if (!root) {
    watchTimer = setTimeout(watchChat, 200);
    return;
  }
  if (element._orbObserver) element._orbObserver.disconnect();
  const observer = new MutationObserver(tick);
  element._orbObserver = observer;
  observer.observe(root, { childList: true, subtree: true });
  tick();
}
watchChat();
element._orbInterval = setInterval(tick, 200);

function hash(n) {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

const webs = [];
function addArc(index, theta, phi, dir, span, width, gain, speed, target) {
  const points = [];
  const steps = 26;
  for (let step = 0; step <= steps; step++) {
    const u = step / steps;
    const along = (u - 0.5) * span;
    const wave = Math.sin(u * Math.PI * 2.4 + index) * 0.11 + Math.sin(u * Math.PI * 5.2 + index * 1.6) * 0.045;
    let nextPhi = phi + Math.sin(dir) * along + wave;
    if (nextPhi < 0.28) nextPhi = 0.28;
    if (nextPhi > Math.PI - 0.28) nextPhi = Math.PI - 0.28;
    points.push({
      theta: theta + Math.cos(dir) * along + wave * 0.4,
      phi: nextPhi,
    });
  }
  (target || webs).push({ points: points, speed: speed, width: width, gain: gain });
}
for (let index = 0; index < 64; index++) {
  const theta = hash(index + 1) * Math.PI * 2;
  const phi = 0.4 + hash(index + 2) * 2.34;
  const dir = hash(index + 3) * Math.PI * 2;
  const bolt = index % 8 === 0;
  const span = bolt ? 1.55 + hash(index + 4) * 0.45 : 0.85 + hash(index + 4) * 0.7;
  addArc(
    index,
    theta,
    phi,
    dir,
    span,
    bolt ? 0.9 : 0.36 + hash(index + 5) * 0.24,
    bolt ? 0.95 : 0.48 + hash(index + 6) * 0.4,
    0.35 + hash(index + 7) * 1.05
  );
  if (index % 3 === 0) {
    addArc(
      index + 80,
      theta + 0.05,
      phi,
      dir + 1.15 + hash(index + 9),
      span * 0.62,
      0.34,
      0.55,
      0.5 + hash(index + 11) * 0.8
    );
  }
}
for (let index = 0; index < 24; index++) {
  const parent = webs[index % webs.length];
  const origin = parent.points[Math.min(8, parent.points.length - 1)];
  addArc(
    300 + index,
    origin.theta,
    origin.phi,
    hash(index + 15) * Math.PI * 2,
    0.22 + hash(index + 16) * 0.2,
    0.26,
    0.75,
    parent.speed
  );
}

const puffs = [];
for (let index = 0; index < 40; index++) {
  puffs.push({
    theta: hash(index + 3) * Math.PI * 2,
    phi: 0.45 + hash(index + 8) * 2.2,
    drift: 0.15 + hash(index + 13) * 0.55,
    size: 0.12 + hash(index + 17) * 0.22,
  });
}

const clouds = [];
for (let index = 0; index < 6; index++) {
  clouds.push({
    theta: hash(index + 90) * Math.PI * 2,
    phi: 0.7 + hash(index + 91) * 1.6,
    speed: 0.25 + hash(index + 92) * 0.9,
    reach: 0.38 + hash(index + 93) * 0.28,
    dark: index % 2 === 1,
  });
}

const stars = [];
for (let index = 0; index < 28; index++) {
  stars.push({
    theta: hash(index + 120) * Math.PI * 2,
    phi: 0.4 + hash(index + 121) * 2.3,
    twinkle: hash(index + 122) * Math.PI * 2,
  });
}

const bolts = [];
for (let index = 0; index < 6; index++) {
  addArc(
    400 + index,
    hash(index + 200) * Math.PI * 2,
    0.6 + hash(index + 201) * 1.8,
    hash(index + 202) * Math.PI * 2,
    0.7 + hash(index + 203) * 0.5,
    0.7,
    0.9,
    0.8 + hash(index + 204) * 0.4,
    bolts
  );
}

const aetherDust = [];
for (let index = 0; index < 140; index++) {
  const onRing = index < 90;
  aetherDust.push({
    angle: hash(index + 500) * Math.PI * 2,
    radius: onRing ? 0.78 + hash(index + 501) * 0.28 : 0.2 + hash(index + 502) * 1.35,
    size: onRing ? 0.6 + hash(index + 503) * 1.4 : 1.5 + hash(index + 504) * 4.5,
    speed: 0.15 + hash(index + 505) * 0.55,
    twinkle: hash(index + 506) * Math.PI * 2,
    bokeh: !onRing && hash(index + 507) > 0.72,
  });
}

const aetherBlades = [];
for (let index = 0; index < 10; index++) {
  aetherBlades.push({
    angle: (index / 10) * Math.PI * 2 + hash(index + 520) * 0.35,
    sweep: 0.55 + hash(index + 521) * 0.55,
    width: 0.12 + hash(index + 522) * 0.1,
    speed: 0.35 + hash(index + 523) * 0.45,
    alpha: 0.12 + hash(index + 524) * 0.16,
  });
}

const neuralPoints = [];
for (let index = 0; index < 520; index++) {
  neuralPoints.push({
    theta: hash(index + 600) * Math.PI * 2,
    phi: Math.acos(2 * hash(index + 601) - 1),
    size: 0.45 + hash(index + 602) * 1.35,
    speed: 0.12 + hash(index + 603) * 0.5,
    twinkle: hash(index + 604) * Math.PI * 2,
    shell: hash(index + 605) > 0.82,
  });
}

const neuralSpokes = [];
for (let index = 0; index < 28; index++) {
  neuralSpokes.push({
    theta: hash(index + 650) * Math.PI * 2,
    phi: 0.35 + hash(index + 651) * 2.4,
    speed: 0.2 + hash(index + 652) * 0.4,
    gain: 0.25 + hash(index + 653) * 0.45,
  });
}

const neuralBlocks = [];
for (let index = 0; index < 36; index++) {
  neuralBlocks.push({
    theta: hash(index + 680) * Math.PI * 2,
    phi: 0.45 + hash(index + 681) * 2.2,
    arc: 0.08 + hash(index + 682) * 0.18,
    speed: 0.15 + hash(index + 683) * 0.35,
  });
}

function fillGlow(cx, cy, radius, reach, inner, mid) {
  const glow = ctx.createRadialGradient(cx, cy, radius * 0.2, cx, cy, reach);
  glow.addColorStop(0, inner);
  glow.addColorStop(0.5, mid);
  glow.addColorStop(1, "rgba(5, 7, 13, 0)");
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(cx, cy, reach, 0, Math.PI * 2);
  ctx.fill();
}

function projectPoint(point, spin, cx, cy, radius) {
  const theta = point.theta + spin;
  const phi = point.phi;
  const sinPhi = Math.sin(phi);
  const x = sinPhi * Math.cos(theta);
  const y = Math.cos(phi);
  const z = sinPhi * Math.sin(theta);
  return { x: cx + x * radius, y: cy + y * radius, z: z };
}

function webPaths(spec, spin, cx, cy, radius) {
  const front = new Path2D();
  const back = new Path2D();
  let prev = null;
  let frontPen = false;
  let backPen = false;
  const limit = radius * 0.14;
  for (let index = 0; index < spec.points.length; index++) {
    const point = projectPoint(spec.points[index], spin, cx, cy, radius);
    if (prev) {
      const dx = point.x - prev.x;
      const dy = point.y - prev.y;
      const near = dx * dx + dy * dy < limit * limit;
      const onFront = point.z > -0.04 && prev.z > -0.04;
      if (near && onFront) {
        if (!frontPen) front.moveTo(prev.x, prev.y);
        front.lineTo(point.x, point.y);
        frontPen = true;
        backPen = false;
      } else if (near) {
        if (!backPen) back.moveTo(prev.x, prev.y);
        back.lineTo(point.x, point.y);
        backPen = true;
        frontPen = false;
      } else {
        frontPen = false;
        backPen = false;
      }
    }
    prev = point;
  }
  return { front: front, back: back };
}

function strokeWeb(path, width, alpha) {
  if (alpha < 0.03) return;
  ctx.lineWidth = width + 0.4;
  ctx.strokeStyle = rgba(glowRgb, alpha * 0.28);
  ctx.stroke(path);
  ctx.lineWidth = Math.max(0.55, width * 0.72);
  ctx.strokeStyle = "rgba(240, 253, 255, " + Math.min(1, alpha) + ")";
  ctx.stroke(path);
}

function strokeRing(cx, cy, rx, ry, rotation, width, alpha) {
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, rotation, 0, Math.PI * 2);
  ctx.lineWidth = width + 2.4;
  ctx.strokeStyle = rgba(glowRgb, alpha * 0.32);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, rotation, 0, Math.PI * 2);
  ctx.lineWidth = width;
  ctx.strokeStyle = "rgba(226, 250, 255, " + alpha + ")";
  ctx.stroke();
}

function boltLife(spec, scene, index, occasional) {
  const base = occasional ? 0.7 : 0.85;
  const gap = (base - scene.mood * 0.45) * (0.72 + (index % 6) * 0.09);
  const slot = Math.max(0.18, gap) * 1000;
  const cycle = Math.floor((scene.now + index * slot * 0.37) / slot);
  if (spec.cycle !== cycle) {
    const first = spec.cycle === undefined;
    spec.cycle = cycle;
    spec.born = scene.now - (first ? (index * 47) % 150 : 0);
  }
  const age = scene.now - spec.born;
  if (age < 0 || age > 150) return 0;
  return (1 - age / 150) * (0.72 + scene.mood * 0.5);
}

function strokeBolt(path, width, alpha) {
  if (alpha < 0.03) return;
  ctx.lineWidth = width + 2.4;
  ctx.strokeStyle = rgba(glowRgb, alpha * 0.22);
  ctx.stroke(path);
  ctx.lineWidth = Math.max(0.4, width * 0.4);
  ctx.strokeStyle = "rgba(255, 255, 255, " + Math.min(1, alpha) + ")";
  ctx.stroke(path);
}

function drawSphere(scene) {
  const hx = scene.cx - scene.radius * 0.28;
  const hy = scene.cy - scene.radius * 0.32;
  const body = ctx.createRadialGradient(hx, hy, scene.radius * 0.08, scene.cx, scene.cy, scene.radius);
  body.addColorStop(0, rgba(mixWhite(scene.active, 0.75), 0.62));
  body.addColorStop(0.38, rgba(scene.active, 0.28));
  body.addColorStop(0.74, rgba(scene.dark, 0.55));
  body.addColorStop(1, "rgba(2, 6, 16, 0.82)");
  ctx.globalCompositeOperation = "source-over";
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, scene.radius, 0, Math.PI * 2);
  ctx.fillStyle = body;
  ctx.fill();
}

function cutRing(scene) {
  const hole = scene.radius * 0.55;
  const grad = ctx.createRadialGradient(scene.cx, scene.cy, hole * 0.62, scene.cx, scene.cy, hole);
  grad.addColorStop(0, "rgba(0,0,0,1)");
  grad.addColorStop(0.7, "rgba(0,0,0,1)");
  grad.addColorStop(1, "rgba(0,0,0,0)");
  ctx.globalCompositeOperation = "destination-out";
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, hole, 0, Math.PI * 2);
  ctx.fill();
}

function drawHalo(scene) {
  const alpha = (0.12 + 0.16 * scene.mood + 0.08 * scene.mood * scene.pulse) * scene.glow;
  const reach = scene.radius * 1.55;
  const halo = ctx.createRadialGradient(scene.cx, scene.cy, scene.radius * 0.9, scene.cx, scene.cy, reach);
  halo.addColorStop(0, rgba(scene.active, 0));
  halo.addColorStop(0.42, rgba(scene.active, alpha));
  halo.addColorStop(1, rgba(scene.active, 0));
  ctx.globalCompositeOperation = "lighter";
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, reach, 0, Math.PI * 2);
  ctx.fillStyle = halo;
  ctx.fill();
}

function drawLightning(scene) {
  const cx = scene.cx;
  const cy = scene.cy;
  const radius = scene.radius;
  ctx.globalCompositeOperation = "lighter";
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  const ringTilt = 0.28 + Math.sin(scene.angle * 0.45) * 0.05;
  const ringBoost = 1 + 0.08 * scene.mood;
  strokeRing(cx, cy, radius * 0.74, radius * 0.6, ringTilt, 1.15 * ringBoost, 0.55 * scene.bright);
  strokeRing(cx, cy, radius * 0.46, radius * 0.37, ringTilt - 0.08, 1.2 * ringBoost, 0.7 * scene.bright);

  for (let index = 0; index < webs.length; index++) {
    const spec = webs[index];
    const life = boltLife(spec, scene, index, false);
    if (life < 0.03) continue;
    const paths = webPaths(spec, driftSpin(scene, spec.speed) + jitter(scene, index), cx, cy, radius);
    strokeBolt(paths.back, spec.width * 0.8, spec.gain * 0.28 * life * scene.bright);
    strokeBolt(paths.front, spec.width, spec.gain * life * scene.bright);
  }

  ctx.save();
  ctx.globalAlpha = Math.min(1, scene.bright);
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 1.04, 0, Math.PI * 2);
  ctx.clip();
  const bandHalf = radius * 11 / 98;
  const band = ctx.createLinearGradient(cx, cy - bandHalf, cx, cy + bandHalf);
  const bandEdge = mixWhite(glowRgb, 0.35);
  band.addColorStop(0, rgba(glowRgb, 0));
  band.addColorStop(0.38, rgba(bandEdge, 0.14 * scene.bright));
  band.addColorStop(0.5, "rgba(230, 252, 255, " + Math.min(1, (0.62 + scene.pulse * 0.12) * scene.bright) + ")");
  band.addColorStop(0.62, rgba(bandEdge, 0.14 * scene.bright));
  band.addColorStop(1, rgba(glowRgb, 0));
  ctx.fillStyle = band;
  ctx.fillRect(cx - radius, cy - bandHalf, radius * 2, bandHalf * 2);
  const flare = ctx.createLinearGradient(cx - radius, cy, cx + radius, cy);
  flare.addColorStop(0, "rgba(180, 240, 255, 0)");
  flare.addColorStop(0.12, "rgba(210, 248, 255, 0.15)");
  flare.addColorStop(0.38, "rgba(245, 254, 255, 0.85)");
  flare.addColorStop(0.5, "rgba(255, 255, 255, 1)");
  flare.addColorStop(0.62, "rgba(245, 254, 255, 0.85)");
  flare.addColorStop(0.88, "rgba(210, 248, 255, 0.15)");
  flare.addColorStop(1, "rgba(180, 240, 255, 0)");
  ctx.strokeStyle = flare;
  ctx.lineWidth = 1.05 + 0.3 * scene.mood;
  ctx.beginPath();
  ctx.moveTo(cx - radius * 0.98, cy);
  ctx.lineTo(cx + radius * 0.98, cy);
  ctx.stroke();
  ctx.restore();

  ctx.globalAlpha = Math.min(1, scene.bright);
  const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.16);
  bloom.addColorStop(0, "rgba(255, 255, 255, 0.95)");
  bloom.addColorStop(0.35, rgba(mixWhite(glowRgb, 0.55), 0.55));
  bloom.addColorStop(1, rgba(glowRgb, 0));
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.16, 0, Math.PI * 2);
  ctx.fill();

  for (let spark = 0; spark < 22; spark++) {
    const spec = webs[spark % webs.length];
    const point = spec.points[Math.min(spec.points.length - 1, 2 + (spark % 5))];
    const life = boltLife(spec, scene, spark, false);
    if (life < 0.05) continue;
    const projected = projectPoint(point, driftSpin(scene, spec.speed) + jitter(scene, spark), cx, cy, radius);
    if (projected.z < 0.05) continue;
    const twinkle = (0.35 + 0.65 * scene.pulse) * life;
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, spark % 4 === 0 ? 1.35 : 0.7, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(245, 254, 255, " + twinkle * scene.bright + ")";
    ctx.fill();
  }
}

function drawMist(scene) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, scene.radius * 0.98, 0, Math.PI * 2);
  ctx.clip();
  ctx.globalCompositeOperation = "lighter";
  for (let index = 0; index < puffs.length; index++) {
    const puff = puffs[index];
    const inner = index < 20;
    const projected = projectPoint(
      { theta: puff.theta, phi: puff.phi },
      driftSpin(scene, puff.drift * (inner ? 0.45 : 1)) + jitter(scene, index),
      scene.cx,
      scene.cy,
      scene.radius * (inner ? 0.46 : 0.78)
    );
    if (projected.z < -0.35) continue;
    const depth = 0.55 + 0.45 * Math.max(0, projected.z);
    const puffRadius = scene.radius * puff.size * depth;
    const alpha = (0.08 + 0.07 * depth) * scene.bright;
    const glow = ctx.createRadialGradient(projected.x, projected.y, 0, projected.x, projected.y, puffRadius);
    glow.addColorStop(0, rgba(scene.light, alpha));
    glow.addColorStop(0.45, rgba(scene.active, alpha * 0.45));
    glow.addColorStop(1, rgba(scene.active, 0));
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, puffRadius, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawNebula(scene) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, scene.radius * 0.98, 0, Math.PI * 2);
  ctx.clip();
  ctx.globalCompositeOperation = "lighter";
  for (let index = 0; index < clouds.length; index++) {
    const cloud = clouds[index];
    const projected = projectPoint(
      { theta: cloud.theta, phi: cloud.phi },
      driftSpin(scene, cloud.speed * 0.45) + jitter(scene, index),
      scene.cx,
      scene.cy,
      scene.radius * 0.5
    );
    const reach = scene.radius * cloud.reach;
    const tone = cloud.dark ? scene.dark : scene.light;
    const alpha = (cloud.dark ? 0.2 : 0.28) * scene.bright;
    const glow = ctx.createRadialGradient(projected.x, projected.y, reach * 0.04, projected.x, projected.y, reach);
    glow.addColorStop(0, rgba(tone, alpha));
    glow.addColorStop(0.5, rgba(scene.active, alpha * 0.4));
    glow.addColorStop(1, rgba(tone, 0));
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, reach, 0, Math.PI * 2);
    ctx.fill();
  }
  for (let index = 0; index < stars.length; index++) {
    const star = stars[index];
    const projected = projectPoint(star, driftSpin(scene, 1.15) + jitter(scene, index + 40), scene.cx, scene.cy, scene.radius * 0.86);
    if (projected.z < 0) continue;
    const twinkle = 0.12 + 0.28 * Math.abs(Math.sin(scene.now * 0.003 * (1 + scene.mood) + star.twinkle));
    ctx.fillStyle = "rgba(255, 255, 255, " + twinkle * scene.bright + ")";
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, 0.7, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawBolts(scene) {
  ctx.save();
  ctx.beginPath();
  ctx.arc(scene.cx, scene.cy, scene.radius * 0.98, 0, Math.PI * 2);
  ctx.clip();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (let index = 0; index < bolts.length; index++) {
    const spec = bolts[index];
    const life = boltLife(spec, scene, index + 20, true);
    if (life < 0.03) continue;
    const paths = webPaths(spec, driftSpin(scene, spec.speed) + jitter(scene, index + 20), scene.cx, scene.cy, scene.radius);
    strokeBolt(paths.back, spec.width * 0.8, spec.gain * 0.28 * life * scene.bright);
    strokeBolt(paths.front, spec.width, spec.gain * life * scene.bright);
  }
  ctx.restore();
}

function drawNebulaLightning(scene) {
  drawNebula(scene);
  drawBolts(scene);
}

function drawMysticSphere(scene) {
  // Interior of the Grok reference orb: soft volume, filaments, shells, equator flare.
  const cx = scene.cx;
  const cy = scene.cy;
  const radius = scene.radius;
  ctx.save();
  ctx.globalCompositeOperation = "lighter";

  // Soft volumetric fill (glass energy body)
  for (let index = 0; index < Math.min(puffs.length, 28); index++) {
    const puff = puffs[index];
    const projected = projectPoint(
      { theta: puff.theta, phi: puff.phi },
      driftSpin(scene, puff.drift * 0.55) + jitter(scene, index + 70),
      cx,
      cy,
      radius * (0.35 + 0.4 * (index % 5) / 5)
    );
    if (projected.z < -0.2) continue;
    const depth = 0.5 + 0.5 * Math.max(0, projected.z);
    const puffRadius = radius * puff.size * 1.35 * depth;
    const alpha = (0.05 + 0.06 * depth) * scene.bright;
    const glow = ctx.createRadialGradient(projected.x, projected.y, 0, projected.x, projected.y, puffRadius);
    glow.addColorStop(0, rgba(scene.light, alpha));
    glow.addColorStop(0.55, rgba(scene.active, alpha * 0.4));
    glow.addColorStop(1, rgba(scene.active, 0));
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, puffRadius, 0, Math.PI * 2);
    ctx.fill();
  }

  // Neural / filament energy (wispy lightning inside)
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (let index = 0; index < webs.length; index++) {
    const spec = webs[index];
    const life = boltLife(spec, scene, index + 11, false);
    if (life < 0.04) continue;
    const paths = webPaths(
      spec,
      driftSpin(scene, spec.speed * 0.85) + jitter(scene, index + 11),
      cx,
      cy,
      radius * 0.92
    );
    strokeBolt(paths.back, spec.width * 0.55, spec.gain * 0.18 * life * scene.bright);
    strokeBolt(paths.front, spec.width * 0.85, spec.gain * 0.75 * life * scene.bright);
  }

  // Concentric energy shells
  const shellTilt = 0.34 + Math.sin(scene.angle * 0.5) * 0.04;
  strokeRing(cx, cy, radius * 0.82, radius * 0.68, shellTilt, 1.05, 0.42 * scene.bright);
  strokeRing(cx, cy, radius * 0.58, radius * 0.46, shellTilt - 0.1, 1.1, 0.5 * scene.bright);
  strokeRing(cx, cy, radius * 0.34, radius * 0.28, shellTilt + 0.08, 1.0, 0.38 * scene.bright);

  // Strong horizontal equator flare (signature of the reference)
  const bandHalf = radius * 0.14;
  const band = ctx.createLinearGradient(cx, cy - bandHalf, cx, cy + bandHalf);
  band.addColorStop(0, rgba(glowRgb, 0));
  band.addColorStop(0.35, rgba(mixWhite(glowRgb, 0.4), 0.18 * scene.bright));
  band.addColorStop(0.5, "rgba(230, 252, 255, " + Math.min(1, (0.55 + scene.pulse * 0.2) * scene.bright) + ")");
  band.addColorStop(0.65, rgba(mixWhite(glowRgb, 0.4), 0.18 * scene.bright));
  band.addColorStop(1, rgba(glowRgb, 0));
  ctx.fillStyle = band;
  ctx.fillRect(cx - radius * 1.05, cy - bandHalf, radius * 2.1, bandHalf * 2);

  const flare = ctx.createLinearGradient(cx - radius * 1.15, cy, cx + radius * 1.15, cy);
  flare.addColorStop(0, "rgba(180, 240, 255, 0)");
  flare.addColorStop(0.18, "rgba(210, 248, 255, 0.2)");
  flare.addColorStop(0.45, "rgba(255, 255, 255, 0.95)");
  flare.addColorStop(0.5, "rgba(255, 255, 255, 1)");
  flare.addColorStop(0.55, "rgba(255, 255, 255, 0.95)");
  flare.addColorStop(0.82, "rgba(210, 248, 255, 0.2)");
  flare.addColorStop(1, "rgba(180, 240, 255, 0)");
  ctx.strokeStyle = flare;
  ctx.lineWidth = 1.4 + 0.5 * scene.mood + 0.4 * scene.pulse;
  ctx.beginPath();
  ctx.moveTo(cx - radius * 1.08, cy);
  ctx.lineTo(cx + radius * 1.08, cy);
  ctx.stroke();

  // Bright core nucleus
  const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.22);
  bloom.addColorStop(0, "rgba(255, 255, 255, 0.98)");
  bloom.addColorStop(0.3, rgba(mixWhite(glowRgb, 0.6), 0.65));
  bloom.addColorStop(1, rgba(glowRgb, 0));
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.22, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawMysticSphereExterior(scene) {
  // Gyro rings + holographic pedestal from the Grok reference (outside the orb clip).
  const cx = scene.cx;
  const cy = scene.cy;
  const radius = scene.radius;
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineCap = "round";

  // Orbital gyroscope rings
  const spin = scene.angle * 0.7;
  strokeRing(cx, cy, radius * 1.18, radius * 0.42, spin * 0.35, 0.9, 0.28 * scene.bright);
  strokeRing(cx, cy, radius * 1.05, radius * 0.95, Math.PI / 2 + spin * 0.2, 0.75, 0.22 * scene.bright);
  strokeRing(cx, cy, radius * 1.28, radius * 0.28, -spin * 0.25, 0.7, 0.18 * scene.bright);

  // Dotted orbital ticks
  for (let i = 0; i < 36; i++) {
    const a = spin * 0.4 + (i / 36) * Math.PI * 2;
    const x = cx + Math.cos(a) * radius * 1.22;
    const y = cy + Math.sin(a) * radius * 0.38;
    ctx.beginPath();
    ctx.arc(x, y, i % 3 === 0 ? 1.2 : 0.6, 0, Math.PI * 2);
    ctx.fillStyle = rgba(mixWhite(glowRgb, 0.55), (0.25 + 0.35 * scene.pulse) * scene.bright);
    ctx.fill();
  }

  // Pedestal: concentric floor rings + upright beam
  const baseY = cy + radius * 1.22;
  for (let ring = 0; ring < 4; ring++) {
    const rx = radius * (0.55 + ring * 0.22);
    const ry = rx * 0.22;
    ctx.beginPath();
    ctx.ellipse(cx, baseY, rx, ry, 0, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(scene.active, (0.28 - ring * 0.05) * scene.bright);
    ctx.lineWidth = 1.1;
    ctx.stroke();
  }
  const beam = ctx.createLinearGradient(cx, cy + radius * 0.85, cx, baseY);
  beam.addColorStop(0, rgba(mixWhite(glowRgb, 0.5), 0.55 * scene.bright));
  beam.addColorStop(1, rgba(glowRgb, 0));
  ctx.strokeStyle = beam;
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  ctx.moveTo(cx, cy + radius * 0.9);
  ctx.lineTo(cx, baseY);
  ctx.stroke();

  // Soft ground bloom
  const floor = ctx.createRadialGradient(cx, baseY, 0, cx, baseY, radius * 1.1);
  floor.addColorStop(0, rgba(scene.active, 0.18 * scene.bright));
  floor.addColorStop(1, rgba(scene.active, 0));
  ctx.fillStyle = floor;
  ctx.beginPath();
  ctx.ellipse(cx, baseY, radius * 1.1, radius * 0.28, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawAetherRing(scene) {
  // Hollow glowing ring with inner blades, dust, and bokeh (voice-orb reference).
  const cx = scene.cx;
  const cy = scene.cy;
  const radius = scene.radius;
  ctx.save();
  ctx.globalCompositeOperation = "lighter";

  // Soft outer bloom
  const bloom = ctx.createRadialGradient(cx, cy, radius * 0.55, cx, cy, radius * 1.45);
  bloom.addColorStop(0, rgba(scene.active, 0));
  bloom.addColorStop(0.55, rgba(scene.active, 0.18 * scene.bright));
  bloom.addColorStop(1, rgba(scene.active, 0));
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 1.45, 0, Math.PI * 2);
  ctx.fill();

  // Inner sweeping blades (keep hollow core)
  for (let index = 0; index < aetherBlades.length; index++) {
    const blade = aetherBlades[index];
    const start = blade.angle + driftSpin(scene, blade.speed);
    const end = start + blade.sweep;
    const inner = radius * (0.28 + blade.width);
    const mid = radius * 0.62;
    const outer = radius * 0.92;
    ctx.beginPath();
    ctx.arc(cx, cy, outer, start, end, false);
    ctx.arc(cx, cy, inner, end, start, true);
    ctx.closePath();
    const grad = ctx.createRadialGradient(cx, cy, inner, cx, cy, outer);
    grad.addColorStop(0, rgba(scene.active, 0));
    grad.addColorStop(0.35, rgba(mixWhite(scene.active, 0.25), blade.alpha * scene.bright));
    grad.addColorStop(0.75, rgba(scene.light, (blade.alpha + 0.08) * scene.bright));
    grad.addColorStop(1, rgba(scene.active, 0));
    ctx.fillStyle = grad;
    ctx.fill();
    // Bright leading edge
    ctx.beginPath();
    ctx.arc(cx, cy, mid, start, start + 0.12);
    ctx.strokeStyle = rgba(mixWhite(scene.active, 0.7), (0.35 + 0.25 * scene.pulse) * scene.bright);
    ctx.lineWidth = 2.2;
    ctx.stroke();
  }

  // Thick luminous torus rim
  for (let pass = 0; pass < 3; pass++) {
    const rimR = radius * (0.86 + pass * 0.04);
    const rim = ctx.createRadialGradient(cx - radius * 0.15, cy - radius * 0.2, radius * 0.1, cx, cy, rimR + radius * 0.18);
    rim.addColorStop(0, rgba(mixWhite(scene.active, 0.55), 0));
    rim.addColorStop(0.72, rgba(scene.active, (0.08 + pass * 0.05) * scene.bright));
    rim.addColorStop(0.9, rgba(mixWhite(scene.active, 0.45), (0.45 - pass * 0.08) * scene.bright));
    rim.addColorStop(1, rgba(scene.active, 0));
    ctx.beginPath();
    ctx.arc(cx, cy, rimR + radius * 0.12, 0, Math.PI * 2);
    ctx.arc(cx, cy, rimR - radius * 0.1, 0, Math.PI * 2, true);
    ctx.fillStyle = rim;
    ctx.fill();
  }
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.9, 0, Math.PI * 2);
  ctx.strokeStyle = rgba(mixWhite(scene.active, 0.65), (0.55 + 0.2 * scene.pulse) * scene.bright);
  ctx.lineWidth = 3.2 + scene.mood;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.78, 0, Math.PI * 2);
  ctx.strokeStyle = rgba(scene.active, 0.28 * scene.bright);
  ctx.lineWidth = 1.4;
  ctx.stroke();

  // Dust + bokeh
  for (let index = 0; index < aetherDust.length; index++) {
    const dust = aetherDust[index];
    const a = dust.angle + driftSpin(scene, dust.speed) * (dust.bokeh ? 0.35 : 1);
    const rr = radius * dust.radius;
    const x = cx + Math.cos(a) * rr;
    const y = cy + Math.sin(a) * rr * (dust.bokeh ? 0.92 : 1);
    const twinkle = 0.35 + 0.65 * Math.abs(Math.sin(scene.now * 0.003 + dust.twinkle));
    const size = dust.size * (dust.bokeh ? (0.8 + 0.4 * scene.pulse) : 1);
    if (dust.bokeh) {
      const soft = ctx.createRadialGradient(x, y, 0, x, y, size * 2.2);
      soft.addColorStop(0, rgba(mixWhite(scene.active, 0.4), 0.35 * twinkle * scene.bright));
      soft.addColorStop(1, rgba(scene.active, 0));
      ctx.fillStyle = soft;
      ctx.beginPath();
      ctx.arc(x, y, size * 2.2, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(x, y, size * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = rgba(mixWhite(scene.active, 0.55), twinkle * 0.85 * scene.bright);
      ctx.fill();
    }
  }
  ctx.restore();
}

function drawNeuralMesh(scene) {
  // JARVIS-like neural point cloud + spokes + data arcs.
  const cx = scene.cx;
  const cy = scene.cy;
  const radius = scene.radius;
  ctx.save();
  ctx.globalCompositeOperation = "lighter";

  // Dim volumetric body (not solid glass)
  const body = ctx.createRadialGradient(cx - radius * 0.2, cy - radius * 0.25, radius * 0.05, cx, cy, radius);
  body.addColorStop(0, rgba(mixWhite(scene.active, 0.55), 0.22 * scene.bright));
  body.addColorStop(0.45, rgba(scene.active, 0.1 * scene.bright));
  body.addColorStop(1, rgba(scene.dark, 0.08));
  ctx.globalCompositeOperation = "source-over";
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = body;
  ctx.fill();
  ctx.globalCompositeOperation = "lighter";

  // Concentric orbital rings at varied tilts
  strokeRing(cx, cy, radius * 0.95, radius * 0.42, scene.angle * 0.25, 0.7, 0.22 * scene.bright);
  strokeRing(cx, cy, radius * 0.72, radius * 0.72, Math.PI / 2 + scene.angle * 0.15, 0.65, 0.18 * scene.bright);
  strokeRing(cx, cy, radius * 0.55, radius * 0.28, -scene.angle * 0.3, 0.6, 0.2 * scene.bright);
  strokeRing(cx, cy, radius * 0.38, radius * 0.38, scene.angle * 0.5, 0.55, 0.16 * scene.bright);

  // Radial neural spokes
  ctx.lineCap = "round";
  for (let index = 0; index < neuralSpokes.length; index++) {
    const spoke = neuralSpokes[index];
    const projected = projectPoint(
      { theta: spoke.theta, phi: spoke.phi },
      driftSpin(scene, spoke.speed),
      cx,
      cy,
      radius * 0.92
    );
    if (projected.z < -0.15) continue;
    const depth = 0.4 + 0.6 * Math.max(0, projected.z);
    const pulse = 0.5 + 0.5 * Math.sin(scene.now * 0.004 + index);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(projected.x, projected.y);
    ctx.strokeStyle = rgba(scene.active, spoke.gain * depth * pulse * scene.bright);
    ctx.lineWidth = 0.6 + depth;
    ctx.stroke();
  }

  // Dense point cloud
  for (let index = 0; index < neuralPoints.length; index++) {
    const point = neuralPoints[index];
    const projected = projectPoint(
      { theta: point.theta, phi: point.phi },
      driftSpin(scene, point.speed),
      cx,
      cy,
      radius * (point.shell ? 0.98 : 0.78)
    );
    if (projected.z < -0.35) continue;
    const depth = 0.35 + 0.65 * Math.max(0, projected.z);
    const twinkle = 0.4 + 0.6 * Math.abs(Math.sin(scene.now * 0.005 + point.twinkle));
    const size = point.size * depth * (point.shell ? 1.15 : 0.9);
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, size * 0.45, 0, Math.PI * 2);
    ctx.fillStyle = rgba(
      mixWhite(scene.active, point.shell ? 0.55 : 0.25),
      twinkle * depth * scene.bright
    );
    ctx.fill();
  }

  // Outer fragmented data blocks / arcs
  for (let index = 0; index < neuralBlocks.length; index++) {
    const block = neuralBlocks[index];
    const spin = driftSpin(scene, block.speed);
    const a0 = block.theta + spin;
    const projected = projectPoint(
      { theta: block.theta, phi: block.phi },
      spin,
      cx,
      cy,
      radius * 1.02
    );
    if (projected.z < 0) continue;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * (0.92 + (index % 3) * 0.04), a0, a0 + block.arc);
    ctx.strokeStyle = rgba(mixWhite(scene.active, 0.4), 0.35 * Math.max(0.2, projected.z) * scene.bright);
    ctx.lineWidth = 1.4 + (index % 3) * 0.5;
    ctx.stroke();
  }

  // Bright neural core
  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.28);
  core.addColorStop(0, "rgba(255, 255, 255, 0.95)");
  core.addColorStop(0.25, rgba(mixWhite(scene.active, 0.65), 0.7));
  core.addColorStop(1, rgba(scene.active, 0));
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.28, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

const drawStyle = {
  lightning: drawLightning,
  mist: drawMist,
  nebula: drawNebula,
  "nebula+lightning": drawNebulaLightning,
  "mystic sphere": drawMysticSphere,
  "aether ring": drawAetherRing,
  "neural mesh": drawNeuralMesh,
};

const hollowStyles = {
  "aether ring": 1,
};

function draw() {
  if (stopped) return;
  const cfg = readConfig();
  applySize(cfg.size);
  const now = performance.now();
  let dt = lastTime ? (now - lastTime) / 1000 : 0.016;
  if (dt > 0.05) dt = 0.05;
  if (dt < 0) dt = 0;
  lastTime = now;
  const thinking = (window.__energyOrbMode || mode) === "thinking";
  const target = thinking ? 1 : 0;
  mood += (target - mood) * (1 - Math.exp(-dt / 0.4));
  if (Math.abs(target - mood) < 0.001) mood = target;
  glowRgb = mixRgb(hexToRgb(cfg.calm), hexToRgb(cfg.thinking), mood);
  const liveLabel = document.querySelector("#energy-orb-host .orb-state");
  if (liveLabel) {
    liveLabel.textContent = mood >= 0.5 ? "THINKING" : "CALM";
    liveLabel.style.color = rgbToHex(glowRgb);
  }
  angle += (0.35 + 0.6 * mood) * cfg.spin * dt;
  const cx = viewW / 2;
  const cy = viewH / 2;
  const breath = Math.sin(now * 0.001 * Math.PI * 2 / 4);
  const radius = (viewW * 98) / 360 * (1 + 0.03 * (1 - mood * 0.45) * breath * cfg.pulseAmt);
  const pulse = 0.5 + 0.5 * Math.sin(now * 0.001 * (1.4 + mood * 1.8));
  const bright = (1 + 0.35 * mood) * cfg.glowAmt;
  const scene = {
    cx: cx,
    cy: cy,
    radius: radius,
    angle: angle,
    pulse: pulse,
    thinking: thinking,
    bright: bright,
    mood: mood,
    swirl: 1 + mood * 0.6,
    now: now,
    dt: dt,
    turbulence: cfg.turbulence,
    glow: cfg.glowAmt,
    shape: cfg.shape,
    active: glowRgb,
    light: mixWhite(glowRgb, 0.5),
    dark: shade(glowRgb, 0.4),
  };
  ctx.clearRect(0, 0, viewW, viewH);
  ctx.globalCompositeOperation = "source-over";
  ctx.shadowBlur = 0;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.save();
  ctx.translate(cx, cy);
  if (cfg.shape === "oval") ctx.scale(1, 0.8);
  ctx.translate(-cx, -cy);
  const hollow = !!hollowStyles[cfg.style];
  ctx.save();
  if (!hollow) {
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.clip();
    drawSphere(scene);
  }

  const paint = drawStyle[cfg.style] || drawLightning;
  paint(scene);

  if (!hollow) {
    ctx.globalCompositeOperation = "source-over";
    ctx.shadowBlur = 0;
    ctx.beginPath();
    ctx.arc(cx, cy, radius - 0.4, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(mixWhite(glowRgb, 0.65), (0.35 + pulse * 0.12) * cfg.glowAmt);
    ctx.lineWidth = 1.15;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 1.2, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(glowRgb, (0.16 + 0.14 * mood + pulse * 0.06) * cfg.glowAmt);
    ctx.lineWidth = 2.4;
    ctx.stroke();
    if (cfg.shape === "ring") cutRing(scene);
  }
  ctx.restore();
  if (cfg.style === "mystic sphere") drawMysticSphereExterior(scene);
  drawHalo(scene);
  ctx.restore();

  element._orbAngle = angle;
  window.__energyOrbFrames = (window.__energyOrbFrames || 0) + 1;
  frame = requestAnimationFrame(draw);
}
draw();
"""

ORB_CSS = """
html, body {
  background: #05070d !important;
  color-scheme: dark;
}
.gradio-container,
.gradio-container.light,
.gradio-container.dark,
.gradio-container .main,
.gradio-container .contain,
.gradio-container .tabs,
.gradio-container .tabitem {
  background: #05070d !important;
  color: #d7eaf6;
}
.gradio-container .block,
.gradio-container .form,
.gradio-container .panel,
.gradio-container .gap {
  background: #0c121c;
  border-color: #163044;
  color: #d7eaf6;
}
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container label,
.gradio-container p,
.gradio-container span,
.gradio-container li {
  color: #d7eaf6;
}
.gradio-container a { color: #67e8f9; }
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
  color: #e7f6ff !important;
  background: #080d16 !important;
  border-color: #16485f !important;
}
.gradio-container .tab-nav button { color: #9fdfff !important; }
.gradio-container .tab-nav button.selected {
  color: #f3fdff !important;
  border-color: #22d3ee !important;
}
.gradio-container footer, footer {
  background: #05070d !important;
}
#energy-orb-host,
#energy-orb-host .html-container {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#energy-orb-host .energy-orb {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 380px;
}
#orb-config-host,
#orb-config-host .html-container {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  overflow: hidden !important;
  background: transparent !important;
}
#chat-stage {
  position: relative;
  min-height: 420px;
}
#chat-toolbar {
  position: absolute;
  top: 8px;
  right: 12px;
  z-index: 50;
  width: auto !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#chat-toolbar .form,
#chat-toolbar .block {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#orb-settings-btn button,
#orb-settings-btn {
  min-width: 42px !important;
  width: 42px !important;
  height: 42px !important;
  border-radius: 999px !important;
  border: 1px solid #1f6f8f !important;
  background: #0a1522 !important;
  color: #9fdfff !important;
  font-size: 18px !important;
  line-height: 1 !important;
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.15);
}
#orb-settings-panel {
  position: absolute;
  top: 56px;
  right: 12px;
  z-index: 60;
  width: min(420px, calc(100% - 24px));
  max-height: min(78vh, 640px);
  overflow-x: hidden;
  overflow-y: auto;
  padding: 14px 14px 10px !important;
  border: 1px solid #1f6f8f !important;
  border-radius: 14px !important;
  background: rgba(8, 14, 22, 0.97) !important;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}
#orb-settings-panel .block,
#orb-settings-panel .form,
#orb-settings-panel .panel {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-top: 0 !important;
  margin-bottom: 8px !important;
}
#orb-settings-panel .gap {
  gap: 8px !important;
}
#orb-settings-panel label,
#orb-settings-panel .label-wrap span {
  font-size: 11px !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #7eb7d4 !important;
}
#orb-settings-panel .orb-panel-title {
  margin: 0 0 10px 0 !important;
  font-size: 13px !important;
  font-weight: 600;
  color: #d7eaf6 !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
#orb-settings-panel .orb-section-label {
  margin: 10px 0 4px 0 !important;
  font-size: 11px !important;
  color: #67e8f9 !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
#orb-settings-panel button {
  min-height: 30px !important;
  height: 30px !important;
  padding: 0 10px !important;
  font-size: 12px !important;
  border-radius: 8px !important;
  border: 1px solid #1f6f8f !important;
  background: #0d1a28 !important;
  color: #c8e7f7 !important;
}
#orb-settings-panel #orb-preset-actions button {
  min-width: 0 !important;
  flex: 1 1 0 !important;
}
#orb-settings-panel input,
#orb-settings-panel textarea,
#orb-settings-panel select {
  min-height: 32px !important;
  font-size: 13px !important;
}
#orb-settings-panel input[type="range"] {
  min-height: 18px !important;
}
#orb-settings-panel .svelte-color-picker,
#orb-settings-panel [data-testid="color-picker"] {
  min-height: 32px !important;
}
#energy-orb-host canvas {
  display: block;
}
#energy-orb-host .orb-state {
  margin-top: 2px;
  font-family: ui-monospace, Consolas, monospace;
  letter-spacing: 0.42em;
  font-size: 12px;
  color: #7ee7ff;
}
#agent-chat { background: transparent !important; }
"""

ORB_THEME = gr.themes.Base(
    primary_hue="cyan",
    secondary_hue="sky",
    neutral_hue="slate",
).set(
    body_background_fill=VOID,
    body_background_fill_dark=VOID,
    body_text_color="#d7eaf6",
    body_text_color_dark="#d7eaf6",
    body_text_color_subdued="#8fb4c9",
    body_text_color_subdued_dark="#8fb4c9",
    background_fill_primary=VOID,
    background_fill_primary_dark=VOID,
    background_fill_secondary="#0c121c",
    background_fill_secondary_dark="#0c121c",
    block_background_fill="#0c121c",
    block_background_fill_dark="#0c121c",
    block_border_color="#163044",
    block_border_color_dark="#163044",
    block_label_text_color="#9fdfff",
    block_label_text_color_dark="#9fdfff",
    block_title_text_color="#d7eaf6",
    block_title_text_color_dark="#d7eaf6",
    panel_background_fill="#0c121c",
    panel_background_fill_dark="#0c121c",
    panel_border_color="#163044",
    panel_border_color_dark="#163044",
    border_color_primary="#164e63",
    border_color_primary_dark="#164e63",
    border_color_accent="#22d3ee",
    border_color_accent_dark="#22d3ee",
    color_accent="#67e8f9",
    color_accent_soft="#083344",
    color_accent_soft_dark="#083344",
    link_text_color="#67e8f9",
    link_text_color_dark="#67e8f9",
    input_background_fill="#080d16",
    input_background_fill_dark="#080d16",
    input_background_fill_focus="#080d16",
    input_background_fill_focus_dark="#080d16",
    input_border_color="#16485f",
    input_border_color_dark="#16485f",
    input_border_color_focus="#22d3ee",
    input_border_color_focus_dark="#22d3ee",
    input_placeholder_color="#6f93a8",
    input_placeholder_color_dark="#6f93a8",
    button_primary_background_fill="#0e7490",
    button_primary_background_fill_dark="#0e7490",
    button_primary_background_fill_hover="#0891b2",
    button_primary_background_fill_hover_dark="#0891b2",
    button_primary_text_color="#e8fbff",
    button_primary_text_color_dark="#e8fbff",
    button_primary_border_color="#155e75",
    button_primary_border_color_dark="#155e75",
    button_secondary_background_fill="#122033",
    button_secondary_background_fill_dark="#122033",
    button_secondary_background_fill_hover="#163044",
    button_secondary_background_fill_hover_dark="#163044",
    button_secondary_text_color="#d7f6ff",
    button_secondary_text_color_dark="#d7f6ff",
    button_secondary_border_color="#1d4e63",
    button_secondary_border_color_dark="#1d4e63",
    shadow_drop="none",
    shadow_drop_lg="none",
)



def current_settings():
    data = load_settings()
    return data.get("security_level") or "OFFICIAL", data.get("jira_url") or ""


def save_settings(level, jira_base_url):
    level = (level or "").strip()
    url = (jira_base_url or "").strip()
    if level not in LEVELS:
        return "Invalid security level."
    if url and not (url.startswith("https://") or url.startswith("http://")):
        return "Jira URL must start with http:// or https://."
    update_setting("security_level", level, confirm=True)
    update_setting("jira_url", url, confirm=True)
    return "Saved."


def _report_json(md_path: Path):
    path = md_path.with_suffix(".json")
    if not path.is_file():
        return "No JSON found"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "No JSON found"


def latest_report():
    try:
        folder = reports_dir()
    except Exception:
        return "No reports yet", None, "No JSON found"
    if not folder.exists():
        return "No reports yet", None, "No JSON found"
    files = sorted(folder.glob("*.md"), key=lambda path: path.stat().st_mtime)
    if not files:
        return "No reports yet", None, "No JSON found"
    newest = files[-1]
    text = newest.read_text(encoding="utf-8")
    shot = None
    for line in text.splitlines():
        if line.startswith("Screenshot:"):
            candidate = Path(line.split(":", 1)[1].strip())
            if candidate.is_file():
                shot = str(candidate)
            break
    return text, shot, _report_json(newest)


def refresh_report():
    """gr.JSON rejects a plain sentence, so the missing-file message is wrapped."""
    text, shot, payload = latest_report()
    if isinstance(payload, str):
        payload = {"message": payload}
    return text, shot, payload


def new_session_id():
    return str(uuid.uuid4())


def respond(message, history, session_id):
    if not session_id:
        session_id = new_session_id()
    response = httpx.post(
        CHAT_URL,
        json={"message": message, "session_id": session_id},
        timeout=180.0,
    )
    response.raise_for_status()
    return response.json().get("reply") or "No response."


class LocalApp(gr.Blocks):
    """Gradio 6 reads analytics on the app, not on launch()."""

    def launch(self, analytics_enabled=False, **kwargs):
        self.analytics_enabled = analytics_enabled
        return super().launch(**kwargs)


with LocalApp(title="AI Testing Agent", analytics_enabled=False) as demo:
    with gr.Tabs():
        with gr.Tab("Chat"):
            _orb = current_orb_config()
            with gr.Column(elem_id="chat-stage"):
                orb_config_host = gr.HTML(
                    orb_config_markup(_orb),
                    elem_id="orb-config-host",
                    apply_default_css=False,
                    padding=False,
                    container=False,
                )
                with gr.Row(elem_id="chat-toolbar"):
                    orb_settings_open = gr.State(False)
                    orb_settings_btn = gr.Button(
                        "\u2699",
                        elem_id="orb-settings-btn",
                        scale=0,
                        min_width=42,
                    )
                gr.HTML(
                    ORB_HTML,
                    elem_id="energy-orb-host",
                    js_on_load=ORB_JS,
                    apply_default_css=False,
                    padding=False,
                    container=False,
                )
                _preset_names = list_orb_preset_names()
                _active_preset = load_settings().get("orb_active_preset") or None
                if _active_preset not in _preset_names:
                    _active_preset = None
                _preset_choices = _preset_names if _preset_names else ["(none yet)"]
                with gr.Column(visible=False, elem_id="orb-settings-panel") as orb_settings_panel:
                    gr.HTML('<div class="orb-panel-title">Orb</div>')
                    gr.HTML('<div class="orb-section-label">Presets</div>')
                    with gr.Row(equal_height=True):
                        orb_preset = gr.Dropdown(
                            choices=_preset_choices,
                            value=_active_preset if _active_preset else _preset_choices[0],
                            label="Saved",
                            scale=3,
                        )
                        orb_preset_name = gr.Textbox(
                            value="",
                            label="New name",
                            placeholder="my look",
                            scale=2,
                        )
                    with gr.Row(elem_id="orb-preset-actions", equal_height=True):
                        orb_preset_save = gr.Button("Save", size="sm")
                        orb_preset_load = gr.Button("Load", size="sm")
                        orb_preset_delete = gr.Button("Delete", size="sm")
                    orb_preset_status = gr.Textbox(
                        value="Ready",
                        label="Status",
                        interactive=False,
                        max_lines=1,
                    )
                    gr.HTML('<div class="orb-section-label">Look</div>')
                    with gr.Row(equal_height=True):
                        orb_style = gr.Dropdown(
                            choices=list(ORB_STYLES),
                            value=_orb["style"],
                            label="Style",
                            scale=2,
                        )
                        orb_shape = gr.Dropdown(
                            choices=list(ORB_SHAPES),
                            value=_orb["shape"],
                            label="Shape",
                            scale=1,
                        )
                    with gr.Row(equal_height=True):
                        orb_calm = gr.ColorPicker(value=_orb["calm_color"], label="Calm")
                        orb_thinking = gr.ColorPicker(value=_orb["thinking_color"], label="Thinking")
                    orb_size = gr.Slider(
                        minimum=200,
                        maximum=480,
                        step=20,
                        value=_orb["size"],
                        label="Size",
                    )
                    gr.HTML('<div class="orb-section-label">Motion</div>')
                    with gr.Row(equal_height=True):
                        orb_spin = gr.Slider(
                            minimum=0, maximum=2, step=0.1, value=_orb["spin_speed"], label="Spin"
                        )
                        orb_turbulence = gr.Slider(
                            minimum=0, maximum=2, step=0.1, value=_orb["turbulence"], label="Turbulence"
                        )
                    with gr.Row(equal_height=True):
                        orb_pulse = gr.Slider(
                            minimum=0, maximum=2, step=0.1, value=_orb["pulse"], label="Pulse"
                        )
                        orb_glow = gr.Slider(
                            minimum=0, maximum=2, step=0.1, value=_orb["glow"], label="Glow"
                        )
                orb_settings_btn.click(
                    toggle_orb_settings,
                    [orb_settings_open],
                    [orb_settings_open, orb_settings_panel],
                )
            orb_inputs = [orb_style, orb_calm, orb_thinking, orb_size, orb_shape, orb_spin, orb_turbulence, orb_pulse, orb_glow]
            for orb_control in orb_inputs:
                orb_control.change(save_orb_config, orb_inputs, orb_config_host)
            orb_preset_save.click(
                save_orb_preset,
                [orb_preset_name] + orb_inputs,
                [orb_config_host, orb_preset, orb_preset_status],
            )
            orb_preset_load.click(
                load_orb_preset,
                [orb_preset],
                [orb_config_host] + orb_inputs + [orb_preset_status],
            )
            orb_preset_delete.click(
                delete_orb_preset,
                [orb_preset],
                [orb_preset, orb_preset_status],
            )
            with gr.Column(elem_id="agent-chat"):
                session_id = gr.State(new_session_id)
                gr.ChatInterface(
                    respond,
                    additional_inputs=[session_id],
                    chatbot=gr.Chatbot(height=340, render=False),
                    title="AI Testing Agent",
                    analytics_enabled=False,
                    fill_height=False,
                )
        with gr.Tab("Settings"):
            loaded_level, loaded_url = current_settings()
            level = gr.Dropdown(choices=list(LEVELS), value=loaded_level, label="security_level")
            jira_base_url = gr.Textbox(value=loaded_url, label="jira_base_url")
            status = gr.Textbox(label="Status", interactive=False)
            gr.Button("Save").click(save_settings, [level, jira_base_url], status)
        with gr.Tab("Reports"):
            report_md = gr.Markdown("No reports yet")
            report_image = gr.Image(label="Screenshot")
            with gr.Accordion("Raw JSON", open=False):
                report_json = gr.JSON(value={"message": "No JSON found"})
            gr.Button("Refresh").click(refresh_report, outputs=[report_md, report_image, report_json])
    demo.load(current_settings, outputs=[level, jira_base_url])
    demo.load(current_orb_inputs, outputs=orb_inputs)

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        share=False,
        analytics_enabled=False,
        theme=ORB_THEME,
        css=ORB_CSS,
    )
