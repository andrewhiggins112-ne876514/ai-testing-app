"""
Re-apply readable ADF layout to enriched KAN issues (same content source as enrich).

Reads credentials from %%LOCALAPPDATA%%/ai_testing_app/settings.json — never logs the token.

This is a thin entry point so formatting tweaks stay in jira_kan_enrich.py (body_to_adf, test_body).

Usage:
  python scripts/jira_kan_reformat.py
  python scripts/jira_kan_reformat.py --dry-run
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_kan_enrich import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())