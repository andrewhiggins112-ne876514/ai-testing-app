"""
Central self-heal guardrails (FR-HEAL-1…5).

Locator-only heals may be proposed after classification. Forbidden transforms
(assertion weaken, value change, skip/fixme, timeout inflation, AUT patch)
are always refused. Real product bugs stay red.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

CLASSIFICATIONS = frozenset(
    {"product_bug", "test_defect", "intended_change", "environment"}
)

# Stronger assertion / expect forms that must not be weakened.
_STRONG_ASSERT = re.compile(
    r"(tohavetext|tohavevalue|tohaveurl|toequal|tobe|"
    r"expect_text|expect_url|expect_value|"
    r"assertequal|assert_equal|asserttext|assert_text)",
    re.I,
)
_WEAK_ASSERT = re.compile(
    r"(tobevisible|tobeattached|tobeenabled|toexist|"
    r"expect_visible|expect_exists|isvisible|is_visible)",
    re.I,
)
_SKIP_FIXME = re.compile(
    r"\b(test\.fixme|test\.skip|xit|xdescribe|pytest\.mark\.skip|"
    r"@unittest\.skip|pending\()\b",
    re.I,
)
_AUT_PATCH = re.compile(
    r"\b(patch_aut|modify_app|edit_source|change_application|"
    r"fix_production|hotfix_aut)\b",
    re.I,
)


@dataclass
class HealProposal:
    """A proposed heal for policy evaluation."""

    kind: str  # locator | assertion | timeout | skip | value | aut_patch | other
    original: str = ""
    proposed: str = ""
    classification: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    original_timeout_ms: Optional[int] = None
    proposed_timeout_ms: Optional[int] = None
    original_retries: Optional[int] = None
    proposed_retries: Optional[int] = None
    value_changed: bool = False
    value_unchanged: Optional[str] = None
    approver: Optional[str] = None


@dataclass
class PolicyDecision:
    allowed: bool
    reason: Optional[str] = None
    message: str = ""
    classification: Optional[str] = None
    proposal_diff: Optional[str] = None


def heal_log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) / "ai_testing_app" if base else Path.home() / ".ai_testing_app"
    return root / "heal_audit.jsonl"


def append_heal_log(entry: Dict[str, Any]) -> None:
    path = heal_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def locator_diff(original: str, proposed: str, value: Optional[str] = None) -> str:
    """Human-readable locator-only proposal (FR-HEAL-1 / FR-HEAL-2)."""
    lines = [
        "Heal proposal: locator only (FR-HEAL-1).",
        f"- original locator intent: {original}",
        f"- proposed locator: {proposed}",
    ]
    if value is not None:
        lines.append(f"- value unchanged: {value!r}")
    lines.append("- suite file not auto-committed (FR-HEAL-2).")
    return "\n".join(lines)


def _refuse(reason: str, message: str, classification: Optional[str] = None) -> PolicyDecision:
    return PolicyDecision(
        allowed=False,
        reason=reason,
        message=message,
        classification=classification,
    )


def _is_assertion_weaken(original: str, proposed: str) -> bool:
    """True when a strong assertion is replaced by a weaker visibility/existence check."""
    o, p = (original or "").strip(), (proposed or "").strip()
    if not o or not p:
        return False
    if _STRONG_ASSERT.search(o) and _WEAK_ASSERT.search(p):
        return True
    if o.lower() in {"expect_text", "expect_url", "tohavetext", "tohaveurl"} and _WEAK_ASSERT.search(p):
        return True
    return False


def evaluate(proposal: HealProposal) -> PolicyDecision:
    """
    Apply FR-HEAL guardrails. Classification is mandatory before any heal is allowed.
    Product bugs are never healed green.
    """
    kind = (proposal.kind or "other").lower().strip()
    classification = (proposal.classification or "").strip().lower() or None

    # FR-HEAL-4: classification mandatory before heal is proposed.
    if not classification:
        return _refuse(
            "missing_classification",
            "Classification is mandatory before any heal is proposed (FR-HEAL-4).",
        )
    if classification not in CLASSIFICATIONS:
        return _refuse(
            "invalid_classification",
            f"Unknown classification {classification!r}; "
            f"expected one of {sorted(CLASSIFICATIONS)}.",
        )

    # Real product bugs stay red — never auto-heal to green.
    if classification == "product_bug":
        return _refuse(
            "product_bug_stays_red",
            "Product bugs stay red; heal refused (FR-HEAL-4).",
            classification=classification,
        )

    # FR-HEAL-3 forbidden transforms (check before kind gate so ACs are explicit).
    if kind == "assertion" or _is_assertion_weaken(proposal.original, proposal.proposed):
        return _refuse(
            "assertion_weaken",
            "Refused: cannot weaken or change assertions "
            "(e.g. toHaveText → toBeVisible) (FR-HEAL-3).",
            classification=classification,
        )

    if kind == "value" or proposal.value_changed:
        return _refuse(
            "alter_expected_value",
            "Refused: expected values must not change without human approval (FR-HEAL-1/3).",
            classification=classification,
        )

    if kind == "skip" or _SKIP_FIXME.search(proposal.proposed or ""):
        return _refuse(
            "skip_or_fixme",
            "Refused: cannot skip or test.fixme() solely to make the suite green (FR-HEAL-3).",
            classification=classification,
        )

    if kind == "timeout":
        return _refuse(
            "timeout_inflation",
            "Refused: cannot raise timeouts or add retries solely to hide flakiness (FR-HEAL-3).",
            classification=classification,
        )

    if kind == "aut_patch" or _AUT_PATCH.search(proposal.proposed or ""):
        return _refuse(
            "aut_patch",
            "Refused: cannot patch the application under test; heal the test only (FR-HEAL-3).",
            classification=classification,
        )

    if kind != "locator":
        return _refuse(
            "unsupported_heal_kind",
            f"Refused: heal kind {kind!r} is not a locator-only change (FR-HEAL-1).",
            classification=classification,
        )

    # Allowed locator-only heal — still requires human approval (FR-HEAL-2).
    diff = locator_diff(
        proposal.original,
        proposal.proposed,
        value=proposal.value_unchanged,
    )
    return PolicyDecision(
        allowed=True,
        reason=None,
        message="Locator-only heal allowed pending human review (FR-HEAL-2).",
        classification=classification,
        proposal_diff=diff,
    )


def record_approved_or_pending(
    proposal: HealProposal,
    decision: PolicyDecision,
    *,
    approver: Optional[str] = "pending_review",
) -> Dict[str, Any]:
    """Append FR-HEAL-5 audit line. Call only after evaluate()."""
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": proposal.kind,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "classification": decision.classification or proposal.classification,
        "evidence": proposal.evidence
        or {
            "original": proposal.original,
            "proposed": proposal.proposed,
        },
        "approver": approver if decision.allowed else None,
        "proposal": decision.proposal_diff or decision.message,
        "message": decision.message,
    }
    try:
        append_heal_log(entry)
    except Exception:
        pass
    return entry


def evaluate_and_log(
    proposal: HealProposal, *, approver: Optional[str] = "pending_review"
) -> PolicyDecision:
    decision = evaluate(proposal)
    record_approved_or_pending(
        proposal, decision, approver=approver if decision.allowed else None
    )
    return decision
