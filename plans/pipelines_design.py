"""H2 / FR-CI-1 — pipelines section design outline (KAN-243).

Design-only: no CI integration is shipped. The outline mirrors
``docs/design/H2_PIPELINES_SECTION.md`` so tests can assert the
contract without reading the whole markdown body.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

DESIGN_DOC = Path(__file__).resolve().parents[1] / "docs" / "design" / "H2_PIPELINES_SECTION.md"

# Catalogue AC sections that the design must cover.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "what_pipeline_record_shows",
    "what_it_will_not_do",
    "secrets_stay_local",
)

# Markdown headings that must appear in the design doc (substring match).
DOC_HEADING_MARKERS: tuple[str, ...] = (
    "What a pipeline record shows",
    "What it will not do",
    "Secrets stay local",
)


def design_outline() -> dict[str, Any]:
    """Machine-readable H2 design summary for tests and later implementers."""
    return {
        "story": "KAN-243",
        "test": "KAN-244",
        "fr": "FR-CI-1",
        "band": "FUTURE",
        "ci_integration_shipped": False,
        "design_doc": str(DESIGN_DOC.as_posix()),
        "sections": {
            "what_pipeline_record_shows": {
                "required_fields": [
                    "display_name",
                    "provider_kind",
                    "external_id",
                    "last_known_status",
                    "security_level",
                ],
                "optional_fields": [
                    "link_out_url",
                    "plan_id",
                    "tag",
                    "last_sync_at",
                    "last_external_run_ref",
                ],
                "app_area": "Pipelines",
                "not_a_case_or_suite_run": True,
                "storage_sketch": "plans/{LEVEL}/pipelines/{pipeline_id}.json",
            },
            "what_it_will_not_do": {
                "replace_in_app_suite": False,
                "auto_import_ci_yaml_as_cases": False,
                "ci_green_equals_local_pass": False,
                "cloud_headed_browser": False,
                "embed_ci_console": False,
                "silent_jira_or_heal_webhooks": False,
                "cross_level_merge": False,
                "distinct_from_g12_local_schedule": True,
            },
            "secrets_stay_local": {
                "tokens_in_level_credentials_only": True,
                "no_tokens_in_pipeline_json": True,
                "no_tokens_in_git_chat_installer": True,
                "export_redacts_tokens": True,
                "gdpr_wipe_includes_pipelines_and_ci_creds": True,
            },
        },
        "out_of_scope_this_story": [
            "shipping_ci_integration",
            "mandatory_single_ci_vendor",
            "replacing_in_app_suite",
            "cloud_hosted_schedules",
            "h3_multi_pc_share",
            "h1_recorder",
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
    assert outline["ci_integration_shipped"] is False, "H2 must not ship CI integration"
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"], f"missing section {key}"
    path = design_doc_path()
    assert path.is_file(), f"design doc missing: {path}"
    missing = missing_doc_headings()
    assert not missing, f"design doc missing headings: {missing}"
    return {
        "status": "ok",
        "ci_integration_shipped": False,
        "design_doc": str(path.as_posix()),
        "sections": list(REQUIRED_SECTIONS),
    }
