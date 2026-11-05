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
ORB_STYLES = ("lightning", "mist", "nebula", "nebula+lightning")
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
  if (style !== "lightning" && style !== "mist" && style !== "nebula" && style !== "nebula+lightning") {
    style = "lightning";
  }
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

const drawStyle = {
  lightning: drawLightning,
  mist: drawMist,
  nebula: drawNebula,
  "nebula+lightning": drawNebulaLightning,
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
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.clip();
  drawSphere(scene);

  const paint = drawStyle[cfg.style] || drawLightning;
  paint(scene);

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
  ctx.restore();
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
            orb_config_host = gr.HTML(
                orb_config_markup(_orb),
                elem_id="orb-config-host",
                apply_default_css=False,
                padding=False,
                container=False,
            )
            gr.HTML(
                ORB_HTML,
                elem_id="energy-orb-host",
                js_on_load=ORB_JS,
                apply_default_css=False,
                padding=False,
                container=False,
            )
            # Presets sit above the style accordion so they always render even if
            # Accordion/Markdown quirks hit older Gradio builds.
            _preset_names = list_orb_preset_names()
            _active_preset = load_settings().get("orb_active_preset") or None
            if _active_preset not in _preset_names:
                _active_preset = None
            _preset_choices = _preset_names if _preset_names else ["(none yet)"]
            orb_preset = gr.Dropdown(
                choices=_preset_choices,
                value=_active_preset if _active_preset else _preset_choices[0],
                label="preset",
            )
            orb_preset_name = gr.Textbox(value="", label="preset name", placeholder="my look")
            with gr.Row():
                orb_preset_save = gr.Button("Save preset")
                orb_preset_load = gr.Button("Load preset")
                orb_preset_delete = gr.Button("Delete preset")
            orb_preset_status = gr.Textbox(
                value="Ready - enter a name and click Save preset",
                label="preset status",
                interactive=False,
            )
            with gr.Accordion("Orb style", open=True):
                orb_style = gr.Dropdown(choices=list(ORB_STYLES), value=_orb["style"], label="style")
                orb_calm = gr.ColorPicker(value=_orb["calm_color"], label="calm")
                orb_thinking = gr.ColorPicker(value=_orb["thinking_color"], label="thinking")
                orb_size = gr.Slider(minimum=200, maximum=480, step=20, value=_orb["size"], label="size")
                orb_shape = gr.Dropdown(choices=list(ORB_SHAPES), value=_orb["shape"], label="shape")
                orb_spin = gr.Slider(minimum=0, maximum=2, step=0.1, value=_orb["spin_speed"], label="spin_speed")
                orb_turbulence = gr.Slider(minimum=0, maximum=2, step=0.1, value=_orb["turbulence"], label="turbulence")
                orb_pulse = gr.Slider(minimum=0, maximum=2, step=0.1, value=_orb["pulse"], label="pulse")
                orb_glow = gr.Slider(minimum=0, maximum=2, step=0.1, value=_orb["glow"], label="glow")
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
