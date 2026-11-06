"""Native desktop window for the AI Testing Agent (pywebview + local FastAPI).

Run:
    .\\venv\\Scripts\\python.exe desktop_app.py
"""
from __future__ import annotations

import sys
import time
import threading
from urllib.request import urlopen
from urllib.error import URLError

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/ui/desktop/index.html?v=desk7"
HEALTH = f"http://{HOST}:{PORT}/health"


def _serve() -> None:
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        reload=False,
    )


def _wait_ready(timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(HEALTH, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (URLError, OSError):
            time.sleep(0.2)
    return False


def main() -> int:
    server = threading.Thread(target=_serve, name="fastapi-desktop", daemon=True)
    server.start()
    if not _wait_ready():
        print(f"ERROR: FastAPI did not become ready on {HEALTH}", flush=True)
        return 1

    print(f"Opening desktop window → {URL}", flush=True)
    webview.create_window(
        title="AI Testing Agent",
        url=URL,
        width=1280,
        height=820,
        min_size=(960, 640),
        background_color="#000000",
    )
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
