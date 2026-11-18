"""KAN-296 — marker checks for enterprise layout research note (KAN-295)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs" / "design" / "ENTERPRISE_LAYOUT_NOTE.md"


def test_enterprise_layout_note_exists() -> None:
    assert NOTE.is_file(), f"missing research note: {NOTE}"


def test_enterprise_layout_note_covers_required_sections() -> None:
    text = NOTE.read_text(encoding="utf-8")
    lower = text.lower()

    assert "type scale" in lower
    assert "spacing" in lower
    assert "header" in lower or "chrome max" in lower
    assert "occlusion checklist" in lower
    assert "plans wire" in lower or "plans · cases" in lower


def test_enterprise_layout_note_forbids_product_anti_patterns() -> None:
    text = NOTE.read_text(encoding="utf-8")
    lower = text.lower()

    assert "tall" in lower and "rail" in lower
    assert "top tab bar" in lower
    assert "purple" in lower
    assert "cdn" in lower or "webfont" in lower or "cloud font" in lower


def test_enterprise_layout_note_blocks_tokens_until_accept() -> None:
    text = NOTE.read_text(encoding="utf-8")
    lower = text.lower()

    assert "kan-297" in lower
    assert "awaiting human accept" in lower or "human accept" in lower
    assert "docs only" in lower or "not a component library" in lower
