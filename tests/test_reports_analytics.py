"""KAN-384 / KAN-385 — Reports visual analytics from local report JSON."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402
from reports.analytics import build_report_analytics  # noqa: E402
from reports.exporter import get_saved_report  # noqa: E402


class ReportAnalyticsUnitTests(unittest.TestCase):
    def test_empty_payload_quiet(self) -> None:
        empty = build_report_analytics(None)
        self.assertFalse(empty["has_metrics"])
        self.assertIsNone(empty["pass_fail"])
        self.assertIsNone(empty["coverage"])
        self.assertIn("No chart metrics", empty["empty_hint"])

        blank = build_report_analytics({"message": "No JSON found"})
        self.assertFalse(blank["has_metrics"])

        zeroish = build_report_analytics(
            {"sections": {"summary": {"passed": 0, "failed": 0, "stories_covered": 0}}}
        )
        self.assertFalse(zeroish["has_metrics"])

    def test_pass_fail_and_coverage_from_sections(self) -> None:
        payload = {
            "sections": {
                "summary": {
                    "passed": 3,
                    "failed": 1,
                    "tests_passed": 3,
                    "tests_failed": 1,
                    "stories_covered": 2,
                    "steps": [
                        {"status": "pass", "action": "a"},
                        {"status": "pass", "action": "b"},
                        {"status": "pass", "action": "c"},
                        {
                            "status": "fail",
                            "action": "d",
                            "failure_class": "selector",
                        },
                    ],
                },
                "stories": {"keys": ["KAN-1", "KAN-2"], "count": 2},
                "bugs": {
                    "counts_by_story": {"KAN-1": 2, "KAN-2": 1},
                    "items": [],
                },
            },
            "result": {"duration_ms": 4500},
        }
        analytics = build_report_analytics(payload)
        self.assertTrue(analytics["has_metrics"])
        self.assertEqual(analytics["pass_fail"]["passed"], 3)
        self.assertEqual(analytics["pass_fail"]["failed"], 1)
        self.assertEqual(analytics["pass_fail"]["pass_rate_percent"], 75.0)
        self.assertEqual(analytics["coverage"]["stories_covered"], 2)
        self.assertEqual(analytics["coverage"]["stories"], ["KAN-1", "KAN-2"])
        self.assertEqual(analytics["duration"]["seconds"], 4.5)
        self.assertEqual(analytics["failure_classes"][0]["label"], "selector")
        self.assertEqual(analytics["bugs_by_story"][0]["story"], "KAN-1")
        self.assertEqual(analytics["bugs_by_story"][0]["count"], 2)


class ReportAnalyticsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_reports = os.environ.get("AI_TESTING_REPORTS")
        self._old_settings = os.environ.get("AI_TESTING_SETTINGS")
        self.reports = Path(tempfile.mkdtemp())
        self.settings_dir = Path(tempfile.mkdtemp())
        os.environ["AI_TESTING_REPORTS"] = str(self.reports)
        os.environ["AI_TESTING_SETTINGS"] = str(self.settings_dir / "settings.json")
        self.client = TestClient(app)

    def tearDown(self) -> None:
        if self._old_reports is None:
            os.environ.pop("AI_TESTING_REPORTS", None)
        else:
            os.environ["AI_TESTING_REPORTS"] = self._old_reports
        if self._old_settings is None:
            os.environ.pop("AI_TESTING_SETTINGS", None)
        else:
            os.environ["AI_TESTING_SETTINGS"] = self._old_settings

    def test_detail_includes_analytics(self) -> None:
        (self.reports / "charted.md").write_text("# Charted\n", encoding="utf-8")
        (self.reports / "charted.json").write_text(
            json.dumps(
                {
                    "timestamp": "2026-11-27T12:00:00",
                    "request": "demo charts",
                    "sections": {
                        "summary": {
                            "passed": 2,
                            "failed": 1,
                            "stories_covered": 1,
                            "steps": [
                                {"status": "pass"},
                                {"status": "pass"},
                                {"status": "fail", "classification": "timeout"},
                            ],
                        },
                        "stories": {"keys": ["KAN-384"], "count": 1},
                    },
                    "result": {"duration_seconds": 12},
                }
            ),
            encoding="utf-8",
        )
        detail = get_saved_report("charted")
        self.assertTrue(detail["found"])
        self.assertTrue(detail["analytics"]["has_metrics"])
        self.assertEqual(detail["analytics"]["pass_fail"]["failed"], 1)
        self.assertEqual(detail["analytics"]["coverage"]["stories_covered"], 1)

        res = self.client.get("/api/reports/charted")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("analytics", body)
        self.assertTrue(body["analytics"]["has_metrics"])
        self.assertEqual(body["analytics"]["pass_fail"]["passed"], 2)
        self.assertEqual(body["analytics"]["coverage"]["stories"], ["KAN-384"])

    def test_empty_json_report_quiet_charts(self) -> None:
        (self.reports / "bare.md").write_text("# Bare\n", encoding="utf-8")
        (self.reports / "bare.json").write_text(
            json.dumps({"timestamp": "2026-11-27T12:00:00", "result": {}}),
            encoding="utf-8",
        )
        res = self.client.get("/api/reports/bare")
        self.assertEqual(res.status_code, 200)
        analytics = res.json()["analytics"]
        self.assertFalse(analytics["has_metrics"])
        self.assertIsNone(analytics["pass_fail"])
        self.assertIn("No chart metrics", analytics["empty_hint"])


class ReportAnalyticsDesktopMarkers(unittest.TestCase):
    def test_reports_charts_markers_desk140(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk140", html)
        self.assertIn("desk140", desk)
        self.assertIn("desktop.css?v=desk140", html)
        self.assertIn("desktop.js?v=desk140", html)

        reports = html.split('id="app-section-reports"', 1)[1].split(
            'id="app-section-documents"', 1
        )[0]
        self.assertIn('data-rpt-charts="1"', reports)
        self.assertIn('data-reports-analytics="1"', reports)
        self.assertIn('id="rpt-charts"', reports)
        self.assertIn('id="rpt-chart-pass-fail"', reports)
        self.assertIn('id="rpt-chart-coverage"', reports)
        self.assertIn('data-rpt-charts-empty="1"', reports)
        self.assertIn("No chart metrics in this report.", reports)

        self.assertIn("renderReportCharts", js)
        self.assertIn("clearReportCharts", js)
        self.assertIn("data.analytics", js)
        self.assertIn(".rpt-charts", css)
        self.assertIn(".rpt-chart-bar-fill.is-pass", css)
        self.assertIn(".rpt-chart-bar-fill.is-fail", css)
        # Markdown + JSON viewers share the same 240px readable height.
        self.assertIn("#rpt-markdown.report-viewer", css)
        self.assertIn("min-height: 240px", css)
        self.assertIn("height: 240px", css)


if __name__ == "__main__":
    unittest.main()
