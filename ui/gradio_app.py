"""Minimal local Gradio chat client. Talks to the FastAPI agent on port 8000."""
import json
import os
import sys
import uuid
from pathlib import Path

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr
import httpx
from reports.exporter import reports_dir
from settings.store import load_settings, update_setting

CHAT_URL = "http://127.0.0.1:8000/chat"
LEVELS = ("OFFICIAL", "SECRET")
VOID = "#05070d"

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
const viewW = 360;
const viewH = 360;
const dpr = Math.min(window.devicePixelRatio || 1, 2);
canvas.width = Math.round(viewW * dpr);
canvas.height = Math.round(viewH * dpr);
canvas.style.width = viewW + "px";
canvas.style.height = viewH + "px";
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

if (element._orbStop) element._orbStop();
window.__energyOrbBoots = (window.__energyOrbBoots || 0) + 1;
let stopped = false;
let frame = 0;
let watchTimer = 0;
let angle = element._orbAngle || 0;
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
  const liveLabel = document.querySelector("#energy-orb-host .orb-state");
  const liveOrb = document.querySelector("#energy-orb-host .energy-orb");
  if (liveLabel) liveLabel.textContent = next === "thinking" ? "THINKING" : "CALM";
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
function addArc(index, theta, phi, dir, span, width, gain, speed) {
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
  webs.push({ points: points, speed: speed, width: width, gain: gain });
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
  ctx.lineWidth = width + 1.15;
  ctx.strokeStyle = "rgba(80, 205, 255, " + (alpha * 0.22) + ")";
  ctx.stroke(path);
  ctx.lineWidth = width;
  ctx.strokeStyle = "rgba(240, 253, 255, " + alpha + ")";
  ctx.stroke(path);
}

function strokeRing(cx, cy, rx, ry, rotation, width, alpha) {
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, rotation, 0, Math.PI * 2);
  ctx.lineWidth = width + 2.4;
  ctx.strokeStyle = "rgba(90, 210, 255, " + (alpha * 0.32) + ")";
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, rotation, 0, Math.PI * 2);
  ctx.lineWidth = width;
  ctx.strokeStyle = "rgba(226, 250, 255, " + alpha + ")";
  ctx.stroke();
}

