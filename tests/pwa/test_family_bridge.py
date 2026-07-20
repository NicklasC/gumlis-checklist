import unittest

from tests.support.paths import PROJECT_ROOT, PWA_TEMPLATES


class FamilyBridgeTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PWA_TEMPLATES / "index.html").read_text(encoding="utf-8")
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

    def test_bridge_validates_iframe_source_and_response_origin(self):
        self.assertIn("event.source !== bridgeWindow", self.html)
        self.assertIn("event.origin !== bridgeOrigin", self.html)
        self.assertIn("event.origin.endsWith('.googleusercontent.com')", self.html)
        self.assertNotIn("!debug.frameLoaded || bridgeWindow", self.html)

    def test_bridge_has_ten_second_timeout(self):
        self.assertIn("}, 10000);", self.html)
        self.assertIn("timeout_seconds: float = 10.0", self.python_bridge)

    def test_diagnostics_never_store_request_payload_or_token(self):
        debug_block = self.html.split("const debug =", 1)[1].split("window.gumliFamilyDebug", 1)[0]
        self.assertNotIn("payload", debug_block)
        self.assertNotIn("deviceToken", debug_block)

    def test_diagnostics_reads_member_from_stable_response_envelope(self):
        self.assertIn("message.response?.data?.member || message.response?.member", self.html)

    def test_deploy_forwards_only_family_worker_messages(self):
        self.assertIn('event.data?.type === \\"gumli-family-request\\"', self.deploy)
        self.assertIn("window.gumliFamilyBridge?.forward", self.deploy)


if __name__ == "__main__":
    unittest.main()
