import unittest

from tests.support.paths import PROJECT_ROOT, PWA_TEMPLATES


class FamilyBridgeTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PWA_TEMPLATES / "index.html").read_text(encoding="utf-8")
        marker = cls.html.index("// Created only after the user opens Familj")
        script_start = cls.html.rfind("<script>", 0, marker) + len("<script>")
        script_end = cls.html.index("</script>", marker)
        cls.family_script = cls.html[script_start:script_end]
        cls.deploy = (PROJECT_ROOT / "deploy.py").read_text(encoding="utf-8")
        cls.python_bridge = (PROJECT_ROOT / "src" / "repositories" / "family_bridge.py").read_text(
            encoding="utf-8"
        )

    def test_family_iframe_is_created_lazily(self):
        self.assertIn("const ensureFrame = () =>", self.html)
        self.assertIn("document.createElement('iframe')", self.html)
        self.assertNotIn('<iframe src="https://script.google.com', self.html)

    def test_device_token_is_not_part_of_api_url(self):
        api_line = next(line for line in self.html.splitlines() if "const apiUrl" in line)
        self.assertNotIn("deviceToken", api_line)
        self.assertNotIn("deviceToken=", self.html + self.python_bridge)

    def test_bridge_authenticates_sandbox_before_binding_window(self):
        nonce_check = self.family_script.index("message.bridgeNonce !== bridgeNonce")
        window_binding = self.family_script.index("bridgeWindow = event.source")
        self.assertLess(nonce_check, window_binding)
        self.assertIn("!isTrustedAppsScriptSandboxOrigin(event.origin)", self.family_script)
        self.assertNotIn("event.origin.endsWith('.googleusercontent.com')", self.family_script)
        self.assertIn("event.source !== bridgeWindow", self.html)
        self.assertIn("event.origin !== bridgeOrigin", self.html)
        self.assertIn("message.bridgeNonce !== bridgeNonce", self.html)
        self.assertNotIn("!debug.frameLoaded || bridgeWindow", self.html)

    def test_bridge_nonce_uses_cryptographic_randomness(self):
        self.assertIn(
            "crypto.getRandomValues(new Uint8Array(32))",
            self.family_script,
        )
        self.assertIn(
            "frameUrl.searchParams.set('bridgeNonce', bridgeNonce)",
            self.family_script,
        )
        self.assertNotIn("Math.random", self.family_script)

    def test_family_bridge_refuses_to_run_when_gumli_is_embedded(self):
        self.assertIn("window.top !== window.self", self.family_script)

    def test_timed_out_handshake_is_reset_and_never_sent_late(self):
        guard = self.family_script.index("if (!pending.has(message.requestId)) return;")
        send = self.family_script.index("bridgeWindow.postMessage({")
        self.assertLess(guard, send)
        self.assertIn("const resetUnreadyFrame = () =>", self.family_script)
        self.assertIn(
            "if (!bridgeWindow && pending.size === 0) resetUnreadyFrame();",
            self.family_script,
        )

    def test_bridge_has_ten_second_timeout(self):
        self.assertIn("}, 10000);", self.html)
        self.assertIn("timeout_seconds: float = 10.0", self.python_bridge)

    def test_diagnostics_never_store_request_payload_or_token(self):
        debug_block = self.html.split("const debug =", 1)[1].split("window.gumliFamilyDebug", 1)[0]
        self.assertNotIn("payload", debug_block)
        self.assertNotIn("deviceToken", debug_block)
        self.assertNotIn("bridgeNonce", debug_block)

    def test_diagnostics_reads_member_from_stable_response_envelope(self):
        self.assertIn("message.response?.data?.member || message.response?.member", self.html)

    def test_deploy_forwards_only_family_worker_messages(self):
        self.assertIn('event.data?.type === \\"gumli-family-request\\"', self.deploy)
        self.assertIn("window.gumliFamilyBridge?.forward", self.deploy)

    def test_deploy_isolates_family_responses_from_flet_messages(self):
        self.assertIn("add_python_worker_family_response_guard", self.deploy)
        self.assertIn('event.data?.type === \"gumli-family-response\"', self.deploy)


if __name__ == "__main__":
    unittest.main()
