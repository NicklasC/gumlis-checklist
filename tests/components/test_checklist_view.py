import unittest
from datetime import date, timedelta
from unittest.mock import patch

from src.models.checklist import Checklist
from src.views.checklist_view import ChecklistView
from tests.support.fixtures import PRIVATE, WORK, InMemoryRepository, StubMainView, item


class ChecklistViewTests(unittest.TestCase):
    def make_view(self, mode=PRIVATE, items=None):
        repo = InMemoryRepository()
        active = repo.get_checklist("active_list")
        active.last_cleaned_date = date.today().isoformat()
        active.items = items or []
        view = ChecklistView(repo, StubMainView(mode))
        return view, repo

    def test_creates_private_item(self):
        view, _ = self.make_view()
        view._add_new_item("Privat", PRIVATE)
        self.assertEqual(view.active_list.items[0].category, PRIVATE)

    def test_creates_work_item(self):
        view, _ = self.make_view()
        view._add_new_item("Jobb", WORK)
        self.assertEqual(view.active_list.items[0].category, WORK)

    def test_generated_item_id_has_prefix(self):
        view, _ = self.make_view()
        view._add_new_item("Test", PRIVATE)
        self.assertTrue(view.active_list.items[0].id.startswith("item_"))

    def test_routes_later_item_to_later_list(self):
        view, repo = self.make_view()
        view._add_new_item("Senare", "Senare")
        self.assertEqual(repo.get_checklist("later_list").items[0].title, "Senare")

    def test_later_item_keeps_active_mode(self):
        view, repo = self.make_view(WORK)
        view._add_new_item("Senare", "Senare")
        self.assertEqual(repo.get_checklist("later_list").items[0].category, WORK)

    def test_favorite_adds_item(self):
        view, _ = self.make_view()
        view._add_favorite_item("Vattna", PRIVATE)
        self.assertEqual(view.active_list.items[0].title, "Vattna")

    def test_duplicate_active_favorite_is_ignored(self):
        existing = item("one", "Vattna")
        view, _ = self.make_view(items=[existing])
        view._add_favorite_item("Vattna", PRIVATE)
        self.assertEqual(len(view.active_list.items), 1)

    def test_checked_favorite_can_be_added_again(self):
        existing = item("one", "Vattna", checked=True)
        view, _ = self.make_view(items=[existing])
        view._add_favorite_item("Vattna", PRIVATE)
        self.assertEqual(len(view.active_list.items), 2)

    def test_delete_removes_only_selected_item(self):
        first = item("one", "One")
        second = item("two", "Two")
        view, _ = self.make_view(items=[first, second])
        view._handle_item_delete(first)
        self.assertEqual([entry.id for entry in view.active_list.items], ["two"])

    def test_move_to_later_removes_active_item(self):
        value = item("one", "One")
        view, _ = self.make_view(items=[value])
        view._handle_item_move_to_later(value)
        self.assertEqual(view.active_list.items, [])

    def test_move_to_later_adds_backlog_item(self):
        value = item("one", "One", category=WORK)
        view, repo = self.make_view(items=[value])
        view._handle_item_move_to_later(value)
        self.assertEqual(repo.get_checklist("later_list").items[0].category, WORK)

    def test_private_mode_renders_only_private_items(self):
        view, _ = self.make_view(items=[item("p", "Private"), item("w", "Work", category=WORK)])
        self.assertEqual(len(view.list_container.controls), 1)

    def test_work_mode_renders_only_work_items(self):
        view, _ = self.make_view(WORK, [item("p", "Private"), item("w", "Work", category=WORK)])
        self.assertEqual(view.list_container.controls[0].item.title, "Work")

    def test_unchecked_items_render_before_checked_items(self):
        checked = item("checked", "Checked", checked=True)
        unchecked = item("unchecked", "Unchecked")
        view, _ = self.make_view(items=[checked, unchecked])
        self.assertEqual(view.list_container.controls[0].item.id, "unchecked")

    def test_daily_cleanup_moves_checked_item_to_history(self):
        checked = item("checked", "Checked", checked=True)
        view, repo = self.make_view(items=[checked])
        view.active_list.last_cleaned_date = (date.today() - timedelta(days=1)).isoformat()
        view._load_data_and_clean()
        self.assertEqual(repo.get_checklist("history_list").items[0].id, "checked")

    def test_checking_item_records_completion_time(self):
        value = item("checked", "Checked")
        view, _ = self.make_view(items=[value])
        value.is_checked = True
        with patch(
            "src.views.checklist_view.now_local_iso",
            return_value="2026-07-19T21:15:00+02:00",
        ):
            view._handle_item_check(value)
        self.assertEqual(value.completed_at, "2026-07-19T21:15:00+02:00")

    def test_unchecking_item_clears_completion_time(self):
        value = item(
            "checked",
            "Checked",
            checked=True,
            completed_at="2026-07-19T21:15:00+02:00",
        )
        view, _ = self.make_view(items=[value])
        value.is_checked = False
        view._handle_item_check(value)
        self.assertIsNone(value.completed_at)

    def test_daily_cleanup_preserves_creation_and_completion_times(self):
        value = item(
            "checked",
            "Checked",
            checked=True,
            age_days=5,
            completed_at="2026-07-19T21:15:00+02:00",
        )
        original_creation = value.created_at
        view, repo = self.make_view(items=[value])
        view._perform_daily_cleanup("2026-07-20")
        archived = repo.get_checklist("history_list").items[0]
        self.assertEqual(archived.created_at, original_creation)
        self.assertEqual(archived.completed_at, "2026-07-19T21:15:00+02:00")

    def test_daily_cleanup_keeps_unchecked_item_active(self):
        unchecked = item("open", "Open")
        view, _ = self.make_view(items=[unchecked])
        view._perform_daily_cleanup(date.today().isoformat())
        self.assertEqual(view.active_list.items[0].id, "open")
