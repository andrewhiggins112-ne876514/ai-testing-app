"""KAN-287 / KAN-288 — Charter Frame window/monitor snap."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import charter_snap as snap
from plans import manual_session as ms

ROOT = Path(__file__).resolve().parents[1]

FAKE_TARGETS = {
    "status": "ok",
    "platform": "win32",
    "monitors": [
        {
            "id": "mon1",
            "label": "Monitor 1 (primary)",
            "bbox": [0, 0, 1920, 1080],
            "is_primary": True,
        },
        {
            "id": "mon2",
            "label": "Monitor 2",
            "bbox": [1920, 0, 3840, 1080],
            "is_primary": False,
        },
    ],
    "windows": [
        {
            "id": "hwnd100",
            "title": "AUT Login",
            "bbox": [100, 50, 900, 700],
        }
    ],
    "virtual": {"left": 0, "top": 0, "width": 3840, "height": 1080},
}


class CharterSnapMathTests(unittest.TestCase):
    def test_bounds_to_frame_on_virtual_desktop(self):
        virt = {"left": 0, "top": 0, "width": 3840, "height": 1080}
        frame = snap.bounds_to_frame([1920, 0, 3840, 1080], virt)
        self.assertAlmostEqual(frame["x"], 0.5, places=4)
        self.assertAlmostEqual(frame["y"], 0.0, places=4)
        self.assertAlmostEqual(frame["w"], 0.5, places=4)
        self.assertAlmostEqual(frame["h"], 1.0, places=4)

    def test_virtual_desktop_union(self):
        virt = snap.virtual_desktop_from_monitors(FAKE_TARGETS["monitors"])
        self.assertEqual(virt["left"], 0)
        self.assertEqual(virt["width"], 3840)
        self.assertEqual(virt["height"], 1080)

    def test_resolve_monitor_and_window(self):
        mon = snap.resolve_snap_target("monitor", "mon2", targets=FAKE_TARGETS)
        self.assertEqual(mon["status"], "ok")
        self.assertEqual(mon["screen_bbox"], [1920, 0, 3840, 1080])
        self.assertAlmostEqual(mon["frame"]["x"], 0.5, places=4)

        win = snap.resolve_snap_target("window", "hwnd100", targets=FAKE_TARGETS)
        self.assertEqual(win["status"], "ok")
        self.assertEqual(win["label"], "AUT Login")
        self.assertEqual(win["screen_bbox"], [100, 50, 900, 700])


class CharterSnapSessionTests(unittest.TestCase):
    def setUp(self):
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

    def test_snap_monitor_then_free_region_clears_bbox(self):
        started = ms.start_session("Snap charter")
        sid = started["session"]["id"]
        self.assertEqual(started["session"]["frame_mode"], "free")
        self.assertIsNone(started["session"]["screen_bbox"])

        snapped = ms.snap_session_frame(
            sid, "monitor", "mon1", targets=FAKE_TARGETS
        )
        self.assertEqual(snapped["status"], "ok")
        self.assertEqual(snapped["session"]["frame_mode"], "monitor")
        self.assertEqual(snapped["session"]["screen_bbox"], [0, 0, 1920, 1080])
        self.assertIn("Monitor 1", snapped["session"]["snap_label"])
        # Assist/mist unchanged
        self.assertFalse(snapped["session"]["agent_assist"])
        self.assertFalse(snapped["session"]["armed_mist"])

        freed = ms.update_session_frame(
            sid,
            {"x": 0.2, "y": 0.2, "w": 0.5, "h": 0.5},
            frame_mode="free",
        )
        self.assertEqual(freed["session"]["frame_mode"], "free")
        self.assertIsNone(freed["session"]["screen_bbox"])
        self.assertEqual(freed["session"]["snap_label"], "")
        self.assertAlmostEqual(freed["session"]["frame"]["x"], 0.2, places=4)

    def test_snap_window_and_defaults_advertise(self):
        info = ms.defaults_info()
        self.assertTrue(info["window_monitor_snap"])
        self.assertEqual(info["frame_snap_modes"], ["free", "monitor", "window"])

        started = ms.start_session("Window snap")
        sid = started["session"]["id"]
        ms.update_session_toggles(sid, agent_assist=True, armed_mist=True)
        snapped = ms.snap_session_frame(
            sid, "window", "hwnd100", targets=FAKE_TARGETS
        )
        self.assertEqual(snapped["status"], "ok")
        self.assertEqual(snapped["session"]["frame_mode"], "window")
        self.assertEqual(snapped["session"]["snap_label"], "AUT Login")
        self.assertTrue(snapped["session"]["agent_assist"])
        self.assertTrue(snapped["session"]["armed_mist"])


class CharterSnapApiAndUiTests(unittest.TestCase):
    def setUp(self):
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
        from main import app

        self.client = TestClient(app)

    def test_api_snap_targets_and_snap(self):
        with mock.patch(
            "main.manual_list_snap_targets", return_value=FAKE_TARGETS
        ):
            targets = self.client.get("/api/manual-sessions/snap-targets").json()
        self.assertEqual(targets["status"], "ok")
        self.assertEqual(len(targets["monitors"]), 2)

        started = self.client.post(
            "/api/manual-sessions/start",
            json={"charter": "API snap"},
        ).json()
        sid = started["session"]["id"]

        resolved = snap.resolve_snap_target(
            "monitor", "mon2", targets=FAKE_TARGETS
        )
        with mock.patch(
            "plans.charter_snap.resolve_snap_target", return_value=resolved
        ):
            snapped = self.client.post(
                f"/api/manual-sessions/{sid}/snap",
                json={"mode": "monitor", "target_id": "mon2"},
            ).json()
        self.assertEqual(snapped["status"], "ok")
        self.assertEqual(snapped["session"]["frame_mode"], "monitor")
        self.assertEqual(snapped["session"]["screen_bbox"], [1920, 0, 3840, 1080])

        freed = self.client.post(
            f"/api/manual-sessions/{sid}/frame",
            json={"x": 0.1, "y": 0.1, "w": 0.4, "h": 0.4, "frame_mode": "free"},
        ).json()
        self.assertEqual(freed["session"]["frame_mode"], "free")
        self.assertIsNone(freed["session"]["screen_bbox"])

        defaults = self.client.get("/api/manual-sessions/defaults").json()
        self.assertTrue(defaults["window_monitor_snap"])

    def test_desktop_snap_markers_desk162(self):
        html = self.client.get("/ui/desktop/index.html?v=desk162").text
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("desk162", html)
        self.assertIn("desk162", desk)
        self.assertIn('data-charter-snap="1"', html)
        self.assertIn('data-charter-snap-monitor="1"', html)
        self.assertIn('data-charter-snap-window="1"', html)
        self.assertIn('data-charter-snap-picker="1"', html)
        self.assertIn("data-charter-snap-ui", html)
        self.assertIn(".charter-snap-picker", css)
        self.assertIn("openCharterSnapPicker", js)
        self.assertIn("applyCharterSnap", js)
        # Assist/mist still present
        self.assertIn("charter-assist-live", html)
        self.assertIn("charter-mist-live", html)


if __name__ == "__main__":
    unittest.main()
