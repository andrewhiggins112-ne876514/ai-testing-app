"""H3 / FR-SEC-1 — shared use without a cloud design outline (KAN-245).

Design-only: no network / share service is shipped. The outline mirrors
``docs/design/H3_SHARED_USE_WITHOUT_CLOUD.md`` so tests can assert the
contract without reading the whole markdown body.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

DESIGN_DOC = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "design"
    / "H3_SHARED_USE_WITHOUT_CLOUD.md"
)

# Catalogue AC sections that the design must cover.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "local_on_prem_options",
    "security_limits",
)

# Markdown headings that must appear in the design doc (substring match).
DOC_HEADING_MARKERS: tuple[str, ...] = (
    "Local / on-prem options",
    "Security limits",
)


def design_outline() -> dict[str, Any]:
    """Machine-readable H3 design summary for tests and later implementers."""
    return {
        "story": "KAN-245",
        "test": "KAN-246",
        "fr": "FR-SEC-1",
        "band": "FUTURE",
        "network_service_shipped": False,
        "cloud_multi_tenant_required": False,
        "design_doc": str(DESIGN_DOC.as_posix()),
        "sections": {
            "local_on_prem_options": {
                "options": [
                    "export_pack_f6",
                    "backup_copy_e4",
                    "future_shared_folder",
                ],
                "related_not_share_channel": [
                    "second_pc_installer_g11",
                    "jira_tickets",
                ],
                "future_shared_folder_shipped": False,
                "storage_sketch": "plans/{LEVEL}/share_outbox/",
            },
            "security_limits": {
                "official_secret_isolation": True,
                "no_shared_credentials_across_pcs": True,
                "secrets_off_by_default_in_packs": True,
                "confirm_before_import_or_restore": True,
                "no_silent_background_sync": True,
                "no_mandatory_network_service": True,
                "refuse_cross_level_mix": True,
                "telemetry_off_by_default": True,
            },
        },
        "out_of_scope_this_story": [
            "shipping_network_or_share_service",
            "mandatory_cloud_multi_tenant",
            "picking_sync_vendor",
            "background_auto_sync",
            "h1_recorder",
            "h2_ci_integration",
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
    assert outline["network_service_shipped"] is False, (
        "H3 must not ship a network / share service"
    )
    assert outline["cloud_multi_tenant_required"] is False
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"], f"missing section {key}"
    opts = outline["sections"]["local_on_prem_options"]["options"]
    for required in ("export_pack_f6", "backup_copy_e4", "future_shared_folder"):
        assert required in opts, f"missing option {required}"
    path = design_doc_path()
    assert path.is_file(), f"design doc missing: {path}"
    missing = missing_doc_headings()
    assert not missing, f"design doc missing headings: {missing}"
    return {
        "status": "ok",
        "network_service_shipped": False,
        "design_doc": str(path.as_posix()),
        "sections": list(REQUIRED_SECTIONS),
        "options": list(opts),
    }
