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
let stopped = false;
let frame = 0;
element._orbStop = function () {
  stopped = true;
  cancelAnimationFrame(frame);
};

let mode = "calm";
let angle = 0;
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
  if (next === mode) return;
  mode = next;
  if (label) label.textContent = next === "thinking" ? "THINKING" : "CALM";
  const orb = element.querySelector(".energy-orb");
  if (orb) orb.setAttribute("data-state", next);
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

document.addEventListener("keydown", function (event) {
  if (event.key !== "Enter" || event.shiftKey) return;
  const root = chatRoot();
  if (!root || !event.target || !root.contains(event.target)) return;
  if (event.target.tagName !== "TEXTAREA") return;
  if (!String(event.target.value || "").trim()) return;
  armThinking();
}, true);

document.addEventListener("click", function (event) {
  const root = chatRoot();
  if (!root || !event.target || !event.target.closest) return;
  const button = event.target.closest('[data-testid="submit-button"]');
  if (!button || !root.contains(button)) return;
  const box = root.querySelector("textarea");
  if (!box || !String(box.value || "").trim()) return;
  armThinking();
}, true);

const observer = new MutationObserver(tick);
function watchChat() {
  const root = chatRoot();
  if (!root) {
    setTimeout(watchChat, 200);
    return;
  }
  observer.observe(root, { childList: true, subtree: true, attributes: true });
  tick();
}
watchChat();
setInterval(tick, 150);

const mists = [];
for (let index = 0; index < 7; index++) {
  mists.push({
    rx: 0.42 + (index % 3) * 0.16,
    ry: 0.26 + (index % 4) * 0.1,
    tilt: index * 0.72,
    speed: 0.24 + (index % 5) * 0.15,
    phase: index * 1.31,
    span: 4.1 + (index % 3) * 0.7,
    spread: 18 + (index % 3) * 7,
    wobble: 7 + index * 1.4,
  });
}

function fillGlow(cx, cy, radius, reach, inner, mid) {
  const glow = ctx.createRadialGradient(cx, cy, radius * 0.02, cx, cy, reach);
  glow.addColorStop(0, inner);
  glow.addColorStop(0.45, mid);
  glow.addColorStop(1, "rgba(5, 7, 13, 0)");
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(cx, cy, reach, 0, Math.PI * 2);
  ctx.fill();
}

function mistPoint(cx, cy, radius, spec, time, u) {
  const along = time * spec.speed + spec.phase + u * spec.span;
  const tilt = spec.tilt + Math.sin(time * 0.25 + spec.phase) * 0.28;
  const breathe = 1 + 0.1 * Math.sin(time * 1.3 + spec.phase + u * 3.6);
  const wave = Math.sin(along * 1.5 + time * 0.9 + spec.phase) * spec.wobble;
  const rx = radius * spec.rx * breathe;
  const ry = radius * spec.ry * breathe;
  const x0 = Math.cos(along) * rx;
  const y0 = Math.sin(along) * ry + wave;
  const ct = Math.cos(tilt);
  const st = Math.sin(tilt);
  return {
    x: cx + x0 * ct - y0 * st * 0.18,
    y: cy + x0 * st * 0.48 + y0 * ct,
    fade: Math.sin(Math.PI * u),
  };
}

function paintMist(cx, cy, radius, spec, time, strength) {
  const samples = 14;
  for (let step = 0; step <= samples; step++) {
    const point = mistPoint(cx, cy, radius, spec, time, step / samples);
    if (point.fade < 0.05) continue;
    const reach = spec.spread * (0.5 + 0.5 * point.fade);
    const puff = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, reach);
    const alpha = strength * point.fade;
    puff.addColorStop(0, "rgba(214, 248, 255, " + (alpha * 0.34) + ")");
    puff.addColorStop(0.38, "rgba(60, 180, 255, " + (alpha * 0.14) + ")");
    puff.addColorStop(1, "rgba(8, 30, 70, 0)");
    ctx.fillStyle = puff;
    ctx.beginPath();
    ctx.arc(point.x, point.y, reach, 0, Math.PI * 2);
    ctx.fill();
  }
}

function draw() {
  if (stopped) return;
  const thinking = mode === "thinking";
  angle += thinking ? 0.011 : 0.0045;
  const cx = viewW / 2;
  const cy = viewH / 2;
  const radius = 98;
  const pulse = 0.5 + 0.5 * Math.sin(angle * (thinking ? 3.4 : 1.35));
  const strength = thinking ? 0.72 : 0.5;
  ctx.clearRect(0, 0, viewW, viewH);
  ctx.globalCompositeOperation = "source-over";
  ctx.shadowBlur = 0;
  ctx.lineWidth = 0;

  fillGlow(cx, cy, radius, 152, "rgba(70, 160, 255, " + (0.22 + pulse * 0.08) + ")", "rgba(8, 40, 120, 0.05)");
  fillGlow(cx, cy, radius, 114, "rgba(140, 220, 255, " + (0.28 + pulse * 0.1) + ")", "rgba(20, 110, 210, 0.1)");
  fillGlow(cx, cy, radius, 70, "rgba(220, 248, 255, " + (0.22 + pulse * 0.08) + ")", "rgba(80, 190, 255, 0.08)");

  for (let index = 0; index < mists.length; index++) {
    paintMist(cx, cy, radius, mists[index], angle, strength);
  }

  const shell = ctx.createRadialGradient(cx - 16, cy - 20, 4, cx, cy, radius * 1.05);
  shell.addColorStop(0, "rgba(210, 246, 255, 0.16)");
  shell.addColorStop(0.28, "rgba(50, 160, 235, 0.1)");
  shell.addColorStop(0.62, "rgba(12, 70, 160, 0.07)");
  shell.addColorStop(1, "rgba(5, 7, 13, 0)");
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 1.05, 0, Math.PI * 2);
  ctx.fillStyle = shell;
  ctx.shadowColor = "rgba(60, 180, 255, " + (thinking ? 0.45 : 0.3) + ")";
  ctx.shadowBlur = thinking ? 28 : 18;
  ctx.fill();
  ctx.shadowBlur = 0;

  const bloom = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.42);
  bloom.addColorStop(0, "rgba(255, 255, 255, " + (0.72 + pulse * 0.08) + ")");
  bloom.addColorStop(0.22, "rgba(190, 245, 255, 0.38)");
  bloom.addColorStop(0.55, "rgba(40, 160, 255, 0.1)");
  bloom.addColorStop(1, "rgba(0, 80, 170, 0)");
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.42, 0, Math.PI * 2);
  ctx.fill();

  for (let mote = 0; mote < 8; mote++) {
    const seed = mote * 2.399;
    const orbit = angle * (0.3 + (mote % 4) * 0.12) + seed;
    const dist = radius * (0.22 + (mote % 5) * 0.12);
    const x = cx + Math.cos(orbit) * dist;
    const y = cy + Math.sin(orbit * 0.85 + seed) * dist * 0.8;
    const twinkle = 0.25 + 0.75 * Math.abs(Math.sin(angle * (thinking ? 4.2 : 1.7) + seed));
    const reach = 6 + (mote % 3) * 3;
    const puff = ctx.createRadialGradient(x, y, 0, x, y, reach);
    puff.addColorStop(0, "rgba(230, 250, 255, " + (0.22 * twinkle) + ")");
    puff.addColorStop(1, "rgba(80, 180, 255, 0)");
    ctx.fillStyle = puff;
    ctx.beginPath();
    ctx.arc(x, y, reach, 0, Math.PI * 2);
    ctx.fill();
  }

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
