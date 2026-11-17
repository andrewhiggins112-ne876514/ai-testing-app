"""H1 / FR-MAN-1 — manual session capture design outline (KAN-241).

Design-only: no session recorder is shipped. The outline mirrors
``docs/design/H1_MANUAL_SESSION_CAPTURE.md`` so tests can assert the
contract without reading the whole markdown body.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

DESIGN_DOC = Path(__file__).resolve().parents[1] / "docs" / "design" / "H1_MANUAL_SESSION_CAPTURE.md"

# Catalogue AC sections that the design must cover.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "charter_start",
    "what_is_recorded",
    "how_bug_is_proposed",
    "confirm",
    "official_secret_separation",
)

# Markdown headings that must appear in the design doc (substring match).
DOC_HEADING_MARKERS: tuple[str, ...] = (
    "Charter start",
    "What is recorded",
    "How a bug",
    "Confirm",
    "OFFICIAL / SECRET",
)


def design_outline() -> dict[str, Any]:
    """Machine-readable H1 design summary for tests and later implementers."""
    return {
        "story": "KAN-241",
        "test": "KAN-242",
        "fr": "FR-MAN-1",
        "band": "FUTURE",
        "recorder_shipped": False,
        "design_doc": str(DESIGN_DOC.as_posix()),
        "sections": {
            "charter_start": {
                "required_fields": ["charter", "security_level"],
                "optional_fields": ["plan_id", "case_id", "jira_key"],
                "off_by_default": True,
                "writes_jira_on_start": False,
            },
            "what_is_recorded": {
                "default_on": ["timestamped_notes"],
                "opt_in": ["screenshots", "page_context_when_known"],
                "never": [
                    "keystrokes",
                    "clipboard",
                    "voice",
                    "silent_video",
                    "secrets",
                    "cross_level_merge",
                ],
                "storage_sketch": "plans/{LEVEL}/sessions/{session_id}.json",
            },
            "how_bug_is_proposed": {
                "review_first": True,
                "propose_options": [
                    "create_bug_via_defect_packet",
                    "comment_on_linked_story",
                    "attach_local_case_run_note",
                ],
                "reuse": ["plans/defect_packet.py", "FR-JIRA-4"],
                "product_bug_only_for_create_bug": True,
            },
            "confirm": {
                "two_step": True,
                "fr": ["FR-AGENT-4", "FR-JIRA-5"],
                "audit": "jira_write_audit.jsonl",
                "cancel_writes_nothing": True,
            },
            "official_secret_separation": {
                "list_active_level_only": True,
                "level_paths_isolated": True,
                "no_credentials_in_session_file": True,
                "gdpr_wipe_includes_sessions": True,
            },
        },
        "out_of_scope_this_story": [
            "shipping_recorder",
            "voice_g10",
            "cloud_sync",
            "replacing_b7_notes",
            "ci_pipelines_h2",
        ],
    }


def design_doc_path() -> Path:
    return DESIGN_DOC


def design_doc_text() -> str:
    path = design_doc_path()
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def missing_doc_headings(text: str | None = None) -> list[str]:
    body = text if text is not None else design_doc_text()
    return [m for m in DOC_HEADING_MARKERS if m not in body]


def assert_design_complete() -> dict[str, Any]:
    """Return a verification payload; raises AssertionError if incomplete."""
    outline = design_outline()
    assert outline["recorder_shipped"] is False, "H1 must not ship a recorder"
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"], f"missing section {key}"
    path = design_doc_path()
    assert path.is_file(), f"design doc missing: {path}"
    missing = missing_doc_headings()
    assert not missing, f"design doc missing headings: {missing}"
    return {
        "status": "ok",
        "recorder_shipped": False,
        "design_doc": str(path.as_posix()),
        "sections": list(REQUIRED_SECTIONS),
    }
