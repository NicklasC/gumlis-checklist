from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class LaterPageTests(BrowserTestCase):
    def setUp(self):
        super().setUp()
        self.select_tab("Senare")

    def later_input(self):
        return self.page.get_by_role("textbox", name="Lägg till i Senare...")

    def add_later_item(self, title):
        field = self.later_input()
        field.fill(title)
        field.press("Enter")
        self.page.get_by_text(title, exact=True).wait_for(state="visible")

    def test_adds_private_later_item(self):
        self.add_later_item("Privat senare")
        self.assertTrue(self.page.get_by_text("Privat senare", exact=True).is_visible())

    def test_adds_work_later_item(self):
        self.set_mode("Jobb")
        self.add_later_item("Jobb senare")
        self.assertTrue(self.page.get_by_text("Jobb senare", exact=True).is_visible())

    def test_blank_later_item_is_ignored(self):
        self.later_input().fill("   ")
        self.later_input().press("Enter")
        self.assertEqual(self.page.locator('[aria-label="Ta bort"]').count(), 0)

    def test_deletes_later_item(self):
        self.add_later_item("Ta bort senare")
        self.page.locator('[aria-label="Ta bort"]').click()
        self.page.get_by_text("Ta bort senare", exact=True).wait_for(state="hidden")

    def test_promotes_later_item_to_today(self):
        self.add_later_item("Till idag")
        self.page.locator('[aria-label="Flytta till idag"]').click()
        self.select_tab("Checklista")
        self.assertTrue(self.page.get_by_text("Till idag", exact=True).is_visible())

    def test_private_later_item_is_hidden_in_work_mode(self):
        self.add_later_item("Bara privat senare")
        self.set_mode("Jobb")
        self.assertEqual(self.page.get_by_text("Bara privat senare", exact=True).count(), 0)

    def test_checklist_later_button_routes_to_later_page(self):
        self.select_tab("Checklista")
        field = self.checklist_input()
        field.fill("Via senareknappen")
        self.page.get_by_role("button", name="+ Senare", exact=True).click()
        self.select_tab("Senare")
        self.assertTrue(self.page.get_by_text("Via senareknappen", exact=True).is_visible())
