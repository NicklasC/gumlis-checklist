import tempfile

from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class ReloadPersistenceTests(BrowserTestCase):
    def test_favorite_survives_reload(self):
        self.select_tab("Snabblistan")
        field = self.page.get_by_role("textbox", name="Skriv ny favorit...")
        field.fill("Beständig favorit")
        field.press("Enter")
        self.page.get_by_text("Beständig favorit", exact=True).wait_for(state="visible")
        self.wait_for_storage_flush()
        self.page.reload()
        self.boot()
        self.select_tab("Snabblistan")
        self.assertTrue(self.page.get_by_role("button", name="Beständig favorit", exact=True).is_visible())

    def test_checklist_item_survives_reload(self):
        self.add_checklist_item("Beständig uppgift")
        self.wait_for_storage_flush()
        self.page.reload()
        self.boot()
        self.assertTrue(self.page.get_by_text("Beständig uppgift", exact=True).is_visible())

    def test_deletion_survives_reload(self):
        self.add_checklist_item("Raderad beständigt")
        self.page.locator('[aria-label="Radera"]').click()
        self.page.get_by_text("Raderad beständigt", exact=True).wait_for(state="hidden")
        self.wait_for_storage_flush()
        self.page.reload()
        self.boot()
        self.assertEqual(self.page.get_by_text("Raderad beständigt", exact=True).count(), 0)

    def test_checked_state_survives_reload(self):
        self.add_checklist_item("Beständigt klar")
        self.page.locator('[aria-label="Markera som klar"]').click()
        self.page.locator('[aria-label="Markera som ogjord"]').wait_for(state="visible")
        self.wait_for_storage_flush()
        self.page.reload()
        self.boot()
        self.assertEqual(self.page.locator('[aria-label="Markera som ogjord"]').count(), 1)

    def test_later_item_survives_reload(self):
        self.select_tab("Senare")
        field = self.page.get_by_role("textbox", name="Lägg till i Senare...")
        field.fill("Beständig senare")
        field.press("Enter")
        self.page.get_by_text("Beständig senare", exact=True).wait_for(state="visible")
        self.wait_for_storage_flush()
        self.page.reload()
        self.boot()
        self.select_tab("Senare")
        self.assertTrue(self.page.get_by_text("Beständig senare", exact=True).is_visible())


@e2e_test
class BrowserRestartPersistenceTests(BrowserTestCase):
    def test_favorite_survives_new_page_in_same_context(self):
        self.select_tab("Snabblistan")
        field = self.page.get_by_role("textbox", name="Skriv ny favorit...")
        field.fill("Ny sida")
        field.press("Enter")
        self.page.get_by_text("Ny sida", exact=True).wait_for(state="visible")
        self.wait_for_storage_flush()
        self.page.close()
        self.page = self.context.new_page()
        self.boot()
        self.select_tab("Snabblistan")
        self.assertTrue(self.page.get_by_role("button", name="Ny sida", exact=True).is_visible())