function draw() {
  if (stopped) return;
  const thinking = (window.__energyOrbMode || mode) === "thinking";
  angle += thinking ? 0.011 : 0.0045;
  const cx = viewW / 2;
  const cy = viewH / 2;
  const radius = 98;
  const pulse = 0.5 + 0.5 * Math.sin(angle * (thinking ? 3.2 : 1.4));
  const boost = thinking ? 1.12 : 1;
  ctx.clearRect(0, 0, viewW, viewH);
  ctx.globalCompositeOperation = "source-over";
  ctx.shadowBlur = 0;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  fillGlow(cx, cy, radius, 150, "rgba(80, 190, 255, " + (0.4 + pulse * 0.12) + ")", "rgba(6, 36, 110, 0.06)");
  fillGlow(cx, cy, radius, 114, "rgba(150, 230, 255, " + (0.32 + pulse * 0.1) + ")", "rgba(16, 110, 200, 0.1)");

  const shell = ctx.createRadialGradient(cx, cy - radius * 0.12, radius * 0.08, cx, cy, radius);
  shell.addColorStop(0, "rgba(186, 244, 255, 0.1)");
  shell.addColorStop(0.48, "rgba(3, 24, 58, 0.55)");
  shell.addColorStop(0.8, "rgba(10, 80, 150, 0.2)");
  shell.addColorStop(0.94, "rgba(70, 200, 255, 0.32)");
  shell.addColorStop(1, "rgba(200, 250, 255, 0.62)");
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = shell;
  ctx.fill();

  ctx.globalCompositeOperation = "lighter";
  const ringTilt = 0.28 + Math.sin(angle * 0.45) * 0.05;
  strokeRing(cx, cy, radius * 0.74, radius * 0.6, ringTilt, 1.15 * boost, 0.72);
  strokeRing(cx, cy, radius * 0.46, radius * 0.37, ringTilt - 0.08, 1.2 * boost, 0.88);

  for (let index = 0; index < webs.length; index++) {
    const spec = webs[index];
    const spin = angle * spec.speed;
    const paths = webPaths(spec, spin, cx, cy, radius);
    strokeWeb(paths.back, spec.width * 0.8, spec.gain * 0.16 * boost);
    strokeWeb(paths.front, spec.width, spec.gain * 0.82 * boost);
  }

  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 1.04, 0, Math.PI * 2);
  ctx.clip();
  const band = ctx.createLinearGradient(cx, cy - 11, cx, cy + 11);
  band.addColorStop(0, "rgba(80, 200, 255, 0)");
  band.addColorStop(0.38, "rgba(120, 220, 255, 0.14)");
  band.addColorStop(0.5, "rgba(230, 252, 255, " + (0.62 + pulse * 0.12) + ")");
  band.addColorStop(0.62, "rgba(120, 220, 255, 0.14)");
  band.addColorStop(1, "rgba(80, 200, 255, 0)");
  ctx.fillStyle = band;
  ctx.fillRect(cx - radius, cy - 11, radius * 2, 22);
  const flare = ctx.createLinearGradient(cx - radius, cy, cx + radius, cy);
  flare.addColorStop(0, "rgba(180, 240, 255, 0)");
  flare.addColorStop(0.12, "rgba(210, 248, 255, 0.15)");
  flare.addColorStop(0.38, "rgba(245, 254, 255, 0.85)");
  flare.addColorStop(0.5, "rgba(255, 255, 255, 1)");
  flare.addColorStop(0.62, "rgba(245, 254, 255, 0.85)");
  flare.addColorStop(0.88, "rgba(210, 248, 255, 0.15)");
  flare.addColorStop(1, "rgba(180, 240, 255, 0)");
  ctx.strokeStyle = flare;
  ctx.lineWidth = thinking ? 1.45 : 1.15;
  ctx.beginPath();
  ctx.moveTo(cx - radius * 0.98, cy);
  ctx.lineTo(cx + radius * 0.98, cy);
  ctx.stroke();
  ctx.restore();

  const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.16);
  bloom.addColorStop(0, "rgba(255, 255, 255, 0.95)");
  bloom.addColorStop(0.35, "rgba(190, 246, 255, 0.55)");
  bloom.addColorStop(1, "rgba(40, 180, 255, 0)");
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.16, 0, Math.PI * 2);
  ctx.fill();

  for (let spark = 0; spark < 22; spark++) {
    const spec = webs[spark % webs.length];
    const point = spec.points[Math.min(spec.points.length - 1, 2 + (spark % 5))];
    const projected = projectPoint(point, angle * spec.speed, cx, cy, radius);
    if (projected.z < 0.05) continue;
    const twinkle = 0.35 + 0.65 * Math.abs(Math.sin(angle * (thinking ? 4 : 1.8) + spark));
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, spark % 4 === 0 ? 1.5 : 0.8, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(245, 254, 255, " + twinkle + ")";
    ctx.fill();
  }

  ctx.globalCompositeOperation = "source-over";
  ctx.beginPath();
  ctx.arc(cx, cy, radius - 0.4, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(214, 250, 255, " + (0.72 + pulse * 0.2) + ")";
  ctx.lineWidth = 1.45;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx, cy, radius + 1.2, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(120, 220, 255, " + (0.28 + pulse * 0.1) + ")";
  ctx.lineWidth = 3.2;
  ctx.stroke();

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
#energy-orb-host canvas {
  display: block;
  width: 360px;
  height: 360px;
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
            gr.HTML(
                ORB_HTML,
                elem_id="energy-orb-host",
                js_on_load=ORB_JS,
                apply_default_css=False,
                padding=False,
                container=False,
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

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        share=False,
        analytics_enabled=False,
        theme=ORB_THEME,
        css=ORB_CSS,
    )
