"""KAN-91 / FR-JIRA-6 — 429 Retry-After backoff and human-readable auth errors."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import jira_plugin  # noqa: E402
from plugins.jira_plugin import (  # noqa: E402
    _auth_error,
    _rate_limited_error,
    _request,
    _retry_after_seconds,
    read_issue,
)


class _Resp:
    def __init__(self, status_code: int, data=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._data = data if data is not None else {}

    def json(self):
        return self._data


class _SeqClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("unexpected extra GET")
        return self._responses.pop(0)

    async def post(self, *args, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("unexpected extra POST")
        return self._responses.pop(0)

    async def put(self, *args, **kwargs):
        self.calls += 1
        if not self._responses:
            raise AssertionError("unexpected extra PUT")
        return self._responses.pop(0)


class RetryAfterHelperTests(unittest.TestCase):
    def test_retry_after_header(self):
        self.assertEqual(_retry_after_seconds(_Resp(429, headers={"Retry-After": "3"})), 3.0)

    def test_retry_after_default(self):
        self.assertEqual(_retry_after_seconds(_Resp(429)), jira_plugin._DEFAULT_RETRY_AFTER)

    def test_auth_message_human_readable(self):
        err = _auth_error(403)
        self.assertEqual(err["status"], "unauthorized")
        self.assertIn("credential", err["message"].lower())
        self.assertNotIn("token=", err["message"].lower())

    def test_rate_limit_message_human_readable(self):
        err = _rate_limited_error(_Resp(429, headers={"Retry-After": "5"}))
        self.assertEqual(err["status"], "rate_limited")
        self.assertIn("rate limit", err["message"].lower())
        self.assertEqual(err["retry_after"], 5.0)


class RequestBackoffTests(unittest.TestCase):
    def test_retries_on_429_then_succeeds(self):
        client = _SeqClient([
            _Resp(429, headers={"Retry-After": "7"}),
            _Resp(200, {"ok": True}),
        ])
        slept = []

        async def _fake_sleep(seconds: float) -> None:
            slept.append(seconds)

        with patch("plugins.jira_plugin._sleep", side_effect=_fake_sleep):
            response = asyncio.run(_request(client, "GET", "https://example.test/x"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.calls, 2)
        self.assertEqual(slept[0], 7.0)

    def test_exhausted_429_returns_last_response(self):
        responses = [_Resp(429, headers={"Retry-After": "1"})] * jira_plugin._MAX_429_ATTEMPTS
        client = _SeqClient(responses)
        with patch("plugins.jira_plugin._sleep", new_callable=AsyncMock):
            response = asyncio.run(_request(client, "GET", "https://example.test/x"))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(client.calls, jira_plugin._MAX_429_ATTEMPTS)


class ReadIssueRateLimitTests(unittest.TestCase):
    def test_read_issue_retries_then_ok(self):
        payload = {
            "key": "KAN-91",
            "fields": {
                "summary": "Backoff",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Story"},
                "description": None,
            },
        }
        client = _SeqClient([
            _Resp(429, headers={"Retry-After": "2"}),
            _Resp(200, payload),
        ])
        with patch(
            "plugins.jira_plugin._list_creds",
            return_value={
                "url": "https://example.atlassian.net",
                "email": "u@example.com",
                "token": "super-secret-token",
            },
        ), patch(
            "plugins.jira_plugin.httpx.AsyncClient",
            lambda *a, **k: client,
        ), patch("plugins.jira_plugin._sleep", new_callable=AsyncMock):
            result = asyncio.run(read_issue("KAN-91"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["key"], "KAN-91")
        self.assertEqual(client.calls, 2)
        self.assertNotIn("super-secret-token", str(result))

    def test_read_issue_exhausted_429_is_rate_limited(self):
        client = _SeqClient(
            [_Resp(429, headers={"Retry-After": "4"})] * jira_plugin._MAX_429_ATTEMPTS
        )
        with patch(
            "plugins.jira_plugin._list_creds",
            return_value={
                "url": "https://example.atlassian.net",
                "email": "u@example.com",
                "token": "super-secret-token",
            },
        ), patch(
            "plugins.jira_plugin.httpx.AsyncClient",
            lambda *a, **k: client,
        ), patch("plugins.jira_plugin._sleep", new_callable=AsyncMock):
            result = asyncio.run(read_issue("KAN-91"))
        self.assertEqual(result["status"], "rate_limited")
        self.assertIn("rate limit", result["message"].lower())
        self.assertNotIn("super-secret-token", str(result))

    def test_read_issue_401_human_readable(self):
        client = _SeqClient([_Resp(401)])
        with patch(
            "plugins.jira_plugin._list_creds",
            return_value={
                "url": "https://example.atlassian.net",
                "email": "u@example.com",
                "token": "super-secret-token",
            },
        ), patch(
            "plugins.jira_plugin.httpx.AsyncClient",
            lambda *a, **k: client,
        ), patch("plugins.jira_plugin._sleep", new_callable=AsyncMock):
            result = asyncio.run(read_issue("KAN-91"))
        self.assertEqual(result["status"], "unauthorized")
        self.assertIn("credential", result["message"].lower())
        self.assertIn("local settings", result["message"].lower())
        self.assertNotIn("super-secret-token", str(result))


if __name__ == "__main__":
    unittest.main()
