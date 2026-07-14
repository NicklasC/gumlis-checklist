from tests.support.browser_case import BrowserTestCase, e2e_test


class LayoutAssertions:
    def assert_no_horizontal_overflow(self):
        overflow = self.page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        self.assertFalse(overflow)

    def assert_screenshot_has_content(self):
        self.assertGreater(len(self.page.screenshot()), 1_000)


@e2e_test
class MinimumViewportTests(LayoutAssertions, BrowserTestCase):
    viewport = {"width": 320, "height": 600}

    def test_no_horizontal_overflow(self):
        self.assert_no_horizontal_overflow()

    def test_navigation_remains_visible(self):
        self.assertTrue(self.page.get_by_role("tab", name="Senare").is_visible())

    def test_input_remains_visible(self):
        self.assertTrue(self.checklist_input().is_visible())

    def test_viewport_renders_a_nonempty_screenshot(self):
        self.assert_screenshot_has_content()


@e2e_test
class MobileViewportTests(LayoutAssertions, BrowserTestCase):
    viewport = {"width": 410, "height": 820}

    def test_no_horizontal_overflow(self):
        self.assert_no_horizontal_overflow()

    def test_all_tabs_have_accessible_names(self):
        names = [tab.get_attribute("aria-label") for tab in self.page.get_by_role("tab").all()]
        self.assertEqual(names, ["Checklista", "Snabblistan", "Historik", "Senare"])

    def test_primary_controls_are_keyboard_focusable(self):
        self.checklist_input().focus()
        self.assertTrue(self.checklist_input().evaluate("element => element === document.activeElement"))

    def test_viewport_renders_a_nonempty_screenshot(self):
        self.assert_screenshot_has_content()


@e2e_test
class TabletViewportTests(LayoutAssertions, BrowserTestCase):
    viewport = {"width": 768, "height": 1024}

    def test_no_horizontal_overflow(self):
        self.assert_no_horizontal_overflow()

    def test_header_is_visible(self):
        self.assertTrue(self.page.get_by_text("Gumli", exact=True).is_visible())

    def test_viewport_renders_a_nonempty_screenshot(self):
        self.assert_screenshot_has_content()


@e2e_test
class DesktopViewportTests(LayoutAssertions, BrowserTestCase):
    viewport = {"width": 1280, "height": 800}

    def test_no_horizontal_overflow(self):
        self.assert_no_horizontal_overflow()

    def test_mode_buttons_are_visible(self):
        self.assertTrue(self.page.get_by_role("button", name="Privat", exact=True).is_visible())

    def test_long_title_does_not_create_page_overflow(self):
        self.add_checklist_item("Mycket lång uppgift " * 20)
        self.assert_no_horizontal_overflow()

    def test_viewport_renders_a_nonempty_screenshot(self):
        self.assert_screenshot_has_content()
