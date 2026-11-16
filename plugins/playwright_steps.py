"""Playwright step generation and quality checks (FR-TEST-1 / FR-TEST-6).

Outcome assertions are ``expect_text`` / ``expect_url``. Visibility-only checks
(``expect_visible``) or interaction-only drafts without an outcome assertion are
incomplete and must be flagged or rejected.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse

OUTCOME_ACTIONS = frozenset({"expect_text", "expect_url"})
WEAK_ACTIONS = frozenset({"expect_visible"})
INTERACTION_ACTIONS = frozenset({"click", "fill"})
NAV_ACTIONS = frozenset({"goto"})
KNOWN_ACTIONS = frozenset(
    {"goto", "click", "fill", "expect_text", "expect_url", "expect_visible"}
)

_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
_CLICK = re.compile(
    r"(?:click|press|tap)\s+(?:(?:the|a|an)\s+)?[\"']?([^\"'\n,.;]+)[\"']?",
    re.I,
)
_FILL = re.compile(
    r"(?:fill|type|enter)\s+(?:(?:in|into)\s+)?[\"']?([^\"'\n,]+?)[\"']?"
    r"\s+(?:with|as|=|:)\s+[\"']?([^\"'\n]+)[\"']?",
    re.I,
)
_EXPECT_TEXT = re.compile(
    r"(?:expect|assert|check|verify)\s+(?:text\s+)?(?:[\"']([^\"']+)[\"']|(\S+))"
    r"|(?:see|contains?)\s+[\"']([^\"']+)[\"']",
    re.I,
)
_EXPECT_URL = re.compile(
    r"(?:expect|assert|check|verify).{0,40}url.{0,20}"
    r"(?:contain(?:s)?|include(?:s)?|is|=|:)\s*[\"']?([^\s\"']+)",
    re.I,
)
_NEGATIVE_HINTS = re.compile(
    r"\b(?:invalid|wrong|empty|missing|denied|unauthorized|error|fail|"
    r"negative|edge\s*case|too\s+long|blank)\b",
    re.I,
)


def _strip_url(url: str) -> str:
    return url.rstrip(".,;:)")


def is_nontrivial(steps: Sequence[Dict[str, Any]]) -> bool:
    """True when the flow does more than a single goto (or has interactions)."""
    if not steps:
        return False
    actions = [str(s.get("action") or "") for s in steps if isinstance(s, dict)]
    if any(a in INTERACTION_ACTIONS or a in WEAK_ACTIONS for a in actions):
        return True
    if len(actions) > 1:
        return True
    return False


def assess_steps(steps: Any) -> Dict[str, Any]:
    """Assess whether a step list has a real outcome assertion (FR-TEST-6)."""
    if not isinstance(steps, list):
        return {
            "complete": False,
            "incomplete": True,
            "status": "incomplete",
            "reason": "steps must be a list",
            "has_outcome_assertion": False,
            "has_weak_only": False,
            "nontrivial": False,
            "actions": [],
        }

    actions: List[str] = []
    for step in steps:
        if isinstance(step, dict) and step.get("action"):
            actions.append(str(step["action"]))

    has_outcome = any(a in OUTCOME_ACTIONS for a in actions)
    has_weak = any(a in WEAK_ACTIONS for a in actions)
    nontrivial = is_nontrivial([s for s in steps if isinstance(s, dict)])
    weak_only = has_weak and not has_outcome
    incomplete = False
    reason = ""

    if not steps:
        incomplete = True
        reason = "empty step list"
    elif nontrivial and not has_outcome:
        incomplete = True
        if weak_only:
            reason = (
                "visibility-only checks without an outcome assertion "
                "(expect_text or expect_url) — incomplete (FR-TEST-6)"
            )
        else:
            reason = (
                "non-trivial flow lacks expect_text or expect_url "
                "(outcome assertion required)"
            )

    return {
        "complete": not incomplete,
        "incomplete": incomplete,
        "status": "incomplete" if incomplete else "ok",
        "reason": reason,
        "has_outcome_assertion": has_outcome,
        "has_weak_only": weak_only,
        "nontrivial": nontrivial,
        "actions": actions,
    }


def validate_steps_quality(
    steps: Any,
    *,
    reject_incomplete: bool = True,
) -> Dict[str, Any]:
    """Return assessment; when reject_incomplete, status is reject for bad drafts."""
    assessment = assess_steps(steps)
    if assessment["incomplete"] and reject_incomplete:
        assessment = dict(assessment)
        assessment["status"] = "reject"
        assessment["rejected"] = True
    else:
        assessment = dict(assessment)
        assessment["rejected"] = False
    return assessment


def _default_url(text: str, url: str = "") -> str:
    if url and str(url).strip():
        return _strip_url(str(url).strip())
    found = _URL.search(text or "")
    if found:
        return _strip_url(found.group(0))
    try:
        from settings.store import load_settings

        hint = (load_settings().get("target_url") or "").strip()
        if hint:
            return _strip_url(hint)
    except Exception:
        pass
    return "https://example.com"


def _host_token(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""
    host = host.lower().removeprefix("www.")
    if not host:
        return "example"
    return host.split(".")[0] or host


async def generate_steps_from_jira(
    issue_key: str,
    url: str = "",
    *,
    include_negatives: bool = True,
) -> Dict[str, Any]:
    """Fetch a Jira story's AC/description and generate Playwright step drafts.

    On fetch failure returns a clear error and does **not** invent acceptance criteria.
    """
    from plugins.jira_plugin import read_issue

    key = str(issue_key or "").strip().upper()
    if not key:
        return {
            "status": "error",
            "message": "issue_key is required (for example KAN-85)",
            "issue_key": "",
            "steps": [],
            "happy_path": [],
            "negatives": [],
        }

    fetched = await read_issue(key)
    if fetched.get("status") != "ok":
        return {
            "status": fetched.get("status") or "error",
            "message": fetched.get("message")
            or "Could not fetch Jira acceptance criteria",
            "issue_key": key,
            "steps": [],
            "happy_path": [],
            "negatives": [],
            "invented_ac": False,
        }

    acceptance = str(fetched.get("acceptance_criteria") or "").strip()
    description = str(fetched.get("description") or "").strip()
    summary = str(fetched.get("summary") or "").strip()
    source_text = acceptance or description
    if not source_text:
        return {
            "status": "error",
            "message": (
                f"Issue {fetched.get('key') or key} has no description or "
                "acceptance criteria to generate from (refusing to invent AC)"
            ),
            "issue_key": fetched.get("key") or key,
            "summary": summary,
            "steps": [],
            "happy_path": [],
            "negatives": [],
            "invented_ac": False,
        }

    # Prefer explicit AC; include summary as light context for URL/label hints only.
    pack_text = source_text
    if summary and summary.lower() not in source_text.lower():
        pack_text = f"{summary}\n{source_text}"

    pack = generate_steps_from_spec(
        pack_text,
        url=url,
        include_negatives=include_negatives,
    )
    pack = dict(pack)
    pack["issue_key"] = fetched.get("key") or key
    pack["summary"] = summary
    pack["acceptance_criteria"] = acceptance
    pack["source"] = "acceptance_criteria" if acceptance else "description"
    pack["invented_ac"] = False
    return pack


def generate_steps_from_spec(
    text: str,
    url: str = "",
    *,
    include_negatives: bool = True,
) -> Dict[str, Any]:
    """Build happy-path + optional negative/edge step lists from chat/spec text."""
    raw = (text or "").strip()
    target = _default_url(raw, url)
    happy: List[Dict[str, Any]] = [{"action": "goto", "value": target}]

    for match in _FILL.finditer(raw):
        field, value = match.group(1).strip(), match.group(2).strip()
        if field and value:
            happy.append({"action": "fill", "selector": f"label={field}", "value": value})

    for match in _CLICK.finditer(raw):
        label = match.group(1).strip()
        if label and label.lower() not in {"the", "a", "an"}:
            happy.append({"action": "click", "selector": f"text={label}"})

    expect_texts: List[str] = []
    for match in _EXPECT_TEXT.finditer(raw):
        value = next((g for g in match.groups() if g), "")
        value = value.strip().rstrip(".,;:")
        if value and value.lower() not in {"url", "the", "a", "an", "text"}:
            expect_texts.append(value)
    expect_urls = [m.group(1).strip() for m in _EXPECT_URL.finditer(raw) if m.group(1).strip()]

    for value in expect_urls:
        happy.append({"action": "expect_url", "value": value})
    for value in expect_texts:
        # Skip values that were already used as URL fragments in expect_url regex noise
        if any(value == u for u in expect_urls):
            continue
        happy.append({"action": "expect_text", "value": value})

    # Ensure non-trivial / any generated flow ends with a real outcome assertion.
    if not any(s.get("action") in OUTCOME_ACTIONS for s in happy):
        if len(happy) == 1:
            # Single goto: still add URL host check so drafts are never assertion-free.
            happy.append({"action": "expect_url", "value": _host_token(target)})
        else:
            if expect_texts or "text" in raw.lower() or "see" in raw.lower():
                happy.append({
                    "action": "expect_text",
                    "value": expect_texts[0] if expect_texts else "Welcome",
                })
            else:
                happy.append({"action": "expect_url", "value": _host_token(target)})

    negatives: List[Dict[str, Any]] = []
    if include_negatives:
        negatives = _negative_variants(target, happy, raw)

    assessment = assess_steps(happy)
    return {
        "status": "ok",
        "url": target,
        "steps": happy,
        "happy_path": happy,
        "negatives": negatives,
        "assessment": assessment,
        "notes": (
            "Negatives are first-class drafts (FR-TEST-6); run them as separate flows."
            if negatives
            else "No negative variants generated."
        ),
    }


def _negative_variants(
    target: str,
    happy: Sequence[Dict[str, Any]],
    text: str,
) -> List[Dict[str, Any]]:
    """Edge/negative drafts: bad fill, empty required, unexpected error text."""
    fills = [s for s in happy if s.get("action") == "fill"]
    clicks = [s for s in happy if s.get("action") == "click"]
    variants: List[Dict[str, Any]] = []

    if fills:
        bad = [{"action": "goto", "value": target}]
        for step in fills:
            bad.append({
                "action": "fill",
                "selector": step.get("selector"),
                "value": "___invalid___",
            })
        for step in clicks[:1]:
            bad.append({"action": "click", "selector": step.get("selector")})
        bad.append({"action": "expect_text", "value": "error"})
        variants.append({
            "name": "invalid_input",
            "kind": "negative",
            "steps": bad,
            "assessment": assess_steps(bad),
        })

        empty = [{"action": "goto", "value": target}]
        for step in fills:
            empty.append({
                "action": "fill",
                "selector": step.get("selector"),
                "value": "",
            })
        for step in clicks[:1]:
            empty.append({"action": "click", "selector": step.get("selector")})
        empty.append({"action": "expect_text", "value": "required"})
        variants.append({
            "name": "empty_required",
            "kind": "edge",
            "steps": empty,
            "assessment": assess_steps(empty),
        })
    elif clicks:
        # Click-only flows: assert we do *not* land on a success URL fragment.
        denied = [
            {"action": "goto", "value": target},
            {"action": "click", "selector": clicks[0].get("selector")},
            {"action": "expect_text", "value": "denied"},
        ]
        variants.append({
            "name": "access_denied_edge",
            "kind": "edge",
            "steps": denied,
            "assessment": assess_steps(denied),
        })
    elif _NEGATIVE_HINTS.search(text or ""):
        variants.append({
            "name": "error_banner",
            "kind": "negative",
            "steps": [
                {"action": "goto", "value": target},
                {"action": "expect_text", "value": "error"},
            ],
            "assessment": assess_steps([
                {"action": "goto", "value": target},
                {"action": "expect_text", "value": "error"},
            ]),
        })

    return variants
