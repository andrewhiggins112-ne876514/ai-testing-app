"""
Central self-heal guardrails (FR-HEAL-1…5).

Locator-only heals may be proposed after classification. Forbidden transforms
(assertion weaken, value change, skip/fixme, timeout inflation, AUT patch)
are always refused. Real product bugs stay red.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _new_proposal_id() -> str:
    return uuid.uuid4().hex[:12]


def _stable_legacy_id(entry: Dict[str, Any], line_index: int) -> str:
    """Deterministic id for audit lines written before KAN-75."""
    raw = "|".join(
        [
            str(entry.get("timestamp") or ""),
            str(entry.get("kind") or ""),
            str(entry.get("classification") or ""),
            str(entry.get("proposal") or entry.get("message") or ""),
            str(line_index),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def record_approved_or_pending(
    proposal: HealProposal,
    decision: PolicyDecision,
    *,
    approver: Optional[str] = "pending_review",
) -> Dict[str, Any]:
    """Append FR-HEAL-5 audit line. Call only after evaluate()."""
    allowed = bool(decision.allowed)
    entry: Dict[str, Any] = {
        "id": _new_proposal_id(),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": proposal.kind,
        "allowed": allowed,
        "reason": decision.reason,
        "classification": decision.classification or proposal.classification,
        "evidence": proposal.evidence
        or {
            "original": proposal.original,
            "proposed": proposal.proposed,
        },
        "approver": approver if allowed else None,
        "review_status": "pending_review" if allowed else "refused",
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


def _read_audit_entries(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    log_path = path or heal_log_path()
    if not log_path.is_file():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for idx, line in enumerate(lines):
        text = (line or "").strip()
        if not text:
            continue
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        entry = dict(raw)
        if not entry.get("id"):
            entry["id"] = _stable_legacy_id(entry, idx)
        status = (entry.get("review_status") or "").strip().lower()
        if not status:
            if entry.get("allowed") and entry.get("approver") == "pending_review":
                status = "pending_review"
            elif entry.get("allowed") and entry.get("approver"):
                status = "approved"
            elif entry.get("allowed") is False:
                status = "refused"
            else:
                status = "unknown"
            entry["review_status"] = status
        entries.append(entry)
    return entries


def _write_audit_entries(entries: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    log_path = path or heal_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(e, ensure_ascii=True) + "\n" for e in entries)
    fd, tmp_name = tempfile.mkstemp(
        prefix="heal_audit_", suffix=".jsonl", dir=str(log_path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        Path(tmp_name).replace(log_path)
    except Exception:
        try:
            Path(tmp_name).unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _public_proposal(entry: Dict[str, Any]) -> Dict[str, Any]:
    evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}
    return {
        "id": entry.get("id"),
        "timestamp": entry.get("timestamp"),
        "kind": entry.get("kind"),
        "classification": entry.get("classification"),
        "proposal": entry.get("proposal") or entry.get("message") or "",
        "message": entry.get("message") or "",
        "approver": entry.get("approver"),
        "review_status": entry.get("review_status"),
        "evidence": {
            "original": evidence.get("original"),
            "proposed": evidence.get("proposed") or evidence.get("used"),
            "action": evidence.get("action"),
            "value_unchanged": evidence.get("value_unchanged"),
        },
    }


def list_pending_heals(*, path: Optional[Path] = None) -> Dict[str, Any]:
    """Pending locator heals awaiting human approve/reject (FR-HEAL-2)."""
    pending = [
        _public_proposal(e)
        for e in _read_audit_entries(path)
        if e.get("allowed") and (e.get("review_status") or "") == "pending_review"
    ]
    return {"pending": pending, "count": len(pending)}


def resolve_heal(
    proposal_id: str,
    *,
    action: str,
    reviewer: str = "local_user",
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Approve or reject a pending heal (FR-HEAL-2 / FR-HEAL-5).

    Approve records a human approver; reject marks not accepted (suite not updated).
    No auto-commit of healed tests.
    """
    pid = (proposal_id or "").strip()
    if not pid:
        return {"ok": False, "error": "proposal_id is required"}

    decision = (action or "").strip().lower()
    if decision not in {"approve", "reject"}:
        return {"ok": False, "error": "action must be approve or reject"}

    name = (reviewer or "").strip() or "local_user"
    entries = _read_audit_entries(path)
    target: Optional[Dict[str, Any]] = None
    for entry in entries:
        if entry.get("id") == pid:
            target = entry
            break
    if target is None:
        return {"ok": False, "error": "proposal not found", "id": pid}

    status = (target.get("review_status") or "").strip().lower()
    if not target.get("allowed") or status != "pending_review":
        return {
            "ok": False,
            "error": "proposal is not pending review",
            "id": pid,
            "review_status": status or target.get("review_status"),
        }

    reviewed_at = datetime.now().isoformat(timespec="seconds")
    if decision == "approve":
        target["review_status"] = "approved"
        target["approver"] = name
        target["reviewed_at"] = reviewed_at
        target["message"] = (
            f"Locator heal approved by {name} (FR-HEAL-2/5). "
            "Suite file not auto-committed."
        )
    else:
        target["review_status"] = "rejected"
        target["approver"] = None
        target["rejected_by"] = name
        target["reviewed_at"] = reviewed_at
        target["message"] = (
            f"Locator heal rejected by {name}; not treated as accepted (FR-HEAL-2)."
        )

    try:
        _write_audit_entries(entries, path)
    except OSError as exc:
        return {"ok": False, "error": f"could not write audit log: {exc}", "id": pid}

    return {
        "ok": True,
        "id": pid,
        "review_status": target["review_status"],
        "approver": target.get("approver"),
        "rejected_by": target.get("rejected_by"),
        "proposal": _public_proposal(target),
    }


def approve_heal(
    proposal_id: str, *, reviewer: str = "local_user", path: Optional[Path] = None
) -> Dict[str, Any]:
    return resolve_heal(proposal_id, action="approve", reviewer=reviewer, path=path)


def reject_heal(
    proposal_id: str, *, reviewer: str = "local_user", path: Optional[Path] = None
) -> Dict[str, Any]:
    return resolve_heal(proposal_id, action="reject", reviewer=reviewer, path=path)
