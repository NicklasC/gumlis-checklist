from datetime import date, timedelta

from tests.support.browser_case import BrowserTestCase, e2e_test


@e2e_test
class NavigationTests(BrowserTestCase):
    def install_family_polish_bridge(self, task_count=1):
        self.page.evaluate(
            """(taskCount) => {
                window.__gumliFamilyOffline = false;
                const tasks = Array.from({length: taskCount}, (_, index) => ({
                    id: `polish-${index}`,
                    title: `Pilotuppgift ${index + 1}`,
                    status: 'Aktuell',
                    assignee: index % 2 === 0 ? 'Nicklas' : 'Alla',
                    assigned_by: 'Nicklas',
                    assigned_at: '2026-07-22T12:00:00+00:00',
                    created_by: 'Nicklas',
                    created_at: `2026-07-22T12:${String(index % 60).padStart(2, '0')}:00+00:00`,
                    deadline: null,
                    updated_by: 'Nicklas',
                    updated_at: '2026-07-22T12:00:00+00:00',
                    completed_by: null,
                    completed_at: null,
                    version: 1
                }));
                window.gumliFamilyBridge.forward = (message, worker) => {
                    const action = message.payload?.action;
                    const offline = window.__gumliFamilyOffline && action !== 'ping';
                    const data = action === 'ping'
                        ? {member: 'Nicklas'}
                        : action === 'bootstrap'
                        ? {
                            tasks,
                            members: [{name: 'Nicklas', active: true, sort_order: 1}],
                            favorites: [
                                {id: 'pilot-favorite', title: 'Töm soporna', active: true, sort_order: 1}
                            ],
                            invalidRows: []
                        }
                        : {tasks: [], invalidRows: []};
                    worker.postMessage({
                        type: 'gumli-family-response',
                        requestId: message.requestId,
                        response: offline
                            ? {ok: false, data: null, error: 'SERVER_ERROR', server_time: null}
                            : {
                                ok: true,
                                data,
                                error: null,
                                server_time: '2026-07-22T12:00:00+00:00',
                                api_version: 'family-polish-test'
                            }
                    });
                };
            }""",
            task_count,
        )

    def connect_family_polish_bridge(self):
        self.set_mode("Familj")
        self.page.get_by_role("textbox", name="Enhetsnyckel").fill("n" * 48)
        self.page.get_by_role(
            "button", name="Anslut den här enheten", exact=True
        ).click()
        self.page.get_by_text("Synkad nyss", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.wait_for_timeout(500)

    def install_family_task_bridge(self):
        self.page.evaluate(
            """() => {
                let task = null;
                window.gumliFamilyBridge.forward = (message, worker) => {
                    const action = message.payload?.action;
                    const input = message.payload?.task ?? {};
                    const timestamp = '2026-07-21T08:00:00+00:00';
                    let data;
                    if (action === 'ping') {
                        data = {member: 'Nicklas'};
                    } else if (action === 'bootstrap') {
                        data = {
                            tasks: task?.status === 'Aktuell' ? [task] : [],
                            members: [{name: 'Nicklas', active: true, sort_order: 1}],
                            favorites: [
                                {id: 'favorite-trash', title: 'Töm soporna', active: true, sort_order: 1}
                            ],
                            invalidRows: []
                        };
                    } else if (action === 'createTask' || action === 'updateTask') {
                        task = {
                            id: input.id,
                            title: input.title,
                            status: 'Aktuell',
                            assignee: input.assignee,
                            assigned_by: 'Nicklas',
                            assigned_at: timestamp,
                            created_by: 'Nicklas',
                            created_at: timestamp,
                            deadline: input.deadline,
                            updated_by: 'Nicklas',
                            updated_at: timestamp,
                            completed_by: null,
                            completed_at: null,
                            version: action === 'createTask' ? 1 : input.version + 1
                        };
                        data = {task};
                    } else if (action === 'changeStatus' || action === 'deleteTask') {
                        const completed = action === 'changeStatus' && input.status === 'Klar';
                        task = {
                            ...task,
                            status: action === 'deleteTask' ? 'Raderad' : input.status,
                            updated_by: 'Nicklas',
                            updated_at: timestamp,
                            completed_by: completed ? 'Nicklas' : null,
                            completed_at: completed ? timestamp : null,
                            version: input.version + 1
                        };
                        data = {task};
                    } else if (action === 'listLater') {
                        data = {
                            tasks: task?.status === 'Senare' ? [task] : [],
                            invalidRows: []
                        };
                    } else if (action === 'listHistory') {
                        data = {
                            tasks: task?.status === 'Klar' ? [task] : [],
                            invalidRows: []
                        };
                    } else {
                        data = {tasks: [], invalidRows: []};
                    }
                    worker.postMessage({
                        type: 'gumli-family-response',
                        requestId: message.requestId,
                        response: {
                            ok: true,
                            data,
                            error: null,
                            server_time: timestamp,
                            api_version: 'family-test'
                        }
                    });
                };
            }"""
        )

    def connect_family_task_bridge(self):
        self.set_mode("Familj")
        self.page.get_by_role("textbox", name="Enhetsnyckel").fill("n" * 48)
        self.page.get_by_role(
            "button", name="Anslut den här enheten", exact=True
        ).click()
        self.page.get_by_text("Ansluten som Nicklas", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Synkad nyss", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.wait_for_timeout(500)

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

    def test_late_family_connection_does_not_override_private_navigation(self):
        self.page.evaluate(
            """() => {
                window.gumliFamilyBridge.forward = (message, worker) => {
                    const action = message.payload?.action;
                    const response = {
                        ok: true,
                        data: action === 'bootstrap'
                            ? {
                                tasks: [],
                                members: [{name: 'Nicklas', active: true, sort_order: 1}],
                                favorites: [],
                                invalidRows: []
                            }
                            : {member: 'Nicklas'},
                        error: null,
                        server_time: '2026-07-22T12:00:00+00:00',
                        api_version: 'family-test'
                    };
                    const delay = action === 'ping' ? 1_200 : 0;
                    setTimeout(() => worker.postMessage({
                        type: 'gumli-family-response',
                        requestId: message.requestId,
                        response
                    }), delay);
                };
            }"""
        )

        self.set_mode("Familj")
        self.page.get_by_role("textbox", name="Enhetsnyckel").fill("n" * 48)
        self.page.get_by_role("button", name="Anslut den här enheten", exact=True).click()
        self.page.get_by_role("button", name="Privat", exact=True).click()
        private_empty = self.page.get_by_text(
            "Allt klart på den privata listan!", exact=True
        )
        private_empty.wait_for(state="visible", timeout=10_000)

        self.page.wait_for_timeout(1_500)

        self.assertTrue(private_empty.is_visible())
        self.assertEqual(
            self.page.get_by_text("Familjeuppgifter", exact=True).count(),
            0,
        )

    def test_all_pages_remain_reachable_after_successful_family_response(self):
        overdue_deadline = (date.today() - timedelta(days=2)).isoformat()
        self.page.evaluate(
            """() => {
                window.gumliFamilyBridge.forward = (message, worker) => {
                    const action = message.payload?.action;
                    const isBootstrap = action === 'bootstrap';
                    const isTaskPage = action === 'listLater' || action === 'listHistory';
                    worker.postMessage({
                        type: 'gumli-family-response',
                        requestId: message.requestId,
                        response: {
                            ok: true,
                            data: isTaskPage
                                ? {tasks: [], invalidRows: []}
                                : isBootstrap
                                ? {
                                    tasks: [
                                        {
                                            id: 'family-overdue', title: 'Försenad familjeuppgift',
                                            status: 'Aktuell', assignee: 'Nicklas',
                                            assigned_by: 'Nicklas', assigned_at: '2026-07-20T08:00:00+00:00',
                                            created_by: 'Nicklas', created_at: '2026-07-20T08:00:00+00:00',
                                            deadline: '__OVERDUE_DEADLINE__', updated_by: 'Nicklas',
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
            }""".replace("__OVERDUE_DEADLINE__", overdue_deadline)
        )

        self.set_mode("Familj")
        self.page.get_by_role("textbox", name="Enhetsnyckel").fill("n" * 48)
        self.page.get_by_role("button", name="Anslut den här enheten", exact=True).click()
        self.page.get_by_text("Ansluten som Nicklas", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        overdue_task = self.page.get_by_role(
            "button", name="Redigera Försenad familjeuppgift", exact=False
        )
        overdue_task.wait_for(state="visible", timeout=10_000)
        self.assertIn("Försenad 2 dagar", overdue_task.inner_text())
        self.assertTrue(self.page.get_by_role("button", name="Alla (2)", exact=True).is_visible())
        self.assertTrue(self.page.get_by_role("button", name="Mina (1)", exact=True).is_visible())
        self.page.get_by_role("button", name="Mina (1)", exact=True).click()
        self.page.get_by_role(
            "button", name="Redigera Gemensam familjeuppgift", exact=False
        ).wait_for(state="hidden")

        self.select_tab("Snabblistan")
        self.page.get_by_text("Familj – Snabblistan", exact=True).wait_for(state="visible")
        self.select_tab("Historik")
        self.page.get_by_text("Familj – Historik", exact=True).wait_for(state="visible")
        self.select_tab("Senare")
        self.page.get_by_text("Familj – Senare", exact=True).wait_for(state="visible")
        self.select_tab("Checklista")

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

    def test_family_assignee_can_be_set_on_create_and_changed_afterwards(self):
        self.install_family_task_bridge()
        self.connect_family_task_bridge()

        self.page.get_by_role("button", name="Ny familjeuppgift", exact=True).click()
        self.page.get_by_role("textbox", name="Uppgift").fill("GUI-ansvarig")
        self.page.get_by_role("radio", name="Ida", exact=True).click()
        self.page.get_by_role("button", name="Skapa uppgift", exact=True).click()
        self.page.get_by_text("Uppgiften skapad", exact=True).wait_for(
            state="visible", timeout=10_000
        )

        task = self.page.get_by_role(
            "button", name="Redigera GUI-ansvarig", exact=False
        )
        task.wait_for(state="visible", timeout=10_000)
        self.assertIn("Ansvarig: Ida", task.inner_text())

        task.click()
        self.page.get_by_text("Redigera familjeuppgift", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.assertTrue(
            self.page.get_by_role("radio", name="Ida", exact=True).is_checked()
        )
        self.page.get_by_role("radio", name="Thor", exact=True).click()
        self.page.get_by_role("button", name="Spara ändringar", exact=True).click()
        self.page.get_by_text("Ändringar sparade", exact=True).wait_for(
            state="visible", timeout=10_000
        )

        updated_task = self.page.get_by_role(
            "button", name="Redigera GUI-ansvarig", exact=False
        )
        updated_task.wait_for(state="visible", timeout=10_000)
        self.assertIn("Ansvarig: Thor", updated_task.inner_text())
        self.assertNotIn("Ansvarig: Ida", updated_task.inner_text())

    def test_family_deadline_stays_visible_when_mobile_keyboard_opens(self):
        self.install_family_polish_bridge()
        self.connect_family_polish_bridge()

        self.page.get_by_role(
            "button", name="Redigera Pilotuppgift 1", exact=False
        ).click()
        deadline = self.page.get_by_role("textbox", name="Deadline (valfritt)")
        deadline.wait_for(state="visible", timeout=10_000)
        deadline.click()

        # A real Android keyboard shrinks both viewports because index.html opts
        # into interactive-widget=resizes-content. Reproduce that smaller app
        # area here and verify Flutter keeps the focused field above it.
        self.page.set_viewport_size({"width": 410, "height": 480})
        self.page.wait_for_timeout(500)

        viewport_content = self.page.locator('meta[name="viewport"]').get_attribute(
            "content"
        )
        self.assertIn("interactive-widget=resizes-content", viewport_content)
        field_box = deadline.bounding_box()
        self.assertIsNotNone(field_box)
        self.assertGreaterEqual(field_box["y"], 0)
        self.assertLessEqual(
            field_box["y"] + field_box["height"],
            self.page.evaluate("window.innerHeight"),
        )

    def test_family_task_can_be_created_and_edited(self):
        self.install_family_task_bridge()
        self.connect_family_task_bridge()

        self.page.get_by_role("button", name="Ny familjeuppgift", exact=True).click()
        self.page.get_by_role("textbox", name="Uppgift", exact=False).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role("textbox", name="Uppgift").fill("GUI-familjeuppgift")
        self.page.get_by_role("textbox", name="Deadline (valfritt)").fill("2026-07-28")
        self.page.wait_for_timeout(300)
        self.page.get_by_role("button", name="Skapa uppgift", exact=True).click()
        self.page.get_by_text("Uppgiften skapad", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        created_task = self.page.get_by_role(
            "button", name="Redigera GUI-familjeuppgift", exact=False
        )
        created_task.wait_for(
            state="visible", timeout=10_000
        )
        created_task.click()
        self.page.get_by_text("Redigera familjeuppgift", exact=True).wait_for(state="visible")
        self.assertTrue(self.page.get_by_text("Skapad av Nicklas", exact=False).is_visible())
        self.assertTrue(self.page.get_by_text("Senast ändrad av Nicklas", exact=False).is_visible())
        title_field = self.page.get_by_role("textbox", name="Uppgift")
        title_field.fill("Redigerad GUI-uppgift")
        self.page.wait_for_timeout(300)
        self.page.get_by_role("button", name="Spara ändringar", exact=True).click()
        self.page.get_by_text("Ändringar sparade", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role(
            "button", name="Redigera Redigerad GUI-uppgift", exact=False
        ).wait_for(
            state="visible", timeout=10_000,
        )
        self.assertEqual(
            self.page.get_by_role(
                "button", name="Redigera GUI-familjeuppgift", exact=False
            ).count(),
            0,
        )

        edited_task = self.page.get_by_role(
            "button", name="Redigera Redigerad GUI-uppgift", exact=False
        )
        edited_task.click()
        self.page.get_by_role("button", name="Flytta till Senare", exact=True).click()
        self.page.get_by_text("Uppgiften flyttad", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.select_tab("Senare")
        later_task = self.page.get_by_role(
            "button", name="Redigera Redigerad GUI-uppgift", exact=False
        )
        later_task.wait_for(state="visible", timeout=10_000)
        later_task.click()
        self.page.get_by_role("button", name="Radera", exact=True).click()
        self.page.get_by_text("Radera familjeuppgift", exact=True).wait_for(state="visible")
        self.page.wait_for_timeout(300)
        self.page.get_by_role("button", name="Radera uppgift", exact=True).click()
        self.page.get_by_text("Uppgiften raderad", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Inga familjeuppgifter i Senare", exact=True).wait_for(
            state="visible", timeout=10_000
        )

        self.select_tab("Checklista")
        self.page.get_by_text("Familjeuppgifter", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Synkad nyss", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="Ny familjeuppgift", exact=True).click()
        self.page.get_by_role("textbox", name="Uppgift", exact=False).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role("textbox", name="Uppgift").fill("GUI-slutförande")
        self.page.wait_for_timeout(300)
        self.page.get_by_role("button", name="Skapa uppgift", exact=True).click()
        self.page.get_by_text("Uppgiften skapad", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role(
            "button", name="Markera GUI-slutförande som klar", exact=True
        ).click()
        self.page.get_by_text("Uppgiften slutförd", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Inga familjeuppgifter i Aktuell", exact=True).wait_for(
            state="visible", timeout=10_000
        )

        self.select_tab("Historik")
        self.page.get_by_text("GUI-slutförande", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_text("Slutförd av Nicklas", exact=False).wait_for(
            state="visible", timeout=10_000
        )
        self.assertEqual(
            self.page.get_by_role(
                "button", name="Markera GUI-slutförande som klar", exact=True
            ).count(),
            0,
        )

        self.select_tab("Snabblistan")
        self.page.get_by_text("Familj – Snabblistan", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role(
            "button", name="Lägg till Töm soporna för Alla", exact=True
        ).click()
        self.page.get_by_text("Tillagd för Alla", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role("button", name="Redigera", exact=True).click()
        self.page.get_by_text("Redigera familjeuppgift", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.assertEqual(
            self.page.get_by_role("textbox", name="Uppgift").input_value(),
            "Töm soporna",
        )
        self.assertEqual(
            self.page.get_by_role("textbox", name="Deadline (valfritt)").input_value(),
            "",
        )
        self.page.get_by_role("button", name="Avbryt", exact=True).click()

    def test_boot_has_no_console_errors(self):
        self.assert_no_unexpected_console_errors()

    def test_family_offline_cache_is_read_only_and_retry_recovers(self):
        self.install_family_polish_bridge(task_count=1)
        self.connect_family_polish_bridge()
        self.page.get_by_role(
            "button", name="Redigera Pilotuppgift 1", exact=False
        ).wait_for(state="visible", timeout=10_000)

        self.page.evaluate("window.__gumliFamilyOffline = true")
        self.set_mode("Privat")
        self.set_mode("Familj")
        self.page.get_by_text("Offline – visar sparad data", exact=True).wait_for(
            state="visible", timeout=10_000
        )

        self.page.get_by_role("button", name="Ny familjeuppgift", exact=True).click()
        self.page.wait_for_timeout(300)
        self.assertEqual(self.page.get_by_role("textbox", name="Uppgift").count(), 0)
        self.assertEqual(
            self.page.get_by_role(
                "button", name="Markera Pilotuppgift 1 som klar", exact=True
            ).count(),
            0,
        )
        self.assertEqual(
            self.page.get_by_role(
                "button", name="Redigera Pilotuppgift 1", exact=False
            ).count(),
            0,
        )

        self.page.evaluate("window.__gumliFamilyOffline = false")
        self.page.get_by_role("button", name="Försök igen", exact=True).click()
        self.page.get_by_text("Synkad nyss", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="Ny familjeuppgift", exact=True).click()
        self.page.get_by_role("textbox", name="Uppgift", exact=False).wait_for(
            state="visible", timeout=10_000
        )
        self.page.get_by_role("button", name="Avbryt", exact=True).click()

    def test_family_fifty_tasks_fit_mobile_target_widths(self):
        self.install_family_polish_bridge(task_count=50)
        self.connect_family_polish_bridge()
        self.assertEqual(
            self.page.get_by_role("button", name="Markera", exact=False).count(),
            50,
        )

        for width in (320, 390, 412):
            with self.subTest(width=width):
                self.page.set_viewport_size({"width": width, "height": 820})
                self.page.wait_for_timeout(150)
                overflow = self.page.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                self.assertFalse(overflow)
                self.assertTrue(
                    self.page.get_by_role("tab", name="Senare", exact=True).is_visible()
                )
                self.assertTrue(
                    self.page.get_by_role(
                        "button", name="Ny familjeuppgift", exact=True
                    ).is_visible()
                )
