import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.models.family import FamilyTask, FamilyTaskStatus
from src.views.family_task_editor import FamilyTaskEditor


class FamilyTaskEditorTests(unittest.IsolatedAsyncioTestCase):
    def test_create_form_defaults_to_all_and_uses_clear_labels(self):
        editor = FamilyTaskEditor(AsyncMock())
        editor.prepare()

        self.assertEqual(editor.heading.value, "Ny familjeuppgift")
        self.assertEqual(editor.title_field.label, "Uppgift")
        self.assertEqual(editor.assignee_label.value, "Ansvarig")
        self.assertEqual(editor.assignee_field.value, "Alla")
        self.assertEqual(editor.save_button.content.value, "Skapa uppgift")

    def test_assignee_selector_exposes_all_household_choices(self):
        editor = FamilyTaskEditor(AsyncMock())

        choices = [
            (control.value, control.label, control.col)
            for control in editor.assignee_field.content.controls
        ]

        self.assertEqual(
            choices,
            [
                ("Alla", "Alla", 6),
                ("Nicklas", "Nicklas", 6),
                ("Ida", "Ida", 6),
                ("Thor", "Thor", 6),
                ("Johanna", "Johanna", 6),
            ],
        )

    def test_deadline_is_placed_before_the_compact_assignee_grid(self):
        editor = FamilyTaskEditor(AsyncMock())

        self.assertEqual(
            editor.content.controls[:3],
            [editor.title_field, editor.deadline_row, editor.assignee_selector],
        )
        self.assertEqual(editor.assignee_field.content.columns, 12)

    def test_assignee_change_is_kept_in_submitted_draft(self):
        editor = FamilyTaskEditor(AsyncMock())
        editor.prepare()
        editor.title_field.value = "Töm soporna"

        editor._assignee_changed(SimpleNamespace(data="Ida"))

        self.assertEqual(editor.assignee_field.value, "Ida")
        self.assertEqual(editor.draft().assignee, "Ida")

    def test_draft_parses_deadline_and_clear_action_removes_it(self):
        editor = FamilyTaskEditor(AsyncMock())
        editor.prepare()
        editor.title_field.value = "Töm soporna"
        editor.assignee_field.value = "Ida"
        editor.deadline_field.value = "2026-07-28"

        draft = editor.draft()

        self.assertEqual(draft.deadline, date(2026, 7, 28))
        editor._clear_deadline()
        self.assertEqual(editor.deadline_field.value, "")

    def test_edit_form_shows_assignment_and_latest_editor(self):
        timestamp = datetime(2026, 7, 21, 8, 15, tzinfo=timezone.utc)
        task = FamilyTask(
            id="family-1",
            title="Töm soporna",
            status=FamilyTaskStatus.CURRENT,
            assignee="Thor",
            assigned_by="Ida",
            assigned_at=timestamp,
            created_by="Nicklas",
            created_at=timestamp,
            deadline=None,
            updated_by="Ida",
            updated_at=timestamp,
            version=2,
        )
        editor = FamilyTaskEditor(AsyncMock())

        editor.prepare(task)

        self.assertTrue(editor.audit_text.visible)
        self.assertIn("Skapad av Nicklas", editor.audit_text.value)
        self.assertIn("Tilldelad av Ida", editor.audit_text.value)
        self.assertIn("Senast ändrad av Ida", editor.audit_text.value)

    async def test_edit_actions_move_current_task_to_later(self):
        callback = AsyncMock()
        timestamp = datetime(2026, 7, 21, 8, 15, tzinfo=timezone.utc)
        task = FamilyTask(
            id="family-1",
            title="Töm soporna",
            status=FamilyTaskStatus.CURRENT,
            assigned_by="Nicklas",
            assigned_at=timestamp,
            created_by="Nicklas",
            created_at=timestamp,
            updated_by="Nicklas",
            updated_at=timestamp,
            version=1,
        )
        editor = FamilyTaskEditor(AsyncMock(), callback)
        editor.prepare(task)

        await editor._move()

        self.assertTrue(editor.move_button.visible)
        self.assertTrue(editor.delete_button.visible)
        callback.assert_awaited_once_with(task, FamilyTaskStatus.LATER, editor)

    async def test_invalid_deadline_blocks_submit_with_swedish_message(self):
        callback = AsyncMock()
        editor = FamilyTaskEditor(callback)
        editor.prepare()
        editor.title_field.value = "Töm soporna"
        editor.deadline_field.value = "28/7"

        await editor._submit()

        callback.assert_not_awaited()
        self.assertTrue(editor.error_text.visible)
        self.assertEqual(editor.error_text.value, "Deadline ska anges som ÅÅÅÅ-MM-DD")

    def test_offline_lock_blocks_mutations_but_keeps_cancel_available(self):
        editor = FamilyTaskEditor(AsyncMock())
        editor.prepare()

        editor.set_available(False)

        self.assertTrue(editor.save_button.disabled)
        self.assertTrue(editor.move_button.disabled)
        self.assertTrue(editor.delete_button.disabled)
        self.assertFalse(editor.cancel_button.disabled)
