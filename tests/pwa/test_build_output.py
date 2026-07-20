import json
import unittest

from tests.support.paths import DEPLOY_APP


@unittest.skipUnless(DEPLOY_APP.is_dir(), "Built PWA is not available")
class BuildOutputTests(unittest.TestCase):
    def test_index_exists(self):
        self.assertTrue((DEPLOY_APP / "index.html").is_file())

    def test_manifest_exists(self):
        self.assertTrue((DEPLOY_APP / "manifest.json").is_file())

    def test_service_worker_exists(self):
        self.assertTrue((DEPLOY_APP / "flutter_service_worker.js").is_file())

    def test_python_application_archive_exists(self):
        self.assertTrue((DEPLOY_APP / "app.tar.gz").is_file())

    def test_flet_javascript_bundle_exists(self):
        self.assertTrue((DEPLOY_APP / "main.dart.mjs").is_file())

    def test_flet_wasm_bundle_exists(self):
        self.assertTrue((DEPLOY_APP / "main.dart.wasm").is_file())

    def test_python_worker_exists(self):
        self.assertTrue((DEPLOY_APP / "python-worker.js").is_file())

    def test_python_host_forwards_startup_marks(self):
        python_host = (DEPLOY_APP / "python.js").read_text(encoding="utf-8")
        self.assertIn("__gumli_startup__:", python_host)

    def test_python_worker_does_not_forward_family_responses_to_flet(self):
        worker = (DEPLOY_APP / "python-worker.js").read_text(encoding="utf-8")
        guard = worker.index('event.data?.type === "gumli-family-response"')
        flet_send = worker.index("flet_js.send(event.data)")
        self.assertLess(guard, flet_send)

    def test_built_manifest_is_valid_json(self):
        value = json.loads((DEPLOY_APP / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(value["name"], "Gumli")

    def test_built_index_uses_expected_base(self):
        html = (DEPLOY_APP / "index.html").read_text(encoding="utf-8")
        self.assertIn('/gumlis-checklist/', html)

    def test_built_index_uses_hashed_python_archive_url(self):
        html = (DEPLOY_APP / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, r'appPackageUrl: "app\.tar\.gz\?build=[0-9a-f]{16}"')

    def test_built_icons_directory_exists(self):
        self.assertTrue((DEPLOY_APP / "icons").is_dir())

    def test_built_192_icon_exists(self):
        self.assertTrue((DEPLOY_APP / "icons" / "icon-192.png").is_file())

    def test_built_512_icon_exists(self):
        self.assertTrue((DEPLOY_APP / "icons" / "icon-512.png").is_file())
