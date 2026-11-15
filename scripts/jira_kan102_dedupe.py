"""Link Tasks/test to canonical Story KAN-103; mark duplicate KAN-105."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "jira_kan_seed_backlog", REPO / "scripts" / "jira_kan_seed_backlog.py"
)
seed = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(seed)

CANONICAL = "KAN-103"
DUPLICATE = "KAN-105"
TASKS = ["KAN-106", "KAN-107", "KAN-108", "KAN-109", "KAN-110"]
TEST = "KAN-104"


def main() -> int:
    url, auth = seed.load_creds()
    j = seed.Jira(url, auth)
    for tk in TASKS + [TEST]:
        j.link_relates(CANONICAL, tk)
    j.comment(
        DUPLICATE,
        "Duplicate Story from PM sync retry — **do not implement**. Canonical Story: KAN-103. Tasks KAN-106…110 and test KAN-104 Relates to KAN-103.",
    )
    j.comment(
        CANONICAL,
        "Canonical implementation Story for KAN-102 CR. Tasks: KAN-106 (area screens), KAN-107 (HUD widgets), KAN-108 (App vs Orb settings), KAN-109 (orb hub later), KAN-110 (KAN-101). Test: KAN-104.",
    )
    # Try to close duplicate if transition exists
    mapping = j.transitions(DUPLICATE)
    for name in ("Done", "Cancelled", "Cancel"):
        if name in mapping:
            j._req(
                "POST",
                f"/rest/api/3/issue/{DUPLICATE}/transitions",
                json={"transition": {"id": mapping[name]}},
                headers={"Content-Type": "application/json"},
            )
            break
    j.close()
    print("failures", j.failures)
    return 1 if j.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())