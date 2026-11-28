"""KAN-357 — Advanced / About foot disclosures stay reachable under scan craft."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AdvancedFootReachableTests(unittest.TestCase):
    def test_advanced_foot_pinned_not_clipped_desk151(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "desktop" / "desktop.css").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk151", html)
        self.assertIn("desk151", desk)

        # Foot disclosures exist as siblings of the primary split inside area-work.
        for adv_id in (
            "doc-advanced",
            "heal-advanced",
            "desk-advanced",
            "suite-advanced",
            "ms-advanced",
            "rpt-advanced",
            "manual-advanced",
        ):
            self.assertIn(f'id="{adv_id}"', html, msg=adv_id)

        # CSS: primary fills remaining height; foot stays flex:0 (reachable).
        self.assertIn("KAN-357", css)
        self.assertIn(
            '.area-work[data-area-work="1"] > .lab-primary',
            css,
        )
        self.assertIn(
            '.area-work[data-area-work="1"] > .lab-advanced',
            css,
        )
        self.assertIn(
            '.area-work[data-area-work="1"] > .suite-advanced',
            css,
        )
        self.assertIn(
            '.area-work[data-area-work="1"] > .rpt-advanced',
            css,
        )
        self.assertIn(
            '.area-work[data-area-work="1"] > .manual-advanced',
            css,
        )

        # Extract the foot-pin block and assert flex contracts.
        pin = css.split("KAN-357", 1)[1].split(
            ".app-section[data-scan-craft=\"1\"] [data-scan-scroll=", 1
        )[0]
        self.assertIn("flex: 1 1 0", pin)
        self.assertIn("flex: 0 0 auto", pin)
        self.assertIn("max-height: min(40vh, 280px)", pin)

        # Split flex must shrink (0 basis), not auto — otherwise Advanced clips.
        no_outer = css.split(
            '.app-section[data-scan-craft="1"] [data-scan-no-outer-scroll="1"]',
            1,
        )[1].split("}", 1)[0]
        self.assertIn("flex: 1 1 0", no_outer)
        self.assertNotIn("flex: 1 1 auto", no_outer)

        # Documents panel must participate in the height chain.
        self.assertIn("#doc-primary.lab-primary > .doc-panel:not([hidden])", css)
        self.assertRegex(
            css,
            re.compile(
                r"#app-section-documents\[data-documents-layout-grammar=\"1\"\] "
                r"\.doc-grammar-split\s*\{[^}]*align-items:\s*stretch",
                re.S,
            ),
        )


if __name__ == "__main__":
    unittest.main()
