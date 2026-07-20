from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class NavigationTests(BrowserTestCase):
    def test_app_title_is_visible(self):
        self.assertTrue(self.page.get_by_text("Gumli", exact=True).is_visible())

    def test_has_four_navigation_tabs(self):
        self.assertEqual(self.page.get_by_role("tab").count(), 4)

    def test_checklist_tab_is_selected_initially(self):
        self.assertEqual(self.page.get_by_role("tab", name="Checklista").get_attribute("aria-selected"), "true")

    def test_favorites_page_opens(self):
        self.select_tab("Snabblistan")
        self.assertTrue(self.page.get_by_text("Hantera favoriter", exact=True).is_visible())

    def test_history_page_opens(self):
        self.select_tab("Historik")
        self.assertTrue(self.page.get_by_text("Ingen privat historik än", exact=True).is_visible())

    def test_later_page_opens(self):
        self.select_tab("Senare")
        self.assertTrue(self.page.get_by_text("Inga privata uppgifter i Senare", exact=True).is_visible())

    def test_switches_to_work_mode(self):
        self.set_mode("Jobb")
        self.assertTrue(self.page.get_by_text("Allt klart på jobb-listan!", exact=True).is_visible())

    def test_switches_back_to_private_mode(self):
        self.set_mode("Jobb")
        self.set_mode("Privat")
        self.assertTrue(self.page.get_by_text("Allt klart på den privata listan!", exact=True).is_visible())

    def test_switches_directly_from_family_back_to_private(self):
        self.set_mode("Familj")
        self.assertTrue(self.page.get_by_text("Anslut Familj", exact=True).is_visible())
        self.set_mode("Privat")
        self.assertTrue(self.page.get_by_text("Allt klart på den privata listan!", exact=True).is_visible())

    def test_family_device_key_can_be_entered_and_reveal_control_used(self):
        self.set_mode("Familj")
        field = self.page.get_by_role("textbox", name="Enhetsnyckel")
        field.fill("SynligEnhetsnyckel123456789012345")
        self.assertEqual(field.input_value(), "SynligEnhetsnyckel123456789012345")
        reveal_button = self.page.locator(
            'flt-semantics:has(> input[aria-label="Enhetsnyckel"]) + flt-semantics[role="button"]'
        )
        self.assertEqual(reveal_button.count(), 1)
        reveal_button.click()
        self.assertEqual(field.input_value(), "SynligEnhetsnyckel123456789012345")

    def test_boot_has_no_console_errors(self):
        self.assert_no_unexpected_console_errors()
