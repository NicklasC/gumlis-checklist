import json
import unittest

from tests.support.paths import PWA_TEMPLATES


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_path = PWA_TEMPLATES / "manifest.json"
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))

    def test_manifest_exists(self):
        self.assertTrue(self.manifest_path.is_file())

    def test_name_is_gumli(self):
        self.assertEqual(self.manifest["name"], "Gumli")

    def test_short_name_is_gumli(self):
        self.assertEqual(self.manifest["short_name"], "Gumli")

    def test_start_url_is_relative(self):
        self.assertEqual(self.manifest["start_url"], ".")

    def test_display_mode_is_standalone(self):
        self.assertEqual(self.manifest["display"], "standalone")

    def test_theme_color_is_defined(self):
        self.assertRegex(self.manifest["theme_color"], r"^#[0-9A-Fa-f]{6}$")

    def test_contains_four_install_icons(self):
        self.assertEqual(len(self.manifest["icons"]), 4)

    def test_all_manifest_icons_exist(self):
        for icon in self.manifest["icons"]:
            with self.subTest(icon=icon["src"]):
                self.assertTrue((PWA_TEMPLATES / icon["src"]).is_file())

    def test_all_manifest_icons_are_png(self):
        for icon in self.manifest["icons"]:
            with self.subTest(icon=icon["src"]):
                self.assertEqual(icon["type"], "image/png")

    def test_maskable_icons_declare_purpose(self):
        maskable = [icon for icon in self.manifest["icons"] if "maskable" in icon["src"]]
        self.assertTrue(all(icon.get("purpose") == "maskable" for icon in maskable))
