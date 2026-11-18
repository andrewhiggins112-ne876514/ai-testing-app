"""KAN-241 / KAN-242 — H1 manual session capture design only (FR-MAN-1)."""
from __future__ import annotations

from pathlib import Path

from plans.manual_session_design import (
    REQUIRED_SECTIONS,
    assert_design_complete,
    design_doc_path,
    design_outline,
    missing_doc_headings,
)

ROOT = Path(__file__).resolve().parents[1]


def test_design_outline_covers_catalogue_ac() -> None:
    outline = design_outline()
    assert outline["fr"] == "FR-MAN-1"
    assert outline["story"] == "KAN-241"
    assert outline["recorder_shipped"] is False
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"]
    charter = outline["sections"]["charter_start"]
    assert charter["off_by_default"] is True
    assert charter["writes_jira_on_start"] is False
    recorded = outline["sections"]["what_is_recorded"]
    assert "keystrokes" in recorded["never"]
    assert "silent_video" in recorded["never"]
    propose = outline["sections"]["how_bug_is_proposed"]
    assert propose["review_first"] is True
    assert propose["product_bug_only_for_create_bug"] is True
    confirm = outline["sections"]["confirm"]
    assert confirm["two_step"] is True
    assert confirm["cancel_writes_nothing"] is True
    isolation = outline["sections"]["official_secret_separation"]
    assert isolation["list_active_level_only"] is True
    assert isolation["no_credentials_in_session_file"] is True
    cr = outline["sections"]["council_cr_charter_frame"]
    assert cr["agent_assist_toggle"] is True
    assert cr["mist_toggle"] is True
    assert cr["agent_assist_default"] == "off"
    assert cr["mist_default"] == "off"
    assert cr["live_circles"] == "parked_fr_man_2"
    assert outline["build_order"][0] == "plans_ia_tidy"


def test_design_doc_exists_with_required_headings() -> None:
    path = design_doc_path()
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "FR-MAN-1" in text
    assert "Does not ship a recorder" in text or "no recorder ships" in text.lower()
    assert "Agent assist" in text
    assert "FR-MAN-2" in text
    assert missing_doc_headings(text) == []


def test_assert_design_complete_ok() -> None:
    result = assert_design_complete()
    assert result["status"] == "ok"
    assert result["recorder_shipped"] is False


def test_no_session_recorder_shipped_in_product() -> None:
    """H1 must not add a live recorder API or desktop start control."""
    forbidden_snippets = (
        "/api/plans/manual-session/start",
        "/api/plans/sessions/start",
        "manual-session-start",
        "plan-session-start-btn",
        "start_manual_session(",
    )
    scan_paths = [
        ROOT / "main.py",
        ROOT / "ui" / "desktop" / "desktop.js",
        ROOT / "ui" / "desktop" / "index.html",
        ROOT / "plans",
    ]
    hits: list[str] = []
    for path in scan_paths:
        if path.is_file():
            body = path.read_text(encoding="utf-8")
            for snip in forbidden_snippets:
                if snip in body and "manual_session_design" not in path.name:
                    hits.append(f"{path.name}:{snip}")
        elif path.is_dir():
            for py in path.glob("*.py"):
                if py.name == "manual_session_design.py":
                    continue
                body = py.read_text(encoding="utf-8")
                for snip in forbidden_snippets:
                    if snip in body:
                        hits.append(f"{py.name}:{snip}")
    assert hits == [], f"recorder surface leaked into product: {hits}"
