"""Local-only regression tests for site authentication, CORS, roles and private docs."""
import base64
import hashlib
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import aiindeksi_bot as app


class SiteAuthTests(unittest.TestCase):
    ORIGIN = "https://raqamlitadqiqot.pages.dev"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rt-auth-test-")
        self.old = {
            "HERE": app.HERE,
            "DB_PATH": app.DB_PATH,
            "SITE_DOCS_DIR": app.SITE_DOCS_DIR,
            "SITE_SESSION_KEY": app.SITE_SESSION_KEY,
        }
        app.HERE = self.tmp.name
        app.DB_PATH = os.path.join(self.tmp.name, "test-db.json")
        app.SITE_DOCS_DIR = os.path.join(self.tmp.name, "private_docs")
        app.SITE_SESSION_KEY = hashlib.sha256(b"unit-test-only-secret-key").digest()
        with app._SITE_AUTH_LOCK:
            app._SITE_AUTH_FAILURES.clear()
        self.db = app._bo_sh_db()
        self.db["site_accounts_initialized"] = True
        self.assertTrue(app._site_create_account(
            self.db, "root-admin", "Admin-test-pass-123", "test", is_admin=True)[0])
        self.assertTrue(app._site_create_account(
            self.db, "member-one", "Member-test-pass-456", "test", is_admin=False)[0])
        self.server = app.make_server(lambda: self.db, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        app.HERE = self.old["HERE"]
        app.DB_PATH = self.old["DB_PATH"]
        app.SITE_DOCS_DIR = self.old["SITE_DOCS_DIR"]
        app.SITE_SESSION_KEY = self.old["SITE_SESSION_KEY"]
        with app._SITE_AUTH_LOCK:
            app._SITE_AUTH_FAILURES.clear()
        self.tmp.cleanup()

    def call(self, path, method="GET", body=None, token=None, origin=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        if origin is not None:
            headers["Origin"] = origin
        request = urllib.request.Request(self.base + path, data=data,
                                         headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read()

    def login(self, login, password):
        status, _, raw = self.call("/api/auth", method="POST",
                                   body={"login": login, "password": password},
                                   origin=self.ORIGIN)
        self.assertEqual(status, 200, raw)
        result = json.loads(raw)
        self.assertTrue(result["ok"])
        return result["token"]

    def test_cors_preflight_is_allowlisted(self):
        status, headers, _ = self.call("/api/auth", method="OPTIONS", origin=self.ORIGIN)
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), self.ORIGIN)
        self.assertIn("Authorization", headers.get("Access-Control-Allow-Headers", ""))
        status, headers, _ = self.call("/api/auth", method="OPTIONS", origin="https://evil.example")
        self.assertEqual(status, 403)
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))

    def test_login_roles_and_no_query_token(self):
        admin = self.login("root-admin", "Admin-test-pass-123")
        member = self.login("member-one", "Member-test-pass-456")
        status, _, raw = self.call("/api/me", token=member)
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(raw)["user"]["is_admin"])
        status, _, _ = self.call("/api/admin/users", token=member)
        self.assertEqual(status, 403)
        status, _, raw = self.call("/api/admin/users", token=admin)
        self.assertEqual(status, 200)
        self.assertNotIn("password_hash", raw.decode("utf-8"))
        status, _, _ = self.call("/api/admin/users?token=" + admin)
        self.assertEqual(status, 401)
        status, _, _ = self.call("/api/admin/users")
        self.assertEqual(status, 401)

    def test_only_telegram_admin_provisions_site_accounts_then_web_admin_can_reset(self):
        admin = self.login("root-admin", "Admin-test-pass-123")
        member = self.login("member-one", "Member-test-pass-456")
        password = "Member-two-pass-789"

        # A web-admin session may not create a workspace account.
        status, _, _ = self.call("/api/admin/add_user", method="POST",
                                 body={"login": "member-two", "password": password}, token=admin)
        self.assertEqual(status, 403)
        self.assertNotIn("member-two", self.db["site_users"])

        # Provisioning is restricted to an authorized Telegram admin's private chat.
        old_admin_ids = app.ADMIN_IDS
        try:
            app.ADMIN_IDS = {77001}
            group_msg = {"chat": {"id": 77001, "type": "group"},
                         "message_id": 1, "text": "/qosh member-two"}
            reply, _ = app._site_account_bot_command(group_msg, self.db, group_msg["text"])
            self.assertIn("Bunday buyruq yo'q", reply)
            self.assertNotIn("member-two", self.db["site_users"])

            non_admin_msg = {"chat": {"id": 77002, "type": "private"},
                             "message_id": 2, "text": "/qosh member-two"}
            reply, _ = app._site_account_bot_command(non_admin_msg, self.db, non_admin_msg["text"])
            self.assertIn("Bunday buyruq yo'q", reply)
            self.assertNotIn("member-two", self.db["site_users"])

            private_msg = {"chat": {"id": 77001, "type": "private"},
                           "message_id": 2, "text": "/qosh member-two"}
            reply, _ = app._site_account_bot_command(private_msg, self.db, private_msg["text"])
            self.assertIn("bir martalik havola", reply)
            token = reply.split("#token=", 1)[1].strip()
            self.assertTrue(app._site_activate(self.db, token, password)[0])
            self.assertNotIn(password, reply)
        finally:
            app.ADMIN_IDS = old_admin_ids

        self.assertTrue(self.db["site_users"]["member-two"]["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertNotIn(password, json.dumps(self.db))
        self.assertTrue(any(event["action"] == "activation_issued"
                            and event["actor"] == "telegram:77001"
                            and event["target"] == "member-two"
                            for event in self.db["site_audit"]))
        status, _, _ = self.call("/api/admin/change_pass", method="POST",
                                 body={"login": "member-one", "new_password": "Member-reset-pass-999"},
                                 token=admin)
        self.assertEqual(status, 200)
        status, _, _ = self.call("/api/me", token=member)
        self.assertEqual(status, 401)
        status, _, raw = self.call("/api/admin/audit", token=admin)
        self.assertEqual(status, 200)
        audit = json.loads(raw)["events"]
        self.assertTrue(any(event["action"] == "password_reset" for event in audit))
        self.assertNotIn(password, raw.decode("utf-8"))
        self.assertTrue(all("password" not in event for event in self.db["site_audit"]))

    def test_club_membership_signup_remains_open_via_telegram_auth(self):
        # Mock Telegram's signed initData validator and all bot sends: this verifies
        # the public membership flow locally without contacting Telegram.
        payload = {
            "initData": "test-only-signed-init-data",
            "ism": "Test Member",
            "fakultet": app.FAKULTETLAR[0],
            "kurs": app.KURSLAR[0],
            "yonalish": "Test yo'nalishi",
            "rozilik": True,
        }
        with patch.object(app, "webapp_auth", return_value={"id": 77002, "username": "test_member"}), \
             patch.object(app, "send") as send_mock, \
             patch.object(app, "ADMIN_IDS", set()):
            status, _, raw = self.call("/register", method="POST", body=payload)
        self.assertEqual(status, 200, raw)
        self.assertTrue(json.loads(raw)["ok"])
        self.assertIn("77002", self.db["users"])
        self.assertNotIn("test_member", self.db["site_users"])
        send_mock.assert_called_once()

    def test_self_password_change_invalidates_session(self):
        member = self.login("member-one", "Member-test-pass-456")
        status, _, raw = self.call("/api/me/change_password", method="POST",
                                   body={"old_password": "Member-test-pass-456",
                                         "new_password": "Member-own-pass-888"}, token=member)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["must_relogin"])
        status, _, _ = self.call("/api/me", token=member)
        self.assertEqual(status, 401)
        self.login("member-one", "Member-own-pass-888")

    def test_documents_are_authenticated_and_path_safe(self):
        admin = self.login("root-admin", "Admin-test-pass-123")
        status, _, _ = self.call("/api/docs")
        self.assertEqual(status, 401)
        os.makedirs(app.SITE_DOCS_DIR, exist_ok=True)
        with open(os.path.join(app.SITE_DOCS_DIR, "sample.txt"), "w", encoding="utf-8") as f:
            f.write("private")
        status, _, raw = self.call("/api/docs", token=admin)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["documents"][0]["name"], "sample.txt")
        status, _, raw = self.call("/api/docs/sample.txt", token=admin)
        self.assertEqual(status, 200)
        self.assertEqual(raw, b"private")
        status, _, _ = self.call("/api/docs/%2e%2e%2fREADME.md", token=admin)
        self.assertEqual(status, 404)

    def test_legacy_import_skips_compromised_default_and_upgrades_hashes(self):
        weak_default = app._LEGACY_DEFAULT_HASH
        legacy_hash = hashlib.sha256(b"Legacy-user-pass-123").hexdigest()
        admin_hash = hashlib.sha256(b"Legacy-admin-pass-456").hexdigest()
        with open(os.path.join(self.tmp.name, "site_creds.json"), "w", encoding="utf-8") as f:
            json.dump([
                {"login": "old-admin", "password_hash": weak_default, "is_admin": True},
                {"login": "legacy-user", "password_hash": legacy_hash, "is_admin": False},
            ], f)
        with open(os.path.join(self.tmp.name, "admin_creds.json"), "w", encoding="utf-8") as f:
            json.dump({"login": "legacy-root", "password_hash": admin_hash}, f)
        legacy_db = app._bo_sh_db()
        app._ensure_site_accounts(legacy_db)
        self.assertNotIn("old-admin", legacy_db["site_users"])
        self.assertIn("legacy-user", legacy_db["site_users"])
        self.assertIn("legacy-root", legacy_db["site_users"])
        ok, needs_rehash = app._site_password_check(
            legacy_db["site_users"]["legacy-user"]["password_hash"], "Legacy-user-pass-123")
        self.assertTrue(ok)
        self.assertTrue(needs_rehash)
        self.assertEqual(legacy_db["site_users"]["legacy-user"]["created_at"], 0)

    def test_failed_login_attempts_are_throttled(self):
        bucket = "127.0.0.1:member-one"
        self.assertTrue(app._site_auth_allowed(bucket)[0])
        for _ in range(app.SITE_AUTH_LIMIT):
            app._site_auth_failed(bucket)
        self.assertFalse(app._site_auth_allowed(bucket)[0])
        app._site_auth_succeeded(bucket)
        self.assertTrue(app._site_auth_allowed(bucket)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
