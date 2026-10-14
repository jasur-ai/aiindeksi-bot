import contextlib
import io
import json
import unittest
from unittest import mock
from urllib.error import HTTPError

from tools import check_bot_admin_groups as audit


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def open(self, request, timeout=15):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class BotAdminAuditTests(unittest.TestCase):
    def test_parse_chat_ids_deduplicates_and_preserves_negative_ids(self):
        self.assertEqual(
            audit.parse_chat_ids("-1001234567890, @public_group -1001234567890"),
            ["-1001234567890", "@public_group"],
        )

    def test_parse_chat_ids_rejects_bad_values(self):
        for raw in ("", "not-a-chat", "-12;not-valid"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.parse_chat_ids(raw)

    def test_read_only_method_allowlist_blocks_message_sending(self):
        with mock.patch.object(audit.urllib.request, "build_opener") as build_opener:
            result, error = audit._api_call("not-a-real-token", "sendMessage", {})
        self.assertIsNone(result)
        self.assertEqual(error, "method_not_allowed")
        build_opener.assert_not_called()

    def test_api_http_errors_are_sanitized(self):
        token = "REDACTED"
        error = HTTPError(
            url=f"{audit.API_ROOT}/bot{token}/getMe",
            code=401,
            msg=f"bad token {token}",
            hdrs=None,
            fp=io.BytesIO(token.encode("utf-8")),
        )
        opener = FakeOpener(error=error)
        with mock.patch.object(audit.urllib.request, "build_opener", return_value=opener):
            result, status = audit._api_call(token, "getMe")
        self.assertIsNone(result)
        self.assertEqual(status, "auth_error")
        self.assertNotIn(token, status)

    def test_member_status_requires_matching_bot_id(self):
        self.assertEqual(audit._member_status(
            {"status": "administrator", "user": {"id": 11}}, 11), "admin")
        self.assertEqual(audit._member_status(
            {"status": "member", "user": {"id": 11}}, 11), "not_admin")
        self.assertEqual(audit._member_status(
            {"status": "administrator", "user": {"id": 12}}, 11), "unknown")

    def test_api_call_accepts_only_read_method_and_parses_response(self):
        opener = FakeOpener(response=FakeResponse({"ok": True, "result": {"id": 7}}))
        with mock.patch.object(audit.urllib.request, "build_opener", return_value=opener):
            result, error = audit._api_call("test-token", "getMe")
        self.assertIsNone(error)
        self.assertEqual(result, {"id": 7})
        self.assertEqual(len(opener.calls), 1)

    def test_main_without_token_does_not_print_secret(self):
        output = io.StringIO()
        with mock.patch.dict("os.environ", {"AIINDEKSI_TOKEN": "", "AIINDEKSI_AUDIT_CHAT_IDS": ""}, clear=True):
            with contextlib.redirect_stdout(output):
                code = audit.main()
        self.assertEqual(code, 2)
        self.assertIn("secure environment", output.getvalue())
        self.assertNotIn("token value", output.getvalue())


if __name__ == "__main__":
    unittest.main()
