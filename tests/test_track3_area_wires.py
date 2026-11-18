"""KAN-309 — marker checks for Track 3 Primary wires pack (KAN-308)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIRES = ROOT / "docs" / "design" / "TRACK3_AREA_WIRES.md"
NOTE = ROOT / "docs" / "design" / "ENTERPRISE_LAYOUT_NOTE.md"


def test_track3_area_wires_exists() -> None:
    assert WIRES.is_file(), f"missing wires pack: {WIRES}"


def test_track3_primary_areas_have_wires() -> None:
    text = WIRES.read_text(encoding="utf-8")
    lower = text.lower()

    assert "plans" in lower and "cases" in lower
    assert "manual" in lower and "confirm" in lower
    assert "reports" in lower
    assert "documents" in lower
    assert "settings" in lower
    assert "security" in lower


def test_track3_chrome_budget_documented() -> None:
    text = WIRES.read_text(encoding="utf-8")
    lower = text.lower()

    assert "120px" in lower or "~120" in lower
    assert "area-work" in lower
    assert "no second filter" in lower or "no** second filter" in lower or "second filter strip" in lower


def test_track3_ae_verify_contract() -> None:
    text = WIRES.read_text(encoding="utf-8")
    lower = text.lower()

    for mode in ("overlay", "stage", "orb_hub", "split", "floating"):
        assert mode in lower, f"missing layout mode {mode}"


def test_track3_lab_is_follow_on() -> None:
    text = WIRES.read_text(encoding="utf-8")
    lower = text.lower()

    assert "follow-on" in lower or "follow on" in lower
    assert "heal" in lower
    assert "suites" in lower
    assert "sandboxes" in lower
    assert "track3-lab" in lower or "lab epic" in lower or "lab density" in lower


def test_track3_accept_gate_blocks_geometry() -> None:
    text = WIRES.read_text(encoding="utf-8")
    lower = text.lower()

    assert "accept track 3 wires" in lower
    assert "accepted" in lower
    assert "no html/css" in lower or "html/css geometry" in lower
    assert "kan-310" in lower


def test_track3_points_at_enterprise_note() -> None:
    text = WIRES.read_text(encoding="utf-8")
    assert "ENTERPRISE_LAYOUT_NOTE.md" in text
    assert NOTE.is_file()
