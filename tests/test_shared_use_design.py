"""KAN-245 / KAN-246 — H3 shared use without a cloud design only (FR-SEC-1)."""
from __future__ import annotations

from pathlib import Path

from plans.shared_use_design import (
    REQUIRED_SECTIONS,
    assert_design_complete,
    design_doc_path,
    design_outline,
    missing_doc_headings,
)

ROOT = Path(__file__).resolve().parents[1]


def test_design_outline_covers_catalogue_ac() -> None:
    outline = design_outline()
    assert outline["fr"] == "FR-SEC-1"
    assert outline["story"] == "KAN-245"
    assert outline["network_service_shipped"] is False
    assert outline["cloud_multi_tenant_required"] is False
    for key in REQUIRED_SECTIONS:
        assert key in outline["sections"]
    opts = outline["sections"]["local_on_prem_options"]
    assert opts["future_shared_folder_shipped"] is False
    for name in ("export_pack_f6", "backup_copy_e4", "future_shared_folder"):
        assert name in opts["options"]
    limits = outline["sections"]["security_limits"]
    assert limits["official_secret_isolation"] is True
    assert limits["no_shared_credentials_across_pcs"] is True
    assert limits["no_mandatory_network_service"] is True
    assert limits["refuse_cross_level_mix"] is True
    assert limits["confirm_before_import_or_restore"] is True


def test_design_doc_exists_with_required_headings() -> None:
    path = design_doc_path()
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    assert "FR-SEC-1" in text
    assert "export pack" in text.lower()
    assert "backup" in text.lower()
    assert "shared folder" in text.lower()
    assert (
        "does not pick or ship a network service" in text.lower()
        or "no network / share service ships" in text.lower()
    )
    assert missing_doc_headings(text) == []


def test_assert_design_complete_ok() -> None:
    result = assert_design_complete()
    assert result["status"] == "ok"
    assert result["network_service_shipped"] is False
    assert "export_pack_f6" in result["options"]


def test_no_network_share_service_shipped_in_product() -> None:
    """H3 must not add a live share/sync API or desktop sync control."""
    forbidden_snippets = (
        "/api/share/",
        "/api/plans/share/",
        "/api/shared-folder/",
        "share-folder-sync-btn",
        "plan-share-sync-btn",
        "start_share_watcher(",
        "sync_shared_folder(",
        "lan_discovery_share(",
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
                if snip in body and "shared_use_design" not in path.name:
                    hits.append(f"{path.name}:{snip}")
        elif path.is_dir():
            for py in path.glob("*.py"):
                if py.name == "shared_use_design.py":
                    continue
                body = py.read_text(encoding="utf-8")
                for snip in forbidden_snippets:
                    if snip in body:
                        hits.append(f"{py.name}:{snip}")
    assert hits == [], f"network share surface leaked into product: {hits}"
