import unittest
from datetime import date, datetime, timezone

from src.models.family import FamilyBootstrap, FamilyMember, FamilyTask, FamilyTaskStatus
from src.views.family_current_view import FamilyCurrentView, FamilyTaskRow, family_deadline_text


def make_task(task_id, title, assignee="Alla", deadline=None, created_at=None):
    timestamp = created_at or datetime(2026, 7, 20, 8, 0, tzinfo=timezone.utc)
    return FamilyTask(
        id=task_id,
        title=title,
        status=FamilyTaskStatus.CURRENT,
        assignee=assignee,
        assigned_by="Nicklas",
        assigned_at=timestamp,
        created_by="Nicklas",
        created_at=timestamp,
        deadline=deadline,
        updated_by="Nicklas",
        updated_at=timestamp,
        version=1,
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
