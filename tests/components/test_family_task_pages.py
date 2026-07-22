import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.models.family import (
    FamilyFavorite,
    FamilyTask,
    FamilyTaskDraft,
    FamilyTaskPage,
    FamilyTaskStatus,
)
from src.views.family_favorites_view import FamilyFavoritesView
from src.views.family_task_page import FamilyHistoryView, FamilyLaterView


class FamilyTaskPageTests(unittest.IsolatedAsyncioTestCase):
    def page(self, title="Familj – Senare"):
        repository = MagicMock()
        repository.list_later = AsyncMock(
            return_value=FamilyTaskPage(
                tasks=[],
                invalid_rows=[],
                server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
            )
        )
        repository.list_history = AsyncMock(
            return_value=FamilyTaskPage(
                tasks=[],
                invalid_rows=[],
                server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
            )
        )
        return (
            FamilyLaterView(repository, "Nicklas")
            if "Senare" in title
            else FamilyHistoryView(repository, "Nicklas")
        ), repository

    async def test_later_page_loads_separate_endpoint(self):
        view, repository = self.page()
        await view._sync()
        repository.list_later.assert_awaited_once()
        self.assertEqual(view.list_container.controls[0].value, "Inga familjeuppgifter i Senare")

    async def test_history_page_has_no_restore_action(self):
        view, repository = self.page("Familj – Historik")
        await view._sync()
        repository.list_history.assert_awaited_once()
        self.assertEqual(view.list_container.controls[0].value, "Ingen familjehistorik de senaste 14 dagarna")

    async def test_favorites_page_renders_bootstrap_favorites(self):
        provider = SimpleNamespace(
            bootstrap=SimpleNamespace(
                favorites=[FamilyFavorite(id="f1", title="Töm soporna", active=True, sort_order=1)]
            ),
            _set_bootstrap=MagicMock(),
        )
        view = FamilyFavoritesView(MagicMock(), "Nicklas", provider)
        await view._sync()
        self.assertEqual(len(view.list_container.controls), 1)
        self.assertIn("Töm soporna", view.list_container.controls[0].content.controls[0].value)

    async def test_later_page_edits_active_task_in_place(self):
        view, repository = self.page()
        task = FamilyTask.model_validate(
            {
                "id": "later-1",
                "title": "Gammal titel",
                "status": "Senare",
                "assignee": "Alla",
                "assigned_by": "Nicklas",
                "assigned_at": "2026-07-20T10:00:00+00:00",
                "created_by": "Nicklas",
                "created_at": "2026-07-20T10:00:00+00:00",
                "deadline": None,
                "updated_by": "Nicklas",
                "updated_at": "2026-07-20T10:00:00+00:00",
                "completed_by": None,
                "completed_at": None,
                "version": 1,
            }
        )
        updated = task.model_copy(update={"title": "Ny titel", "version": 2})
        view.task_page = FamilyTaskPage(
            tasks=[task],
            invalid_rows=[],
            server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )
        repository.update_task = AsyncMock(return_value=updated)

        await view._save_editor(
            task,
            FamilyTaskDraft(title="Ny titel"),
            view.editor,
        )

        self.assertEqual(view.task_page.tasks[0].title, "Ny titel")
        self.assertEqual(view.status_text.value, "Ändringar sparade")

    async def test_later_page_completion_removes_task(self):
        view, repository = self.page()
        task = FamilyTask.model_validate(
            {
                "id": "later-1",
                "title": "Töm soporna",
                "status": "Senare",
                "assignee": "Alla",
                "assigned_by": "Nicklas",
                "assigned_at": "2026-07-20T10:00:00+00:00",
                "created_by": "Nicklas",
                "created_at": "2026-07-20T10:00:00+00:00",
                "deadline": None,
                "updated_by": "Nicklas",
                "updated_at": "2026-07-20T10:00:00+00:00",
                "completed_by": None,
                "completed_at": None,
                "version": 1,
            }
        )
        completed = task.model_copy(
            update={
                "status": FamilyTaskStatus.COMPLETED,
                "completed_by": "Nicklas",
                "completed_at": datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
                "version": 2,
            }
        )
        view.task_page = FamilyTaskPage(
            tasks=[task],
            invalid_rows=[],
            server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )
        repository.complete_task = AsyncMock(return_value=completed)

        await view._complete_task(task)

        repository.complete_task.assert_awaited_once_with(task)
        self.assertEqual(view.task_page.tasks, [])
        self.assertEqual(view.status_text.value, "Uppgiften slutförd")

    async def test_history_sorts_newest_first_and_shows_completion_audit(self):
        view, _ = self.page("Familj – Historik")

        def completed(task_id, completed_at, completed_by):
            return FamilyTask.model_validate(
                {
                    "id": task_id,
                    "title": task_id,
                    "status": "Klar",
                    "assignee": "Alla",
                    "assigned_by": "Nicklas",
                    "assigned_at": "2026-07-20T10:00:00+00:00",
                    "created_by": "Nicklas",
                    "created_at": "2026-07-20T10:00:00+00:00",
                    "deadline": None,
                    "updated_by": completed_by,
                    "updated_at": completed_at,
                    "completed_by": completed_by,
                    "completed_at": completed_at,
                    "version": 2,
                }
            )

        older = completed("Äldre", "2026-07-20T11:00:00+00:00", "Ida")
        newer = completed("Nyare", "2026-07-20T12:00:00+00:00", "Thor")
        view.task_page = FamilyTaskPage(
            tasks=[older, newer],
            invalid_rows=[],
            server_time=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual([task.id for task in view._visible_tasks()], ["Nyare", "Äldre"])
        view._render_tasks()
        self.assertIn("Slutförd av Thor", view.list_container.controls[0].completion_text.value)
        self.assertIsNone(view.editor)
