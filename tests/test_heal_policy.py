"""Unit tests for FR-HEAL central policy (KAN-49). No browser required."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins.heal_policy import HealProposal, evaluate, locator_diff  # noqa: E402


class HealPolicyTests(unittest.TestCase):
    def test_refuse_tohavetext_to_tobevisible(self):
        decision = evaluate(
            HealProposal(
                kind="assertion",
                original="expect(page.locator('h1')).toHaveText('Welcome')",
                proposed="expect(page.locator('h1')).toBeVisible()",
                classification="test_defect",
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "assertion_weaken")
        self.assertIn("toBeVisible", decision.message)

    def test_unclassified_heal_mandatory(self):
        decision = evaluate(
            HealProposal(
                kind="locator",
                original="#email",
                proposed="Email address",
                classification=None,
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "missing_classification")

    def test_product_bug_stays_red(self):
        decision = evaluate(
            HealProposal(
                kind="locator",
                original="#submit",
                proposed="Submit",
                classification="product_bug",
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "product_bug_stays_red")

    def test_timeout_inflation_refused(self):
        decision = evaluate(
            HealProposal(
                kind="timeout",
                original="10000",
                proposed="60000",
                classification="test_defect",
                original_timeout_ms=10000,
                proposed_timeout_ms=60000,
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "timeout_inflation")

    def test_skip_fixme_refused(self):
        decision = evaluate(
            HealProposal(
                kind="skip",
                original="test('login')",
                proposed="test.fixme('login')",
                classification="test_defect",
            )
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "skip_or_fixme")

    def test_locator_only_allowed_pending_review(self):
        decision = evaluate(
            HealProposal(
                kind="locator",
                original="email",
                proposed="Email address",
                classification="test_defect",
            )
        )
        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.reason)
        self.assertIn("locator only", decision.proposal_diff or "")

    def test_locator_diff_value_unchanged(self):
        text = locator_diff("Email", "Email address", value="keep-me")
        self.assertIn("locator only", text)
        self.assertIn("value unchanged: 'keep-me'", text)
        self.assertIn("auto-committed", text)


if __name__ == "__main__":
    unittest.main()
