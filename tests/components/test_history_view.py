import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from src.views.history_view import HistoryView
from tests.support.fixtures import PRIVATE, WORK, InMemoryRepository, StubMainView, item


class HistoryViewTests(unittest.TestCase):
    def make_view(self, mode=PRIVATE, items=None):
        repo = InMemoryRepository()
        repo.get_checklist("history_list").items = items or []
        callback = MagicMock()
        view = HistoryView(repo, callback, StubMainView(mode))
        return view, repo, callback

    def test_formats_today(self):
        view, *_ = self.make_view()
        self.assertEqual(view._format_swedish_date(date.today()), "Idag")

    def test_formats_yesterday(self):
        view, *_ = self.make_view()
        self.assertEqual(view._format_swedish_date(date.today() - timedelta(days=1)), "Igår")

    def test_formats_older_date_with_swedish_month(self):
        view, *_ = self.make_view()
        self.assertIn("januari", view._format_swedish_date(date(2025, 1, 3)))

    def test_private_empty_state(self):
        view, *_ = self.make_view()
        self.assertIn("Ingen privat historik", view.history_container.controls[0].content.controls[1].value)

    def test_work_empty_state(self):
        view, *_ = self.make_view(WORK)
        self.assertIn("Ingen jobb-historik", view.history_container.controls[0].content.controls[1].value)

    def test_private_mode_filters_work_history(self):
        view, *_ = self.make_view(items=[item("w", "Work", category=WORK, checked=True)])
        self.assertEqual(len(view.history_container.controls), 1)

    def test_history_creates_date_header_and_card(self):
        view, *_ = self.make_view(items=[item("p", "Private", checked=True)])
        self.assertEqual(len(view.history_container.controls), 2)

    def test_history_groups_by_completion_date_not_creation_date(self):
        value = item(
            "p",
            "Private",
            checked=True,
            completed_at=(date.today() - timedelta(days=1)).isoformat() + "T21:15:00+02:00",
        )
        view, *_ = self.make_view(items=[value])
        self.assertEqual(view.history_container.controls[0].content.value, "IGÅR")

    def test_restore_removes_item_from_history(self):
        value = item("one", "One", checked=True)
        view, _, _ = self.make_view(items=[value])
        view._restore_item(value)
        self.assertEqual(view.history_list.items, [])

    def test_restore_adds_unchecked_item_to_active(self):
        value = item("one", "One", checked=True, category=WORK)
        view, repo, _ = self.make_view(WORK, [value])
        view._restore_item(value)
        restored = repo.get_checklist("active_list").items[0]
        self.assertFalse(restored.is_checked)

    def test_restore_preserves_category(self):
        value = item("one", "One", checked=True, category=WORK)
        view, repo, _ = self.make_view(WORK, [value])
        view._restore_item(value)
        self.assertEqual(repo.get_checklist("active_list").items[0].category, WORK)

    def test_restore_calls_parent_callback(self):
        value = item("one", "One", checked=True)
        view, _, callback = self.make_view(items=[value])
        view._restore_item(value)
        callback.assert_called_once()
