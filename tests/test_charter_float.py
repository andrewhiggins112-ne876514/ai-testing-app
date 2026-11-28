"""KAN-386 / KAN-512 / KAN-525 — Charter float: native Look 4 side tray."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from plans import charter_float as cf
from plans import charter_ring_native as ring
from plans import manual_session as ms
from plans.store import plans_dir

ROOT = Path(__file__).resolve().parents[1]


class CharterFloatGeometryTests(unittest.TestCase):
    def test_default_geom_clamped_to_primary_not_huge(self) -> None:
        monitors = [
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
        ]
        geom = cf.default_window_geom(
            virtual={"left": 0, "top": 0, "width": 3840, "height": 1080},
            frame={"x": 0.18, "y": 0.16, "w": 0.64, "h": 0.58},
            monitors=monitors,
        )
        self.assertLessEqual(geom["width"], cf.MAX_CAPTURE_W + 2 * cf.SIDE)
        self.assertLess(geom["x"] + geom["width"], 1920 + 1)
        payload = cf.is_float_available_payload(True)
        self.assertTrue(payload["click_through_hole"])

    def test_tray_geom_side_look4(self) -> None:
        """KAN-525: side rail beside the capture ring (under-ring Rejected)."""
        monitors = [
            {
                "id": "mon1",
                "label": "Monitor 1 (primary)",
                "bbox": [0, 0, 1920, 1080],
                "is_primary": True,
            }
        ]
        dock = ring.dock_geom_for_bbox(
            [100, 80, 800, 500],
            virtual={"left": 0, "top": 0, "width": 1920, "height": 1080},
            monitors=monitors,
            side="east",
            collapsed=False,
        )
        self.assertEqual(dock["placement"], "side")
        self.assertEqual(dock["host"], "native_toolwindow")
        self.assertEqual(dock["side"], "east")
        self.assertGreaterEqual(dock["width"], ring.MIN_TRAY_HWND_W)
        self.assertGreaterEqual(dock["height"], ring.BTN_H)
        # East of the ring right edge.
        self.assertGreaterEqual(dock["x"], 800)
        self.assertLessEqual(dock["x"] + dock["width"], 1920)
        # Near right edge → flip west.
        edge = ring.dock_geom_for_bbox(
            [1700, 100, 1880, 500],
            virtual={"left": 0, "top": 0, "width": 1920, "height": 1080},
            monitors=monitors,
            side="east",
            collapsed=False,
        )
        self.assertEqual(edge["placement"], "side")
        self.assertEqual(edge["side"], "west")
        self.assertLessEqual(edge["x"] + edge["width"], 1700)

    def test_tray_collapsed_keeps_min_hit(self) -> None:
        dock = ring.dock_geom_for_bbox(
            [200, 120, 700, 520],
            virtual={"left": 0, "top": 0, "width": 1920, "height": 1080},
            monitors=[
                {
                    "id": "mon1",
                    "bbox": [0, 0, 1920, 1080],
                    "is_primary": True,
                }
            ],
            side="east",
            collapsed=True,
        )
        self.assertTrue(dock["collapsed"])
        self.assertEqual(dock["placement"], "side")
        self.assertGreaterEqual(dock["width"], ring.MIN_TRAY_HWND_W)
        self.assertGreaterEqual(dock["height"], ring.BTN_H)


class CharterRingNativeTests(unittest.TestCase):
    def test_nudge_and_resize_bbox(self) -> None:
        b = [100, 100, 500, 400]
        self.assertEqual(ring.nudge_bbox(b, 10, -5), [110, 95, 510, 395])
        bigger = ring.resize_bbox(b, 40, 20)
        self.assertEqual(bigger[2] - bigger[0], 440)
        self.assertEqual(bigger[3] - bigger[1], 320)

    def test_apply_drag_delta_move_and_corners(self) -> None:
        b = [200, 150, 600, 450]
        moved = ring.apply_drag_delta(b, "move", 30, -20)
        self.assertEqual(moved, [230, 130, 630, 430])
        se = ring.apply_drag_delta(b, "se", 50, 40)
        self.assertEqual(se, [200, 150, 650, 490])
        nw = ring.apply_drag_delta(b, "nw", 40, 30)
        self.assertEqual(nw, [240, 180, 600, 450])
        # Min capture clamp when shrinking SE toward zero.
        tiny = ring.apply_drag_delta(b, "se", -900, -900)
        self.assertEqual(tiny[2] - tiny[0], ring.MIN_CAPTURE_W)
        self.assertEqual(tiny[3] - tiny[1], ring.MIN_CAPTURE_H)

    def test_bar_hit_mode_corners_and_move(self) -> None:
        self.assertEqual(ring.bar_hit_mode("n", 5, 2, 400, 8), "nw")
        self.assertEqual(ring.bar_hit_mode("n", 390, 2, 400, 8), "ne")
        self.assertEqual(ring.bar_hit_mode("n", 200, 2, 400, 8), "move")
        self.assertEqual(ring.bar_hit_mode("e", 2, 5, 8, 400), "ne")
        self.assertEqual(ring.bar_hit_mode("e", 2, 390, 8, 400), "se")
        self.assertEqual(ring.bar_hit_mode("w", 2, 200, 8, 400), "move")

    def test_dock_stays_glued_on_side_flip(self) -> None:
        """KAN-530: near right edge → west, still attached to hole (not screen-left)."""
        monitors = [
            {
                "id": "mon1",
                "bbox": [0, 0, 1920, 1080],
                "is_primary": True,
            }
        ]
        virt = {"left": 0, "top": 0, "width": 1920, "height": 1080}
        hole = [1600, 200, 1880, 600]
        dock = ring.dock_geom_for_bbox(
            hole, virtual=virt, monitors=monitors, side="east", collapsed=False
        )
        self.assertEqual(dock["side"], "west")
        self.assertLessEqual(dock["x"] + dock["width"] + 1, hole[0])
        # Glued: right edge of tray within gap of hole left.
        self.assertGreaterEqual(dock["x"] + dock["width"], hole[0] - ring.TRAY_GAP - 2)
        self.assertGreater(dock["x"], 100)  # not clamped to screen far-left

    def test_max_capture_covers_typical_window(self) -> None:
        from plans.charter_float import max_capture_for_work

        mw, mh = max_capture_for_work(
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
            [{"id": "m", "bbox": [0, 0, 1920, 1080], "is_primary": True}],
        )
        self.assertGreaterEqual(mw, 1400)
        self.assertGreaterEqual(mh, 800)
        big = ring.apply_drag_delta([100, 100, 500, 400], "se", 2000, 2000)
        self.assertGreaterEqual(big[2] - big[0], 1400)

    def test_verb_hover_tips_defined(self) -> None:
        for verb in ring._VERBS_EXPANDED:
            self.assertIn(verb, ring._VERB_TIPS)
            self.assertTrue(str(ring._VERB_TIPS[verb]).strip())

    def test_tip_readable_size_constants_kan532(self) -> None:
        # KAN-532 — larger tip font/box than the old 28px system-default tip.
        self.assertGreaterEqual(ring.TIP_FONT_PX, 15)
        self.assertGreaterEqual(ring.TIP_PAD_Y, 8)
        self.assertGreaterEqual(ring.TIP_MIN_W, 140)
        self.assertGreaterEqual(ring.TIP_PAD_X, 12)
        src = (ROOT / "plans" / "charter_ring_native.py").read_text(encoding="utf-8")
        self.assertIn("_ensure_tip_font", src)
        self.assertIn("_measure_tip_text", src)
        self.assertIn("CreateFontW", src)
        self.assertIn("GetTextExtentPoint32W", src)
        self.assertNotIn("th = 28", src)
        self.assertNotIn("len(text) * 7", src)

    def test_default_capture_bbox_on_primary(self) -> None:
        monitors = [
            {
                "id": "mon1",
                "bbox": [0, 0, 1920, 1080],
                "is_primary": True,
            }
        ]
        bbox = ring.default_capture_bbox(
            virtual={"left": 0, "top": 0, "width": 1920, "height": 1080},
            monitors=monitors,
        )
        self.assertEqual(len(bbox), 4)
        self.assertLess(bbox[2], 1920)
        self.assertLess(bbox[3], 1080)


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
        self.assertFalse(out["session"]["ticket_bound"])
        self.assertFalse(out["writes_jira"])

    def test_float_still_level_scoped(self) -> None:
        started = ms.start_session("Float still", ticket_bound=False, agent_assist=False)
        sid = started["session"]["id"]
        with mock.patch("PIL.ImageGrab.grab") as grab:
            fake = mock.MagicMock()
            fake.size = (300, 200)

            def _save(path, format=None):  # noqa: A002
                Path(path).write_bytes(b"PNG")

            fake.save.side_effect = _save
            grab.return_value = fake
            still = ms.attach_still(sid, screen_bbox=[10, 20, 310, 220])
        self.assertTrue(still["still"]["captured"])
        path = Path(still["still"]["path"])
        expected_root = plans_dir("OFFICIAL") / "sessions"
        self.assertEqual(path.resolve().parent.parent, expected_root.resolve())
        ms.end_session(sid)


class CharterFloatUiMarkersTests(unittest.TestCase):
    def test_desktop_float_markers_desk161(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        self.assertIn("desk161", html)
        self.assertIn("desk161", desk)
        self.assertIn("DESK_V = \"desk161\"", desk)
        self.assertIn("native_toolwindow", desk)
        self.assertIn("g_tray_look4", desk)
        self.assertIn("charter_float_set_tray", desk)
        self.assertIn("show_side_tray", desk)
        self.assertIn("destroy_side_tray", desk)
        self.assertIn("set_geom_callback", desk)
        self.assertIn("_on_ring_geom", desk)
        self.assertIn("fresh_tray", desk)
        # Must never punch WebView2 with SetWindowRgn (crash / opaque fill).
        self.assertNotIn("apply_hollow_window_region", desk)
        # KAN-525: no second pywebview Charter Frame / hide-reuse tray.
        self.assertNotIn("FLOAT_URL", desk)
        self.assertNotIn("_float_window", desk)
        self.assertNotIn("win.hide()", desk)
        self.assertIn("charter_float_drag_by", desk)
        self.assertIn("data-manual-session-chip", html)
        self.assertIn("data-manual-session-end", html)
        self.assertIn("data-manual-session-still", html)
        self.assertIn("data-manual-session-note", html)
        self.assertIn("data-manual-resume", html)
        self.assertIn('>Resume</button>', html)  # chip re-arm label
        self.assertIn("captureStillFromManualChip", js)
        self.assertIn("addNoteFromManualChip", js)
        self.assertIn("syncManualEndVisible", js)
        self.assertIn("note_focus", js)
        # Resume stays available while session open (not gated on float-active).
        resume_fn = js.split("function setManualResumeUi", 1)[1].split(
            "function showManualSessionChip", 1
        )[0]
        self.assertIn("manualResumeCharter.hidden = !on;", resume_fn)
        self.assertNotIn("charterOsFloatActive", resume_fn)
        self.assertIn("setManualResumeUi(session)", js)
        self.assertIn("__manualFloatFailStatus", js)
        self.assertIn("6000", js)
        ring_src = (ROOT / "plans" / "charter_ring_native.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"placement": "side"', ring_src)
        self.assertIn("native_toolwindow", ring_src)
        self.assertIn("show_side_tray", ring_src)
        self.assertIn("destroy_side_tray", ring_src)
        self.assertIn("WS_EX_TOOLWINDOW", ring_src)
        self.assertIn("_paint_tray", ring_src)
        self.assertIn("_draw_icon", ring_src)
        # KAN-528 native drag/resize on ring thread.
        self.assertIn("_bar_wndproc", ring_src)
        self.assertIn("apply_drag_delta", ring_src)
        self.assertIn("bar_hit_mode", ring_src)
        self.assertIn("RING_BW", ring_src)
        self.assertIn("_live_place_unlocked", ring_src)
        self.assertIn("set_geom_callback", ring_src)
        # KAN-530 tray glue + hover tips + larger max.
        self.assertIn("_VERB_TIPS", ring_src)
        self.assertIn("_schedule_tip", ring_src)
        self.assertIn("_remember_dock_context", ring_src)
        self.assertIn("max_capture_for_work", ring_src)
        self.assertIn("glued", ring_src)
        self.assertIn("KAN-530", desk)
        # KAN-532 readable tip size.
        self.assertIn("TIP_FONT_PX", ring_src)
        self.assertIn("_ensure_tip_font", ring_src)
        self.assertIn("KAN-532", ring_src)
        # Owner-drawn Look 4 icons — no stock Win32 BUTTON chrome.
        self.assertNotIn('"BUTTON"', ring_src)
        # Under-ring must not remain the product placement lock.
        self.assertNotIn('"placement": "under_ring"', ring_src)
        # Manual UX: Start must not closeArea; library reopen must not toggle-close.
        self.assertIn("function ensureAreaOpen", js)
        self.assertIn('ensureAreaOpen("manual")', js)
        start_fn = js.split("async function startManualSession()", 1)[1].split(
            "async function endManualSessionFromFrame()", 1
        )[0]
        self.assertNotIn("closeArea()", start_fn)
        self.assertIn("session_already_open", start_fn)
        self.assertIn('openAreaName === "manual"', js)
        self.assertIn("function setManualResumeUi", js)
        self.assertIn("function showManualSessionChip", js)
        self.assertIn("Resume Charter", js)
        self.assertIn("setManualResumeUi(openData.session)", js)
        self.assertNotIn("await showCharterFrame(openData.session)", js)
        show_fn = js.split("async function showCharterFrame(session)", 1)[1].split(
            "async function hideCharterFrame()", 1
        )[0]
        self.assertIn("Look 4", show_fn)
        self.assertIn("no silent in-app", show_fn)
        self.assertIn("showManualSessionChip", show_fn)
        self.assertIn("charterFrameRoot.hidden = true", show_fn)
        self.assertIn('setManualLoopStage("idle")', show_fn)
        self.assertIn("Do NOT set recording yet", show_fn)
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        self.assertNotIn(
            "#app-section-manual[data-loop-stage=\"recording\"] .manual-primary {\n"
            "  opacity: 0.72;\n"
            "  pointer-events: none;\n"
            "}",
            css,
        )
        self.assertIn("#manual-start", css)
        self.assertIn("manual-session-chip-note-row", css)

    def test_api_start_charter_only(self) -> None:
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
                self.assertEqual(res.json()["status"], "ok")
                sid = res.json()["session"]["id"]
                client.post(
                    f"/api/manual-sessions/{sid}/cancel", json={"confirm": True}
                )


if __name__ == "__main__":
    unittest.main()
