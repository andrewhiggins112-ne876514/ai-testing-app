"""Reliable Gradio UI entry point for Windows.

Use this (not fragile module paths):

    .\\venv\\Scripts\\python.exe run_ui.py
"""
from ui.gradio_app import demo, ORB_THEME, ORB_CSS

if __name__ == "__main__":
    print("Starting AI Testing Agent UI on http://127.0.0.1:7860 ...", flush=True)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        analytics_enabled=False,
        theme=ORB_THEME,
        css=ORB_CSS,
        inbrowser=True,
    )
