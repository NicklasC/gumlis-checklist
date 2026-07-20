from datetime import date, timedelta

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


@e2e_test
class HistoryCompletionFlowTests(BrowserTestCase):
    def test_completed_item_uses_completion_day_after_next_day_cleanup(self):
        title = "Klar på rätt historikdatum"
        self.add_checklist_item(title)
        self.page.locator('[aria-label="Markera som klar"]').click()
        self.page.locator('[aria-label="Markera som ogjord"]').wait_for(state="visible")
        self.wait_for_storage_flush()

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.page.evaluate(
            """async ({ title, yesterday }) => {
                const db = await new Promise((resolve, reject) => {
                    const request = indexedDB.open('gumli-direct-storage', 1);
                    request.onsuccess = () => resolve(request.result);
                    request.onerror = () => reject(request.error);
                });
                const raw = await new Promise((resolve, reject) => {
                    const transaction = db.transaction('app-data', 'readonly');
                    const request = transaction.objectStore('app-data').get('checklists-json');
                    request.onsuccess = () => resolve(request.result);
                    request.onerror = () => reject(request.error);
                });
                const data = JSON.parse(raw);
                const active = data.checklists.find(item => item.id === 'active_list');
                const task = active.items.find(item => item.title === title);
                active.last_cleaned_date = yesterday;
                task.completed_at = `${yesterday}T21:15:00+02:00`;
                await new Promise((resolve, reject) => {
                    const transaction = db.transaction('app-data', 'readwrite');
                    transaction.objectStore('app-data').put(JSON.stringify(data), 'checklists-json');
                    transaction.oncomplete = resolve;
                    transaction.onerror = () => reject(transaction.error);
                });
                db.close();
            }""",
            {"title": title, "yesterday": yesterday},
        )

        self.page.reload()
        self.boot()
        self.select_tab("Historik")

        self.page.get_by_text(title, exact=True).wait_for(state="visible")
        self.assertTrue(self.page.get_by_text("IGÅR", exact=True).is_visible())
        self.assertEqual(self.page.get_by_text("IDAG", exact=True).count(), 0)
