from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class FavoritesPageTests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        self.select_tab("Snabblistan")

    def favorite_input(self):
        return self.page.get_by_role("textbox", name="Skriv ny favorit...")

    def add_favorite(self, title):
        field = self.favorite_input()
        field.fill(title)
        field.press("Enter")
        self.page.get_by_text(title, exact=True).wait_for(state="visible", timeout=10_000)

    def test_private_group_is_visible(self):
        self.assertTrue(self.page.get_by_text("Privat favoriter", exact=True).is_visible())

    def test_work_group_is_visible_after_mode_switch(self):
        self.set_mode("Jobb")
        self.assertTrue(self.page.get_by_text("Jobb favoriter", exact=True).is_visible())

    def test_adds_favorite_with_enter(self):
        self.add_favorite("E2E favorit")
        self.assertTrue(self.page.get_by_text("E2E favorit", exact=True).is_visible())

    def test_blank_favorite_is_ignored(self):
        before = self.page.locator('[aria-label="Ta bort favorit"]').count()
        self.favorite_input().fill("   ")
        self.favorite_input().press("Enter")
        self.assertEqual(self.page.locator('[aria-label="Ta bort favorit"]').count(), before)

    def test_duplicate_favorite_is_ignored(self):
        self.add_favorite("Ingen dubblett")
        field = self.favorite_input()
        field.fill("Ingen dubblett")
        field.press("Enter")
        self.assertEqual(self.page.get_by_text("Ingen dubblett", exact=True).count(), 1)

    def test_deletes_new_favorite(self):
        self.add_favorite("Ta bort favorit")
        delete_buttons = self.page.locator('[aria-label="Ta bort favorit"]')
        delete_buttons.last.click()
        self.page.get_by_text("Ta bort favorit", exact=True).wait_for(state="hidden")

    def test_tapping_favorite_adds_checklist_item(self):
        self.page.get_by_role("button", name="Vattna blommorna", exact=True).click()
        self.select_tab("Checklista")
        self.assertTrue(self.page.get_by_text("Vattna blommorna", exact=True).is_visible())

    def test_private_favorite_is_not_shown_in_work_group(self):
        self.set_mode("Jobb")
        self.assertEqual(self.page.get_by_role("button", name="Vattna blommorna", exact=True).count(), 0)
