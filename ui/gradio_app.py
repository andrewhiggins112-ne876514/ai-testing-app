"""Minimal local Gradio chat client. Talks to the FastAPI agent on port 8000."""
import os
import uuid

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr
import httpx

CHAT_URL = "http://127.0.0.1:8000/chat"


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
    session_id = gr.State(new_session_id)
    gr.ChatInterface(
        respond,
        additional_inputs=[session_id],
        title="AI Testing Agent",
        analytics_enabled=False,
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", share=False, analytics_enabled=False)
