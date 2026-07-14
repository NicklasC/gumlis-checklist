import unittest

from tests.support.paths import PWA_TEMPLATES


class IndexTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PWA_TEMPLATES / "index.html").read_text(encoding="utf-8")

    def test_uses_github_pages_base_path(self):
        self.assertIn('<base href="/gumlis-checklist/">', self.html)

    def test_sets_flet_entrypoint_base(self):
        self.assertIn('flet.entrypointBaseUrl="/gumlis-checklist/"', self.html)

    def test_sets_flet_asset_base(self):
        self.assertIn('flet.assetBase="/gumlis-checklist/"', self.html)

    def test_references_manifest(self):
        self.assertIn("manifest.json", self.html)

    def test_references_favicon(self):
        self.assertIn("favicon.png", self.html)

    def test_registers_service_worker(self):
        self.assertIn("navigator.serviceWorker.register('flutter_service_worker.js')", self.html)


class ServiceWorkerTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = (PWA_TEMPLATES / "flutter_service_worker.js").read_text(encoding="utf-8")

    def test_has_versioned_cache_name(self):
        self.assertIn("CACHE_NAME", self.worker)

    def test_has_install_handler(self):
        self.assertIn("addEventListener('install'", self.worker)

    def test_has_activate_handler(self):
        self.assertIn("addEventListener('activate'", self.worker)

    def test_has_fetch_handler(self):
        self.assertIn("addEventListener('fetch'", self.worker)

    def test_fetch_handler_returns_network_response(self):
        self.assertIn("event.respondWith(fetch(event.request))", self.worker)
