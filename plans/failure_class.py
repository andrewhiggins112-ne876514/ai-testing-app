"""Failure class labels on plan runs (KAN-145)."""

_ALLOWED = frozenset({"product_bug", "test_defect", "environment", "known_issue", ""})


def normalize_failure_class(value: str | None) -> str | None:
    text = (value or "").strip().lower().replace(" ", "_")
    if not text:
        return None
    if text in _ALLOWED:
        return text if text else None
    return "product_bug" if "product" in text else text[:64]