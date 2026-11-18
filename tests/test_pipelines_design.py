"""KAN-243 / KAN-244 — H2 pipelines section design only (FR-CI-1)."""
from __future__ import annotations

from pathlib import Path

from plans.pipelines_design import (
    REQUIRED_SECTIONS,
    assert_design_complete,
    design_doc_path,
    design_outline,
    missing_doc_headings,
)

ROOT = Path(__file__).resolve().parents[1]


def test_design_outline_covers_catalogue_ac() -> None:
    outline = design_outline()
    assert outline["fr"] == "FR-CI-1"
    assert outline["story"] == "KAN-243"
    assert outline["ci_integration_shipped"] is False
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"]
    record = outline["sections"]["what_pipeline_record_shows"]
    assert record["not_a_case_or_suite_run"] is True
    assert record["app_area"] == "Pipelines"
    assert "display_name" in record["required_fields"]
    assert "last_known_status" in record["required_fields"]
    wont = outline["sections"]["what_it_will_not_do"]
    assert wont["replace_in_app_suite"] is False
    assert wont["ci_green_equals_local_pass"] is False
    assert wont["distinct_from_g12_local_schedule"] is True
    secrets = outline["sections"]["secrets_stay_local"]
    assert secrets["tokens_in_level_credentials_only"] is True
    assert secrets["no_tokens_in_pipeline_json"] is True
    assert secrets["no_tokens_in_git_chat_installer"] is True


def test_design_doc_exists_with_required_headings() -> None:
    path = design_doc_path()
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "FR-CI-1" in text
    assert "Does not ship CI integration" in text or "no CI integration ships" in text.lower()
    assert missing_doc_headings(text) == []


def test_assert_design_complete_ok() -> None:
    result = assert_design_complete()
    assert result["status"] == "ok"
    assert result["ci_integration_shipped"] is False


def test_no_ci_integration_shipped_in_product() -> None:
    """H2 must not add a live Pipelines API or desktop CI sync control."""
    forbidden_snippets = (
        "/api/pipelines/",
        "/api/plans/pipelines/",
        "pipeline-sync-btn",
        "plan-pipeline-add-btn",
        "sync_pipeline_status(",
        "fetch_ci_status(",
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
                if snip in body and "pipelines_design" not in path.name:
                    hits.append(f"{path.name}:{snip}")
        elif path.is_dir():
            for py in path.glob("*.py"):
                if py.name == "pipelines_design.py":
                    continue
                body = py.read_text(encoding="utf-8")
                for snip in forbidden_snippets:
                    if snip in body:
                        hits.append(f"{py.name}:{snip}")
    assert hits == [], f"CI integration surface leaked into product: {hits}"
