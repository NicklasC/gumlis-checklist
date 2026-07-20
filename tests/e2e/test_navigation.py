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

    def test_all_pages_remain_reachable_after_successful_family_response(self):
        self.page.evaluate(
            """() => {
                window.gumliFamilyBridge.forward = (message, worker) => {
                    const isBootstrap = message.payload?.action === 'bootstrap';
                    worker.postMessage({
                        type: 'gumli-family-response',
                        requestId: message.requestId,
                        response: {
                            ok: true,
                            data: isBootstrap
                                ? {
                                    tasks: [
                                        {
                                            id: 'family-overdue', title: 'Försenad familjeuppgift',
                                            status: 'Aktuell', assignee: 'Nicklas',
                                            assigned_by: 'Nicklas', assigned_at: '2026-07-20T08:00:00+00:00',
                                            created_by: 'Nicklas', created_at: '2026-07-20T08:00:00+00:00',
                                            deadline: '2026-07-18', updated_by: 'Nicklas',
                                            updated_at: '2026-07-20T08:00:00+00:00',
                                            completed_by: null, completed_at: null, version: 1
                                        },
                                        {
                                            id: 'family-all', title: 'Gemensam familjeuppgift',
                                            status: 'Aktuell', assignee: 'Alla',
                                            assigned_by: 'Nicklas', assigned_at: '2026-07-20T08:00:00+00:00',
                                            created_by: 'Nicklas', created_at: '2026-07-20T08:00:00+00:00',
                                            deadline: null, updated_by: 'Nicklas',
                                            updated_at: '2026-07-20T08:00:00+00:00',
                                            completed_by: null, completed_at: null, version: 1
                                        }
                                    ],
                                    members: [{name: 'Nicklas', active: true, sort_order: 1}],
                                    favorites: [], invalidRows: []
                                }
                                : {member: 'Nicklas'},
                            server_time: '2026-07-20T12:00:00+00:00'
                        }
                    });
                };
            }"""
        )

        self.set_mode("Familj")
        self.page.get_by_role("textbox", name="Enhetsnyckel").fill("n" * 48)
        self.page.get_by_role("button", name="Anslut den här enheten", exact=True).click()
        self.page.get_by_text("Ansluten som Nicklas", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Försenad 2 dagar", exact=True).wait_for(state="visible", timeout=10_000)
        self.assertTrue(self.page.get_by_text("Försenad familjeuppgift", exact=True).is_visible())
        self.assertTrue(self.page.get_by_role("button", name="Alla (2)", exact=True).is_visible())
        self.assertTrue(self.page.get_by_role("button", name="Mina (1)", exact=True).is_visible())
        self.page.get_by_role("button", name="Mina (1)", exact=True).click()
        self.page.get_by_text("Gemensam familjeuppgift", exact=True).wait_for(state="hidden")

        destinations = {
            "Checklista": {
                "Privat": "Allt klart på den privata listan!",
                "Jobb": "Allt klart på jobb-listan!",
            },
            "Snabblistan": {
                "Privat": "Hantera favoriter",
                "Jobb": "Hantera favoriter",
            },
            "Historik": {
                "Privat": "Ingen privat historik än",
                "Jobb": "Ingen jobb-historik än",
            },
            "Senare": {
                "Privat": "Inga privata uppgifter i Senare",
                "Jobb": "Inga jobb-uppgifter i Senare",
            },
        }

        for mode in ("Privat", "Jobb"):
            self.set_mode(mode)
            for tab_name, expected_by_mode in destinations.items():
                self.select_tab(tab_name)
                self.assertTrue(
                    self.page.get_by_text(expected_by_mode[mode], exact=True).is_visible(),
                    f"{mode} / {tab_name} öppnade inte avsedd sida",
                )

            if mode == "Privat":
                self.set_mode("Familj")
                self.page.get_by_text("Ansluten som Nicklas", exact=True).wait_for(
                    state="visible", timeout=10_000
                )

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
