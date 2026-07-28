import json
from pathlib import Path
import re
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
        self.assertIn("probeWrite_(request, member)", self.code)
        self.assertNotIn("request.member", self.code)

    def test_rejects_wrong_key_before_action_dispatch(self):
        rejection = self.code.index('failureResponse_("UNAUTHORIZED"')
        dispatch = self.code.index("switch (request.action)")
        self.assertLess(rejection, dispatch)

    def test_only_authenticated_web_entrypoints_are_public(self):
        functions = set(
            re.findall(
                r"^function\s+([A-Za-z0-9_$]+)\s*\(",
                self.code,
                re.MULTILINE,
            )
        )
        public_functions = {name for name in functions if not name.endswith("_")}

        self.assertEqual(public_functions, {"doGet", "doPost", "handleRequest"})
        for name in (
            "setupProbeSheet_",
            "setupFamilySheets_",
            "verifyConfiguration_",
        ):
            self.assertIn(name, functions)

    def test_supports_ping_bootstrap_later_history_and_probe_operations(self):
        self.assertIn('case "ping"', self.code)
        self.assertIn('case "bootstrap"', self.code)
        self.assertIn('case "listLater"', self.code)
        self.assertIn('case "listHistory"', self.code)
        self.assertIn("function listHistoryData_()", self.code)
        self.assertIn('task.status === "Klar"', self.code)
        self.assertIn('case "probeWrite"', self.code)
        self.assertIn('case "probeRead"', self.code)
        self.assertIn('=== requestId', self.code)

    def test_create_and_update_are_authenticated_idempotent_and_versioned(self):
        self.assertIn('case "createTask"', self.code)
        self.assertIn('case "updateTask"', self.code)
        self.assertIn("function createTask_(request, member)", self.code)
        self.assertIn("function updateTask_(request, member)", self.code)
        self.assertIn("withTaskLock_", self.code)
        self.assertIn("duplicate: true", self.code)
        self.assertIn('apiError_("VERSION_CONFLICT", { latestTask: existing.task })', self.code)
        self.assertIn('throw apiError_("INVALID_INPUT")', self.code)
        self.assertIn("if (error?.apiCode)", self.code)
        self.assertIn("version: existing.task.version + 1", self.code)
        self.assertNotIn("request.member", self.code)

    def test_status_lifecycle_is_versioned_and_server_audited(self):
        self.assertIn('case "changeStatus"', self.code)
        self.assertIn('case "deleteTask"', self.code)
        self.assertIn("function mutateTaskStatus_", self.code)
        self.assertIn('task.status = "Raderad"', self.code)
        self.assertIn("version: existing.task.version + 1", self.code)
        self.assertIn("task.updated_by = member", self.code)

    def test_completion_uses_authenticated_member_and_server_timestamp(self):
        self.assertIn('["Aktuell", "Senare", "Klar"]', self.code)
        self.assertIn('if (input.status === "Klar")', self.code)
        self.assertIn("task.completed_by = member", self.code)
        self.assertIn("task.completed_at = now", self.code)
        self.assertNotIn("request.completed_by", self.code)
        self.assertNotIn("request.completed_at", self.code)

    def test_history_is_filtered_without_cleanup_and_sorted_newest_first(self):
        history = self.code[
            self.code.index("function listHistoryData_") : self.code.index("function createTask_")
        ]
        self.assertIn("14 * 24 * 60 * 60 * 1000", history)
        self.assertIn("Date.parse(task.completed_at) >= cutoff", history)
        self.assertIn("Date.parse(right.completed_at) - Date.parse(left.completed_at)", history)
        self.assertNotIn("writeValues_", history)

    def test_due_later_tasks_are_activated_before_bootstrap(self):
        bootstrap = self.code[self.code.index("function bootstrapData_") : self.code.index("function listLaterData_")]
        self.assertIn("activateDueLaterTasks_();", bootstrap)
        self.assertIn("function deadlineWithinSevenDays_", self.code)
        self.assertIn('task.updated_by = "Automatik"', self.code)
        self.assertIn('task.status = "Aktuell"', self.code)

    def test_assignment_audit_changes_only_when_assignee_changes(self):
        self.assertIn("if (input.assignee !== existing.task.assignee)", self.code)
        self.assertIn("updated.assigned_by = member", self.code)
        self.assertIn("updated.assigned_at = now", self.code)

    def test_all_api_responses_use_stable_envelope(self):
        for field in ("ok", "data", "error", "server_time", "api_version"):
            self.assertIn(field + ":", self.code)
        self.assertIn("successResponse_", self.code)
        self.assertIn("failureResponse_", self.code)

    def test_bootstrap_reads_only_current_tasks_members_and_favorites(self):
        self.assertIn('task.status === "Aktuell"', self.code)
        self.assertIn("MEMBERS_SHEET_NAME", self.code)
        self.assertIn("FAVORITES_SHEET_NAME", self.code)
        bootstrap = self.code[self.code.index("function bootstrapData_") : self.code.index("function listLaterData_")]
        self.assertNotIn('"Klar"', bootstrap)
        self.assertNotIn('"Raderad"', bootstrap)

    def test_bootstrap_returns_only_active_sheet_favorites(self):
        bootstrap = self.code[
            self.code.index("function bootstrapData_") : self.code.index("function listLaterData_")
        ]
        self.assertIn("favorites: parsed.favorites.filter", bootstrap)
        self.assertIn("return favorite.active", bootstrap)

    def test_bootstrap_does_not_read_history_sheet(self):
        self.assertNotIn("HISTORY_SHEET_NAME", self.code)
        self.assertNotIn("Historik'!", self.code)

    def test_invalid_sheet_rows_are_isolated(self):
        self.assertIn('error: "INVALID_ROW"', self.code)
        self.assertIn("parsed.push(parser(row || []))", self.code)
        self.assertIn("invalidRows.push", self.code)

    def test_blank_checkbox_rows_are_not_reported_as_invalid(self):
        self.assertIn("const normalized = String(value ||", self.code)
        self.assertIn('normalized === "" || normalized === "false"', self.code)
        self.assertIn(".trim().toLowerCase()", self.code)

    def test_setup_uses_single_status_based_tasks_sheet(self):
        self.assertIn("function setupFamilySheets_()", self.code)
        self.assertIn('TASKS_SHEET_NAME = "Uppgifter"', self.code)
        self.assertIn('"Status"', self.code)
        self.assertNotIn('TASKS_SHEET_NAME = "Aktiva"', self.code)

    def test_serializes_probe_writes_with_script_lock(self):
        self.assertIn("LockService.getScriptLock()", self.code)
        self.assertIn("lock.tryLock(5000)", self.code)
        self.assertIn("lock.releaseLock()", self.code)

    def test_probe_sheet_is_separate_from_family_tasks(self):
        self.assertIn('PROBE_SHEET_NAME = "Tekniskt test"', self.code)
        self.assertIn("function setupProbeSheet_()", self.code)

    def test_direct_post_returns_json_without_putting_key_in_url(self):
        self.assertIn("function doPost(event)", self.code)
        self.assertIn("ContentService.MimeType.JSON", self.code)
        self.assertNotIn("deviceToken=", self.code + self.bridge)

    def test_bridge_restricts_parent_origin_and_targets_reply_origin(self):
        self.assertIn("allowedOrigins.has(event.origin)", self.bridge)
        self.assertIn("event.source !== window.top", self.bridge)
        self.assertIn("event.source?.postMessage", self.bridge)
        self.assertIn("}, event.origin);", self.bridge)
        self.assertIn("window.top.postMessage", self.bridge)

    def test_bridge_requires_a_validated_client_nonce(self):
        self.assertIn("function doGet(event)", self.code)
        self.assertIn("normalizeBridgeNonce_(event?.parameter?.bridgeNonce)", self.code)
        self.assertIn("/^[a-f0-9]{64}$/", self.code)
        self.assertIn("template.bridgeNonceJson", self.code)
        self.assertIn("const bridgeNonce = <?!= bridgeNonceJson ?>;", self.bridge)
        self.assertIn("message.bridgeNonce !== bridgeNonce", self.bridge)

    def test_bridge_ready_signal_never_uses_a_wildcard_target(self):
        self.assertIn("for (const origin of allowedOrigins)", self.bridge)
        self.assertIn("}, origin);", self.bridge)
        self.assertNotIn(
            "window.top.postMessage({ type: 'gumli-family-ready' }, '*')",
            self.bridge,
        )

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
