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

JARVIS_HTML = """
<div class="jarvis-orb" data-state="calm">
  <canvas width="640" height="640" aria-label="JARVIS energy orb"></canvas>
  <div class="jarvis-state">CALM</div>
</div>
"""

JARVIS_JS = r"""
const canvas = element.querySelector("canvas");
const label = element.querySelector(".jarvis-state");
if (!canvas) return;
const ctx = canvas.getContext("2d");
const viewW = 340;
const viewH = 400;
const dpr = Math.min(window.devicePixelRatio || 1, 2);
canvas.width = Math.round(viewW * dpr);
canvas.height = Math.round(viewH * dpr);
canvas.style.width = viewW + "px";
canvas.style.height = viewH + "px";
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

if (element._jarvisStop) element._jarvisStop();
let stopped = false;
let frame = 0;
element._jarvisStop = function () {
  stopped = true;
  cancelAnimationFrame(frame);
};

let mode = "calm";
let angle = 0;
let sawLoading = false;
let armedAt = 0;

function chatRoot() {
  return document.getElementById("jarvis-chat");
}

function loading() {
  const root = chatRoot();
  return !!(root && root.querySelector('[aria-label="Loading response"]'));
}

function setMode(next) {
  if (next === mode) return;
  mode = next;
  if (label) label.textContent = next === "thinking" ? "THINKING" : "CALM";
  const orb = element.querySelector(".jarvis-orb");
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

function glowArc(cx, cy, rx, ry, tilt, spin, span, width, alpha) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(tilt);
  ctx.shadowColor = "rgba(110, 225, 255, 0.95)";
  ctx.shadowBlur = 14;
  ctx.beginPath();
  ctx.ellipse(0, 0, rx, ry, 0, spin, spin + span);
  ctx.strokeStyle = "rgba(120, 210, 255, " + (alpha * 0.4) + ")";
  ctx.lineWidth = width + 2.6;
  ctx.stroke();
  ctx.shadowBlur = 5;
  ctx.beginPath();
  ctx.ellipse(0, 0, rx, ry, 0, spin, spin + span);
  ctx.strokeStyle = "rgba(236, 252, 255, " + alpha + ")";
  ctx.lineWidth = width;
  ctx.stroke();
  ctx.restore();
}

function draw() {
  if (stopped) return;
  const thinking = mode === "thinking";
  angle += thinking ? 0.011 : 0.0045;
  const cx = viewW / 2;
  const cy = 148;
  const radius = 86;
  const floorY = 368;
  const pulse = 0.5 + 0.5 * Math.sin(angle * (thinking ? 3.4 : 1.35));
  const arcAlpha = thinking ? 0.92 : 0.7;
  ctx.clearRect(0, 0, viewW, viewH);
  ctx.globalCompositeOperation = "source-over";
  ctx.shadowBlur = 0;

  const glowReach = 142;
  const halo = ctx.createRadialGradient(cx, cy, radius * 0.08, cx, cy, glowReach);
  halo.addColorStop(0, "rgba(198, 248, 255, " + (0.7 + pulse * 0.18) + ")");
  halo.addColorStop(0.2, "rgba(60, 185, 255, " + (0.38 + pulse * 0.1) + ")");
  halo.addColorStop(0.5, "rgba(14, 90, 180, 0.16)");
  halo.addColorStop(0.78, "rgba(8, 28, 60, 0.04)");
  halo.addColorStop(1, "rgba(5, 7, 13, 0)");
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.arc(cx, cy, glowReach, 0, Math.PI * 2);
  ctx.fill();

  const beam = ctx.createLinearGradient(cx, cy + radius * 0.4, cx, floorY);
  beam.addColorStop(0, "rgba(170, 240, 255, " + (0.42 + pulse * 0.12) + ")");
  beam.addColorStop(0.45, "rgba(50, 170, 255, 0.16)");
  beam.addColorStop(1, "rgba(50, 170, 255, 0)");
  ctx.fillStyle = beam;
  ctx.beginPath();
  ctx.moveTo(cx - 7, cy + radius * 0.72);
  ctx.lineTo(cx + 7, cy + radius * 0.72);
  ctx.lineTo(cx + 26, floorY);
  ctx.lineTo(cx - 26, floorY);
  ctx.fill();

  for (let ring = 0; ring < 3; ring++) {
    ctx.beginPath();
    ctx.ellipse(cx, floorY, 34 + ring * 26, 8 + ring * 5, 0, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(130, 220, 255, " + (0.32 - ring * 0.07) + ")";
    ctx.lineWidth = ring === 0 ? 1.4 : 1;
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.arc(cx, floorY, 2.2, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(220, 250, 255, 0.85)";
  ctx.fill();

  const body = ctx.createRadialGradient(cx - 18, cy - 22, 2, cx, cy, radius);
  body.addColorStop(0, "rgba(255, 255, 255, 1)");
  body.addColorStop(0.1, "rgba(210, 250, 255, 0.98)");
  body.addColorStop(0.32, "rgba(70, 205, 255, 0.9)");
  body.addColorStop(0.68, "rgba(10, 78, 180, 0.78)");
  body.addColorStop(1, "rgba(3, 16, 42, 0.5)");
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = body;
  ctx.shadowColor = "rgba(80, 210, 255, " + (thinking ? 0.9 : 0.65) + ")";
  ctx.shadowBlur = thinking ? 42 : 28;
  ctx.fill();
  ctx.shadowBlur = 0;

  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.42);
  core.addColorStop(0, "rgba(255, 255, 255, 0.95)");
  core.addColorStop(0.45, "rgba(140, 235, 255, 0.45)");
  core.addColorStop(1, "rgba(80, 190, 255, 0)");
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.42, 0, Math.PI * 2);
  ctx.fill();

  ctx.globalCompositeOperation = "lighter";
  const arcs = [
    [radius * 0.62, radius * 0.34, 0.55, 0.72, 0.4, 4.4, 1.15],
    [radius * 0.84, radius * 0.5, -0.85, 1.2, 1.7, 4.1, 1.05],
    [radius * 1.16, radius * 0.46, 1.15, 0.55, 2.5, 3.5, 1.1],
    [radius * 1.34, radius * 0.3, -0.25, 1.55, 4.1, 2.9, 0.95],
  ];
  for (let index = 0; index < arcs.length; index++) {
    const arc = arcs[index];
    glowArc(
      cx,
      cy,
      arc[0],
      arc[1],
      arc[2] + angle * 0.12,
      angle * arc[3] + arc[4],
      arc[5],
      arc[6],
      arcAlpha
    );
  }
  ctx.globalCompositeOperation = "source-over";

  ctx.beginPath();
  ctx.arc(cx, cy, radius - 1, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(200, 246, 255, " + (0.4 + pulse * 0.3) + ")";
  ctx.lineWidth = 1.6;
  ctx.shadowColor = "rgba(150, 235, 255, 0.85)";
  ctx.shadowBlur = 12;
  ctx.stroke();
  ctx.shadowBlur = 0;

  ctx.beginPath();
  ctx.ellipse(cx - 28, cy - 32, 22, 11, -0.55, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(255, 255, 255, 0.28)";
  ctx.fill();

  for (let spark = 0; spark < 14; spark++) {
    const seed = spark * 2.399;
    const orbit = angle * (0.45 + (spark % 4) * 0.22) + seed;
    const dist = radius * (0.28 + (spark % 6) * 0.16);
    const x = cx + Math.cos(orbit) * dist;
    const y = cy + Math.sin(orbit * 0.86 + seed) * dist * 0.78;
    const twinkle = 0.2 + 0.8 * Math.abs(Math.sin(angle * (thinking ? 5.5 : 2.1) + seed));
    ctx.beginPath();
    ctx.arc(x, y, spark % 5 === 0 ? 1.5 : 0.85, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(225, 250, 255, " + (0.18 + twinkle * 0.5) + ")";
    ctx.fill();
  }

  frame = requestAnimationFrame(draw);
}
draw();
"""

JARVIS_CSS = """
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
#jarvis-orb-host,
#jarvis-orb-host .html-container {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}
#jarvis-orb-host .jarvis-orb {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 430px;
}
#jarvis-orb-host canvas {
  display: block;
  width: 340px;
  height: 400px;
}
#jarvis-orb-host .jarvis-state {
  margin-top: 2px;
  font-family: ui-monospace, Consolas, monospace;
  letter-spacing: 0.42em;
  font-size: 12px;
  color: #7ee7ff;
}
#jarvis-chat { background: transparent !important; }
"""

JARVIS_THEME = gr.themes.Base(
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
                JARVIS_HTML,
                elem_id="jarvis-orb-host",
                js_on_load=JARVIS_JS,
                apply_default_css=False,
                padding=False,
                container=False,
            )
            with gr.Column(elem_id="jarvis-chat"):
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
        theme=JARVIS_THEME,
        css=JARVIS_CSS,
    )
