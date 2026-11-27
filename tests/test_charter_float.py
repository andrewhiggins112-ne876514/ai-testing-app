"""KAN-386 — OS-level Manual Charter Frame float (FR-MAN-1 snip-tool)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import charter_float as cf
from plans import manual_session as ms
from plans.store import plans_dir

ROOT = Path(__file__).resolve().parents[1]


class CharterFloatGeometryTests(unittest.TestCase):
    def test_content_bbox_from_window(self) -> None:
        bbox = cf.content_bbox_from_window(100, 50, 640, 480)
        self.assertIsNotNone(bbox)
        assert bbox is not None
        self.assertEqual(bbox[0], 100 + cf.BORDER)
        self.assertEqual(bbox[1], 50 + cf.BORDER + cf.HEADER_H)
        self.assertLess(bbox[2] - bbox[0], 640)
        self.assertLess(bbox[3] - bbox[1], 480)

    def test_window_geom_roundtrip(self) -> None:
        geom = cf.window_geom_from_content_bbox([200, 120, 800, 500])
        back = cf.content_bbox_from_window(
            geom["x"], geom["y"], geom["width"], geom["height"]
        )
        self.assertEqual(back, [200, 120, 800, 500])

    def test_default_geom_and_payload(self) -> None:
        geom = cf.default_window_geom(
            virtual={"left": 0, "top": 0, "width": 1000, "height": 800},
            frame={"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5},
        )
        self.assertGreaterEqual(geom["width"], cf.MIN_WINDOW_W)
        self.assertGreaterEqual(geom["height"], cf.MIN_WINDOW_H)
        payload = cf.is_float_available_payload(True)
        self.assertTrue(payload["available"])
        self.assertFalse(payload["keylog"])
        self.assertFalse(payload["clipboard"])
        self.assertFalse(payload["mic"])
        self.assertEqual(payload["title"], "Charter Frame")


class CharterFloatSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._root = Path(self._tmpdir.name)
        self._level_patch = mock.patch(
            "settings.store.get_security_level", return_value="OFFICIAL"
        )
        self._dir_patch = mock.patch(
            "settings.store.app_data_dir", return_value=self._root
        )
        self._level_patch.start()
        self._dir_patch.start()
        self.addCleanup(self._level_patch.stop)
        self.addCleanup(self._dir_patch.stop)
        ms.reset_open_cache()

    def test_start_without_jira_or_assist(self) -> None:
        out = ms.start_session(
            "Explore snip float",
            ticket_bound=False,
            jira_story_key="",
            agent_assist=False,
        )
        self.assertEqual(out["status"], "ok")
        sess = out["session"]
        self.assertFalse(sess["ticket_bound"])
        self.assertEqual(sess["jira_story_key"], "")
        self.assertFalse(sess["agent_assist"])
        self.assertFalse(out["writes_jira"])
        self.assertFalse(out["background_capture"])

    def test_float_frame_keeps_screen_bbox_and_still_level_scoped(self) -> None:
        started = ms.start_session(
            "Float still",
            ticket_bound=False,
            agent_assist=False,
        )
        sid = started["session"]["id"]
        framed = ms.update_session_frame(
            sid,
            {"x": 0.2, "y": 0.2, "w": 0.4, "h": 0.4},
            frame_mode="float",
            screen_bbox=[10, 20, 310, 220],
        )
        self.assertEqual(framed["status"], "ok")
        self.assertEqual(framed["session"]["frame_mode"], "float")
        self.assertEqual(framed["session"]["screen_bbox"], [10, 20, 310, 220])

        with mock.patch("PIL.ImageGrab.grab") as grab:
            fake = mock.MagicMock()
            fake.size = (300, 200)

            def _save(path, format=None):  # noqa: A002
                Path(path).write_bytes(b"PNG")

            fake.save.side_effect = _save
            grab.return_value = fake
            still = ms.attach_still(sid, screen_bbox=[10, 20, 310, 220])
        self.assertEqual(still["status"], "ok")
        self.assertTrue(still["still"]["captured"])
        path = Path(still["still"]["path"])
        self.assertTrue(path.is_file())
        # Level-scoped under plans/OFFICIAL/sessions/…
        expected_root = plans_dir("OFFICIAL") / "sessions"
        self.assertEqual(path.resolve().parent.parent, expected_root.resolve())
        ended = ms.end_session(sid)
        self.assertEqual(ended["status"], "ok")
        self.assertEqual(len(ended["session"]["stills"]), 1)


class CharterFloatUiMarkersTests(unittest.TestCase):
    def test_desktop_float_markers_desk141(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        float_html = (ROOT / "ui" / "desktop" / "charter_float.html").read_text(
            encoding="utf-8"
        )
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk141", html)
        self.assertIn("desk141", desk)
        self.assertIn("desk141", float_html)
        self.assertIn('data-charter-float="1"', html)
        self.assertIn('data-charter-float="1"', float_html)
        self.assertIn("data-os-float", float_html)
        self.assertIn("charter_float_open", desk)
        self.assertIn("openOsCharterFloat", js)
        self.assertIn("charterOsFloatActive", js)
        self.assertIn("withTimeout", js)
        self.assertIn("No keylog", float_html)
        # Deadlock guard: open path must not call evaluate_js into the float page.
        open_fn = desk.split("def charter_float_open", 1)[1].split(
            "def charter_float_close", 1
        )[0]
        self.assertNotIn(".evaluate_js(", open_fn)
        self.assertNotIn("evaluate_js(", open_fn.split('"""', 2)[-1])
        float_js = (ROOT / "ui" / "desktop" / "charter_float.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("loadOpenSession", float_js)
        self.assertIn("/api/manual-sessions/open", float_js)

    def test_api_start_charter_only_and_float_frame(self) -> None:
        from main import app

        client = TestClient(app)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch(
                "settings.store.get_security_level", return_value="OFFICIAL"
            ), mock.patch(
                "settings.store.app_data_dir", return_value=root
            ):
                ms.reset_open_cache()
                res = client.post(
                    "/api/manual-sessions/start",
                    json={
                        "charter": "API float snip",
                        "ticket_bound": False,
                        "agent_assist": False,
                    },
                )
                self.assertEqual(res.status_code, 200)
                body = res.json()
                self.assertEqual(body["status"], "ok")
                sid = body["session"]["id"]
                fr = client.post(
                    f"/api/manual-sessions/{sid}/frame",
                    json={
                        "x": 0.2,
                        "y": 0.2,
                        "w": 0.5,
                        "h": 0.5,
                        "frame_mode": "float",
                        "screen_bbox": [40, 40, 440, 340],
                    },
                )
                self.assertEqual(fr.status_code, 200)
                framed = fr.json()
                self.assertEqual(framed["session"]["frame_mode"], "float")
                self.assertEqual(framed["session"]["screen_bbox"], [40, 40, 440, 340])
                client.post(
                    f"/api/manual-sessions/{sid}/cancel", json={"confirm": True}
                )


if __name__ == "__main__":
    unittest.main()
