from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class ChecklistPageTests(BrowserTestCase):
    def test_adds_item_with_enter(self):
        self.submit_checklist_item_with_enter("E2E lägg till")
        self.assertTrue(self.page.get_by_text("E2E lägg till", exact=True).is_visible())

    def test_blank_text_does_not_add_item(self):
        field = self.checklist_input()
        field.fill("   ")
        field.press("Enter")
        self.assertEqual(self.page.locator('[aria-label="Radera"]').count(), 0)

    def test_submission_trims_visible_title(self):
        field = self.checklist_input()
        field.fill("  Trimmad titel  ")
        self.page.get_by_role("button", name="+ Att göra", exact=True).click()
        self.page.get_by_text("Trimmad titel", exact=True).wait_for(state="visible")

    def test_submission_clears_input(self):
        self.add_checklist_item("Fältet töms")
        self.assertEqual(self.checklist_input().input_value(), "")

    def test_deletes_item(self):
        self.add_checklist_item("Radera mig")
        self.page.locator('[aria-label="Radera"]').click()
        self.page.get_by_text("Radera mig", exact=True).wait_for(state="hidden")

    def test_marks_item_complete(self):
        self.add_checklist_item("Klar")
        self.page.locator('[aria-label="Markera som klar"]').click()
        self.page.locator('[aria-label="Markera som ogjord"]').wait_for(state="visible")

    def test_marks_completed_item_undone(self):
        self.add_checklist_item("Ångra klar")
        self.page.locator('[aria-label="Markera som klar"]').click()
        self.page.locator('[aria-label="Markera som ogjord"]').click()
        self.page.locator('[aria-label="Markera som klar"]').wait_for(state="visible")

    def test_moves_item_to_later(self):
        self.add_checklist_item("Flytta mig")
        self.page.locator('[aria-label="Flytta till Senare"]').click()
        self.page.get_by_text("Flytta mig", exact=True).wait_for(state="hidden")

    def test_private_item_is_hidden_in_work_mode(self):
        self.add_checklist_item("Endast privat")
        self.set_mode("Jobb")
        self.assertEqual(self.page.get_by_text("Endast privat", exact=True).count(), 0)

    def test_work_item_is_visible_in_work_mode(self):
        self.set_mode("Jobb")
        self.submit_checklist_item_with_enter("Endast jobb")
        self.assertTrue(self.page.get_by_text("Endast jobb", exact=True).is_visible())

    def test_private_empty_state_is_visible(self):
        self.assertTrue(self.page.get_by_text("Allt klart på den privata listan!", exact=True).is_visible())

    def test_work_empty_state_is_visible(self):
        self.set_mode("Jobb")
        self.assertTrue(self.page.get_by_text("Allt klart på jobb-listan!", exact=True).is_visible())
