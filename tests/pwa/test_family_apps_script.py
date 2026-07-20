import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "apps_script" / "family_api"


class FamilyAppsScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = (API_DIR / "Code.gs").read_text(encoding="utf-8")
        cls.bridge = (API_DIR / "Bridge.html").read_text(encoding="utf-8")
        cls.manifest = json.loads((API_DIR / "appsscript.json").read_text(encoding="utf-8"))
        cls.readme = (API_DIR / "README.md").read_text(encoding="utf-8")

    def test_contains_no_spreadsheet_url_or_local_secret_file(self):
        combined = self.code + self.bridge + self.readme
        self.assertNotIn("docs.google.com/spreadsheets/d/", combined)
        self.assertNotIn("BEGIN PRIVATE KEY", combined)
        self.assertFalse((API_DIR / ".env").exists())

    def test_reads_configuration_from_script_properties(self):
        self.assertIn("PropertiesService.getScriptProperties()", self.code)
        self.assertIn('spreadsheetId: "SPREADSHEET_ID"', self.code)
        self.assertIn('serviceAccountJson: "SERVICE_ACCOUNT_JSON"', self.code)
        self.assertIn('deviceTokenHashes: "DEVICE_TOKEN_HASHES_JSON"', self.code)

    def test_service_account_private_key_stays_server_side(self):
        self.assertIn("function getServiceAccountAccessToken_()", self.code)
        self.assertIn("serviceAccount.private_key", self.code)
        self.assertNotIn("SERVICE_ACCOUNT_JSON", self.bridge)
        self.assertNotIn("private_key", self.bridge)

    def test_member_identity_comes_from_device_token(self):
        self.assertIn("const member = authenticateDevice_(request?.deviceToken)", self.code)
        self.assertIn("probeWrite_(request, apiVersion, member)", self.code)
        self.assertNotIn("request.member", self.code)

    def test_rejects_wrong_key_before_action_dispatch(self):
        rejection = self.code.index('error: "UNAUTHORIZED"')
        dispatch = self.code.index("switch (request.action)")
        self.assertLess(rejection, dispatch)

    def test_supports_ping_read_and_idempotent_write_probe(self):
        self.assertIn('case "ping"', self.code)
        self.assertIn('case "probeWrite"', self.code)
        self.assertIn('case "probeRead"', self.code)
        self.assertIn('=== requestId', self.code)

    def test_serializes_probe_writes_with_script_lock(self):
        self.assertIn("LockService.getScriptLock()", self.code)
        self.assertIn("lock.tryLock(5000)", self.code)
        self.assertIn("lock.releaseLock()", self.code)

    def test_probe_sheet_is_separate_from_family_tasks(self):
        self.assertIn('PROBE_SHEET_NAME = "Tekniskt test"', self.code)
        self.assertIn("setupProbeSheet", self.code)

    def test_direct_post_returns_json_without_putting_key_in_url(self):
        self.assertIn("function doPost(event)", self.code)
        self.assertIn("ContentService.MimeType.JSON", self.code)
        self.assertNotIn("deviceToken=", self.code + self.bridge)

    def test_bridge_restricts_parent_origin_and_targets_reply_origin(self):
        self.assertIn("allowedOrigins.has(event.origin)", self.bridge)
        self.assertIn("event.source?.postMessage", self.bridge)
        self.assertIn("}, event.origin);", self.bridge)
        self.assertIn("window.top.postMessage", self.bridge)

    def test_manifest_runs_as_owner_and_allows_anonymous_web_app_calls(self):
        self.assertEqual(self.manifest["webapp"]["executeAs"], "USER_DEPLOYING")
        self.assertEqual(self.manifest["webapp"]["access"], "ANYONE_ANONYMOUS")
        self.assertEqual(self.manifest["timeZone"], "Europe/Stockholm")
        self.assertEqual(
            self.manifest["oauthScopes"],
            ["https://www.googleapis.com/auth/script.external_request"],
        )
        self.assertNotIn(
            "https://www.googleapis.com/auth/spreadsheets",
            self.manifest["oauthScopes"],
        )
        self.assertIn("endast familjearket", self.readme)


if __name__ == "__main__":
    unittest.main()
