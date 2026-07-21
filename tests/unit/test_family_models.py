import unittest

from pydantic import ValidationError

from src.models.family import (
    FamilyBootstrap,
    FamilyFavorite,
    FamilyMember,
    FamilyTask,
    FamilyTaskDraft,
    FamilyTaskStatus,
)


def task_data(**overrides):
    values = {
        "id": "family-1",
        "title": "Töm soporna",
        "status": "Aktuell",
        "assignee": "Alla",
        "assigned_by": "Nicklas",
        "assigned_at": "2026-07-20T18:00:00+02:00",
        "created_by": "Nicklas",
        "created_at": "2026-07-20T18:00:00+02:00",
        "deadline": "2026-07-27",
        "updated_by": "Nicklas",
        "updated_at": "2026-07-20T18:00:00+02:00",
        "completed_by": None,
        "completed_at": None,
        "version": 1,
    }
    values.update(overrides)
    return values


class FamilyTaskModelTests(unittest.TestCase):
    def test_parses_swedish_sheet_values(self):
        task = FamilyTask.model_validate(task_data())
        self.assertEqual(task.status, FamilyTaskStatus.CURRENT)
        self.assertEqual(task.deadline.isoformat(), "2026-07-27")

    def test_all_is_valid_default_assignee(self):
        self.assertEqual(FamilyTask.model_validate(task_data()).assignee, "Alla")

    def test_rejects_unknown_assignee(self):
        with self.assertRaises(ValidationError):
            FamilyTask.model_validate(task_data(assignee="Någon"))

    def test_completed_task_requires_both_completion_fields(self):
        with self.assertRaises(ValidationError):
            FamilyTask.model_validate(task_data(status="Klar", completed_by="Ida"))

    def test_completed_task_accepts_actual_completer(self):
        task = FamilyTask.model_validate(
            task_data(
                status="Klar",
                completed_by="Ida",
                completed_at="2026-07-20T19:00:00+02:00",
                updated_by="Ida",
            )
        )
        self.assertEqual(task.completed_by, "Ida")

    def test_non_completed_task_rejects_stale_completion_fields(self):
        with self.assertRaises(ValidationError):
            FamilyTask.model_validate(
                task_data(
                    completed_by="Ida",
                    completed_at="2026-07-20T19:00:00+02:00",
                )
            )

    def test_task_draft_normalizes_title_and_validates_assignee(self):
        draft = FamilyTaskDraft(title="  Töm soporna  ", assignee="Ida")
        self.assertEqual(draft.title, "Töm soporna")
        with self.assertRaises(ValidationError):
            FamilyTaskDraft(title="Töm soporna", assignee="Någon")


class FamilyBootstrapModelTests(unittest.TestCase):
    def test_accepts_valid_read_only_bootstrap(self):
        bootstrap = FamilyBootstrap.model_validate(
            {
                "tasks": [task_data()],
                "members": [
                    {"name": "Nicklas", "active": True, "sort_order": 1},
                    {"name": "Ida", "active": True, "sort_order": 2},
                ],
                "favorites": [
                    {"id": "favorite-1", "title": "Töm soporna", "active": True, "sort_order": 1}
                ],
                "invalid_rows": [],
                "server_time": "2026-07-20T19:00:00+02:00",
            }
        )
        self.assertEqual(bootstrap.tasks[0].title, "Töm soporna")
        self.assertIsInstance(bootstrap.members[0], FamilyMember)
        self.assertIsInstance(bootstrap.favorites[0], FamilyFavorite)

    def test_rejects_unknown_member(self):
        with self.assertRaises(ValidationError):
            FamilyMember(name="Någon", active=True, sort_order=1)
