import unittest

from tests.support.paths import PWA_TEMPLATES


class IndexTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (PWA_TEMPLATES / "index.html").read_text(encoding="utf-8")

    def test_uses_github_pages_base_path(self):
        self.assertIn('<base href="/gumlis-checklist/">', self.html)

    def test_mobile_keyboard_resizes_the_layout_viewport(self):
        self.assertIn(
            "interactive-widget=resizes-content",
            self.html,
        )
        self.assertIn("new MutationObserver(applyKeyboardViewport)", self.html)

    def test_sets_flet_entrypoint_base(self):
        self.assertIn('flet.entrypointBaseUrl="/gumlis-checklist/"', self.html)

    def test_sets_flet_asset_base(self):
        self.assertIn('flet.assetBase="/gumlis-checklist/"', self.html)

    def test_uses_flet_runtime_cdn(self):
        self.assertIn("flet.noCdn=false", self.html)

    def test_references_manifest(self):
        self.assertIn("manifest.json", self.html)

    def test_references_favicon(self):
        self.assertIn("favicon.png", self.html)

    def test_registers_service_worker(self):
        self.assertIn("navigator.serviceWorker.register('flutter_service_worker.js')", self.html)

    def test_cache_busts_python_app_archive(self):
        self.assertIn("app.tar.gz?build=__APP_ARCHIVE_HASH__", self.html)

    def test_exposes_startup_timing_marks(self):
        self.assertIn("window.gumliStartup", self.html)
        self.assertIn("performance.mark(`gumli:${name}`)", self.html)

    def test_startup_console_logging_is_opt_in(self):
        self.assertIn("get('debug-startup') === '1'", self.html)

    def test_marks_flutter_ready(self):
        self.assertIn("mark('flutter-app-ready')", self.html)


class ServiceWorkerTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = (PWA_TEMPLATES / "flutter_service_worker.js").read_text(encoding="utf-8")

    def test_has_versioned_cache_name(self):
        self.assertIn("const BUILD_VERSION = '__APP_ARCHIVE_HASH__'", self.worker)
        self.assertIn("const CACHE_NAME = `${CACHE_PREFIX}${BUILD_VERSION}`", self.worker)

    def test_has_install_handler(self):
        self.assertIn("addEventListener('install'", self.worker)

    def test_has_activate_handler(self):
        self.assertIn("addEventListener('activate'", self.worker)

    def test_has_fetch_handler(self):
        self.assertIn("addEventListener('fetch'", self.worker)

    def test_precaches_lightweight_app_shell(self):
        self.assertIn("cache.addAll(APP_SHELL)", self.worker)

    def test_removes_old_versioned_caches(self):
        self.assertIn("name !== CACHE_NAME", self.worker)
        self.assertIn("caches.delete(name)", self.worker)

    def test_navigation_uses_network_first(self):
        self.assertIn("event.respondWith(networkFirst(request))", self.worker)

    def test_static_resources_use_cache_first(self):
        self.assertIn("event.respondWith(cacheFirst(request))", self.worker)

    def test_only_trusted_runtime_cdns_are_cacheable(self):
        self.assertIn("RUNTIME_CDN_HOSTS", self.worker)
        self.assertIn("cdn.jsdelivr.net", self.worker)
        self.assertIn("www.gstatic.com", self.worker)

    def test_only_caches_successful_responses(self):
        self.assertIn("if (response.ok)", self.worker)
