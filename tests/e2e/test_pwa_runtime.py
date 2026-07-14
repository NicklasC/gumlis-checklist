from urllib.request import urlopen

from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class PwaRuntimeTests(BrowserTestCase):
    def response(self, relative_path):
        return urlopen(self.server.base_url + relative_path)

    def test_index_returns_html(self):
        self.assertIn("text/html", self.response("").headers.get_content_type())

    def test_mjs_uses_javascript_mime_type(self):
        self.assertEqual(self.response("main.dart.mjs").headers.get_content_type(), "application/javascript")

    def test_wasm_uses_wasm_mime_type(self):
        self.assertEqual(self.response("main.dart.wasm").headers.get_content_type(), "application/wasm")

    def test_manifest_is_reachable(self):
        self.assertEqual(self.response("manifest.json").status, 200)

    def test_service_worker_is_reachable(self):
        self.assertEqual(self.response("flutter_service_worker.js").status, 200)

    def test_service_worker_registers_in_browser(self):
        registration = self.page.evaluate(
            """async () => {
                const ready = navigator.serviceWorker.ready.then(() => true);
                const timedOut = new Promise(resolve => setTimeout(() => resolve(false), 5000));
                if (!await Promise.race([ready, timedOut])) return false;
                return Boolean(await navigator.serviceWorker.getRegistration());
            }"""
        )
        self.assertTrue(registration)

    def test_app_boots_without_console_errors(self):
        self.assert_no_unexpected_console_errors()
