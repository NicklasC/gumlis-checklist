from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class HistoryPageTests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        self.select_tab("Historik")

    def test_private_empty_state(self):
        self.assertTrue(self.page.get_by_text("Ingen privat historik än", exact=True).is_visible())

    def test_work_empty_state(self):
        self.set_mode("Jobb")
        self.assertTrue(self.page.get_by_text("Ingen jobb-historik än", exact=True).is_visible())

    def test_history_page_has_no_restore_button_when_empty(self):
        self.assertEqual(self.page.locator('[aria-label="Återställ till checklistan"]').count(), 0)
