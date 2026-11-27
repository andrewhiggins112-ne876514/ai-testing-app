"""KAN-352 / KAN-353 — Documents toolbar scope, Heal confirm copy, Lab Advanced disclosure."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Track5DocsHealLabDisclosureTests(unittest.TestCase):
    def test_documents_heal_lab_disclosure_markers_desk138(self) -> None:
        html = (ROOT / "ui" / "desktop" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "desktop" / "desktop.js").read_text(encoding="utf-8")
        desk = (ROOT / "desktop_app.py").read_text(encoding="utf-8")

        self.assertIn("desk138", html)
        self.assertIn("desk138", desk)
        self.assertIn("desktop.css?v=desk138", html)
        self.assertIn("desktop.js?v=desk138", html)

        documents = html.split('id="app-section-documents"', 1)[1].split(
            'id="app-section-heal"', 1
        )[0]
        heal = html.split('id="app-section-heal"', 1)[1].split(
            'id="app-section-desktop"', 1
        )[0]
        desktop = html.split('id="app-section-desktop"', 1)[1].split(
            'id="app-section-plans"', 1
        )[0]
        suites = html.split('id="app-section-suites"', 1)[1].split(
            'id="app-section-sandboxes"', 1
        )[0]
        sandboxes = html.split('id="app-section-sandboxes"', 1)[1].split(
            'id="app-drawer-toggle"', 1
        )[0]

        # --- Documents: tab-scoped Parse / Refresh ---
        self.assertIn('data-documents-toolbar-scope="1"', documents)
        self.assertIn('id="doc-parse"', documents)
        self.assertIn('data-show="propose"', documents)
        self.assertIn('id="doc-uploads-refresh"', documents)
        self.assertIn('data-show="uploads"', documents)
        parse_btn = documents.split('id="doc-parse"', 1)[1].split(">", 1)[0]
        refresh_btn = documents.split('id="doc-uploads-refresh"', 1)[1].split(">", 1)[0]
        self.assertIn('data-show="propose"', parse_btn)
        self.assertNotIn("hidden", parse_btn)
        self.assertIn('data-show="uploads"', refresh_btn)
        self.assertIn("hidden", refresh_btn)
        # Confirm / Decline stay off the scan row (in detail).
        diff_table = documents.split('id="doc-diff-scan"', 1)[1].split("</table>", 1)[0]
        self.assertNotIn('id="doc-confirm"', diff_table)
        self.assertNotIn('id="doc-decline"', diff_table)
        detail = documents.split('id="doc-diff-detail"', 1)[1].split(
            'id="doc-panel-uploads"', 1
        )[0]
        self.assertIn('id="doc-confirm"', detail)
        self.assertIn('id="doc-decline"', detail)
        self.assertIn("function showDocPanel", js)
        self.assertIn('#doc-chrome-toolbar [data-show]', js)

        # --- Heal: confirm copy names count + files are not written; no bulk Reject ---
        self.assertIn('data-heal-confirm-copy="1"', heal)
        self.assertIn('data-heal-confirm="1"', heal)
        self.assertIn('data-heal-bulk="1"', heal)
        self.assertIn('id="heal-bulk-approve"', heal)
        self.assertIn('id="heal-reject"', heal)
        bulk = heal.split('data-heal-bulk="1"', 1)[1].split("</span>", 1)[0]
        self.assertIn('id="heal-bulk-approve"', bulk)
        self.assertNotIn("Reject selected", bulk)
        self.assertNotIn("heal-bulk-reject", heal)
        self.assertNotIn("heal-bulk-reject", js)
        self.assertIn("Files are not written", js)
        self.assertIn("Approve ", js)
        self.assertIn(" proposals?", js)
        self.assertIn("Reject is not part of this step", js)
        self.assertIn("Confirm approve", js)
        # Reject stays on focused detail actions only.
        actions = heal.split('data-heal-actions="1"', 1)[1].split("</div>", 1)[0]
        self.assertIn('id="heal-reject"', actions)
        heal_list = heal.split('id="heal-list"', 1)[1].split('id="heal-detail"', 1)[0]
        self.assertNotIn('id="heal-reject"', heal_list)

        # --- Lab: Desktop / Suites / Sandboxes Advanced closed disclosure ---
        for section, adv_id, marker in (
            (desktop, "desk-advanced", "data-desk-detail-disclosure"),
            (suites, "suite-advanced", "data-suite-detail-disclosure"),
            (sandboxes, "ms-advanced", "data-ms-detail-disclosure"),
        ):
            self.assertIn('data-lab-detail-disclosure="1"', section, msg=adv_id)
            self.assertIn(f'{marker}="1"', section, msg=adv_id)
            # Opening <details …> must not start open.
            before, after = section.split(f'id="{adv_id}"', 1)
            open_tag = before.rsplit("<details", 1)[-1] + 'id="' + adv_id + '"' + after.split(">", 1)[0]
            self.assertNotRegex(open_tag, r"\bopen\b", msg=adv_id)
            summary_block = after.split("</details>", 1)[0]
            self.assertIn("<summary>Advanced</summary>", summary_block, msg=adv_id)

        # Primary actions stay outside Advanced.
        desk_detail = desktop.split('data-desk-detail="1"', 1)[1].split(
            'id="desk-advanced"', 1
        )[0]
        self.assertIn('id="desk-save"', desk_detail)
        desk_adv = desktop.split('id="desk-advanced"', 1)[1]
        self.assertNotIn('id="desk-save"', desk_adv)
        self.assertNotIn('id="desk-smoke"', desk_adv)

        suite_detail = suites.split('data-suite-detail="1"', 1)[1].split(
            'id="suite-advanced"', 1
        )[0]
        self.assertIn('id="suite-run-focused"', suite_detail)
        suite_adv = suites.split('id="suite-advanced"', 1)[1]
        self.assertIn('id="suite-import"', suite_adv)
        self.assertNotIn('id="suite-run-focused"', suite_adv)

        ms_detail = sandboxes.split('data-ms-detail="1"', 1)[1].split(
            'id="ms-advanced"', 1
        )[0]
        self.assertIn('id="ms-upsert"', ms_detail)
        self.assertIn('id="ms-remove"', ms_detail)
        ms_adv = sandboxes.split('id="ms-advanced"', 1)[1]
        self.assertNotIn('id="ms-upsert"', ms_adv)
        self.assertNotIn('id="ms-remove"', ms_adv)

        # No-regression: Charter Frame + no second App rail on Plans.
        self.assertIn('data-charter-frame="1"', html)
        self.assertIn('id="charter-frame-root"', html)
        plans = html.split('id="app-section-plans"', 1)[1].split(
            'id="app-section-manual"', 1
        )[0]
        self.assertNotIn("data-settings-section-rail", plans)
        self.assertNotIn("data-plan-section-rail", plans)


if __name__ == "__main__":
    unittest.main()
