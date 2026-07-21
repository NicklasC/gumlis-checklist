import unittest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.models.family import (
    FamilyBootstrap,
    FamilyMember,
    FamilyTask,
    FamilyTaskDraft,
    FamilyTaskStatus,
)
from src.repositories.family_repository import FamilyVersionConflict
from src.views.family_current_view import FamilyCurrentView, FamilyTaskRow, family_deadline_text


def make_task(
    task_id,
    title,
    assignee="Alla",
    deadline=None,
    created_at=None,
    assigned_by="Nicklas",
    created_by="Nicklas",
    updated_by="Nicklas",
    version=1,
):
    timestamp = created_at or datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
    return FamilyTask(
        id=task_id,
        title=title,
        status=FamilyTaskStatus.CURRENT,
        assignee=assignee,
        assigned_by=assigned_by,
        assigned_at=timestamp,
        created_by=created_by,
        created_at=timestamp,
        deadline=deadline,
        updated_by=updated_by,
        updated_at=timestamp,
        version=version,
    )


class FamilyCurrentViewTests(unittest.TestCase):
    def make_bootstrap(self):
        return FamilyBootstrap(
            tasks=[
                make_task("late", "Försenad", assignee="Nicklas", deadline=date(2026, 7, 18)),
                make_task("mine", "Min uppgift", assignee="Nicklas", deadline=date(2026, 7, 25)),
                make_task("all", "Alla-uppgift"),
            ],
            members=[FamilyMember(name="Nicklas", active=True, sort_order=1)],
            favorites=[],
            server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )

    def test_deadline_text_marks_overdue_in_red_state(self):
        text, overdue = family_deadline_text(
            make_task("late", "Försenad", deadline=date(2026, 7, 18)),
            today=date(2026, 7, 20),
        )
        self.assertEqual(text, "Försenad 2 dagar")
        self.assertTrue(overdue)

    def test_row_exposes_assignee_and_overdue_deadline(self):
        row = FamilyTaskRow(
            make_task("late", "Försenad", assignee="Ida", deadline=date(2026, 7, 18)),
            today=date(2026, 7, 20),
        )
        self.assertEqual(row.assignee_text.value, "Ansvarig: Ida")
        self.assertEqual(row.deadline_text.value, "Försenad 2 dagar")
        self.assertEqual(row.deadline_text.color, "#F87171")

    def test_row_shows_who_reassigned_current_assignee(self):
        row = FamilyTaskRow(
            make_task(
                "reassigned",
                "Töm soporna",
                assignee="Thor",
                assigned_by="Ida",
                created_by="Nicklas",
            )
        )
        self.assertTrue(row.assigned_by_text.visible)
        self.assertEqual(row.assigned_by_text.value, "Tilldelad av Ida")

    def test_all_and_mine_filters_sort_and_count_tasks(self):
        view = FamilyCurrentView(repository=None, member="Nicklas")
        view._set_bootstrap(self.make_bootstrap())

        self.assertEqual([task.id for task in view._visible_tasks()], ["late", "mine", "all"])
        self.assertEqual(view.filter_row.controls[0].content.value, "Alla (3)")
        self.assertEqual(view.filter_row.controls[1].content.value, "Mina (2)")

        view.selected_filter = "Mina"
        self.assertEqual([task.id for task in view._visible_tasks()], ["late", "mine"])

    def test_empty_mine_filter_has_clear_message(self):
        view = FamilyCurrentView(repository=None, member="Ida")
        view._set_bootstrap(self.make_bootstrap())
        view.selected_filter = "Mina"
        view._render_tasks()
        self.assertEqual(view.list_container.controls[0].value, "Du har inga tilldelade familjeuppgifter")


class FamilyCurrentMutationTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self, repository=None):
        repository = repository or MagicMock()
        repository.cache_bootstrap = AsyncMock()
        view = FamilyCurrentView(repository=repository, member="Nicklas")
        view._set_bootstrap(
            FamilyBootstrap(
                tasks=[],
                members=[FamilyMember(name="Nicklas", active=True, sort_order=1)],
                favorites=[],
                server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
            )
        )
        return view, repository

    async def test_create_editor_adds_returned_task_and_updates_cache(self):
        view, repository = self.make_view()
        created = make_task("created", "Töm soporna", assignee="Ida")
        repository.create_task = AsyncMock(return_value=created)

        await view._save_editor(
            None,
            FamilyTaskDraft(title="Töm soporna", assignee="Ida"),
            view.editor,
        )

        repository.create_task.assert_awaited_once()
        self.assertEqual(
            repository.create_task.await_args.kwargs["task_id"],
            view.editor.pending_create_id,
        )
        repository.cache_bootstrap.assert_awaited_once()
        self.assertEqual([task.id for task in view.bootstrap.tasks], ["created"])
        self.assertEqual(view.status_text.value, "Uppgiften skapad")

    async def test_create_retry_reuses_same_client_task_id(self):
        view, repository = self.make_view()
        created = make_task("created", "Töm soporna")
        repository.create_task = AsyncMock(
            side_effect=[TimeoutError("Försök igen"), created]
        )
        view.editor.prepare()
        stable_id = view.editor.pending_create_id
        draft = FamilyTaskDraft(title="Töm soporna")

        await view._save_editor(None, draft, view.editor)
        await view._save_editor(None, draft, view.editor)

        self.assertEqual(repository.create_task.await_count, 2)
        self.assertEqual(
            [call.kwargs["task_id"] for call in repository.create_task.await_args_list],
            [stable_id, stable_id],
        )
        self.assertEqual([task.id for task in view.bootstrap.tasks], ["created"])

    async def test_update_conflict_loads_latest_task_without_overwriting(self):
        original = make_task("task", "Min redigering")
        latest = make_task("task", "Idas ändring", updated_by="Ida", version=2)
        view, repository = self.make_view()
        view._upsert_task(original)
        repository.update_task = AsyncMock(side_effect=FamilyVersionConflict(latest))

        await view._save_editor(
            original,
            FamilyTaskDraft(title="Min redigering"),
            view.editor,
        )

        self.assertEqual(view.bootstrap.tasks[0].title, "Idas ändring")
        self.assertIs(view.editor.task, latest)
        self.assertIn("ändrades av Ida", view.editor.error_text.value)
