import unittest
from unittest.mock import MagicMock

from src.views.later_view import LaterView
from tests.support.fixtures import PRIVATE, WORK, InMemoryRepository, StubMainView, item


class LaterViewTests(unittest.TestCase):
    def make_view(self, mode=PRIVATE, items=None):
        repo = InMemoryRepository()
        repo.get_checklist("later_list").items = items or []
        callback = MagicMock()
        view = LaterView(repo, callback, StubMainView(mode))
        view.text_field.update = MagicMock()
        view.text_field.focus = MagicMock()
        return view, repo, callback

    def test_submit_adds_private_item(self):
        view, *_ = self.make_view()
        view.text_field.value = "Senare"
        view._handle_submit(None)
        self.assertEqual(view.later_list.items[0].category, PRIVATE)

    def test_submit_adds_work_item(self):
        view, *_ = self.make_view(WORK)
        view.text_field.value = "Senare"
        view._handle_submit(None)
        self.assertEqual(view.later_list.items[0].category, WORK)

    def test_submit_trims_title(self):
        view, *_ = self.make_view()
        view.text_field.value = "  Senare  "
        view._handle_submit(None)
        self.assertEqual(view.later_list.items[0].title, "Senare")

    def test_submit_clears_field(self):
        view, *_ = self.make_view()
        view.text_field.value = "Senare"
        view._handle_submit(None)
        self.assertEqual(view.text_field.value, "")

    def test_blank_submit_adds_nothing(self):
        view, *_ = self.make_view()
        view.text_field.value = "   "
        view._handle_submit(None)
        self.assertEqual(view.later_list.items, [])

    def test_delete_removes_selected_item(self):
        value = item("one", "One")
        view, *_ = self.make_view(items=[value])
        view._delete_item(value)
        self.assertEqual(view.later_list.items, [])

    def test_promote_moves_item_to_active_list(self):
        value = item("one", "One", category=WORK)
        view, repo, _ = self.make_view(WORK, [value])
        view._promote_item(value)
        self.assertEqual(repo.get_checklist("active_list").items[0].id, "one")

    def test_promote_preserves_category(self):
        value = item("one", "One", category=WORK)
        view, repo, _ = self.make_view(WORK, [value])
        view._promote_item(value)
        self.assertEqual(repo.get_checklist("active_list").items[0].category, WORK)

    def test_promote_calls_parent_callback(self):
        value = item("one", "One")
        view, _, callback = self.make_view(items=[value])
        view._promote_item(value)
        callback.assert_called_once_with(value)

    def test_private_mode_filters_work_items(self):
        view, *_ = self.make_view(items=[item("w", "Work", category=WORK)])
        self.assertIn("Inga privata", view.list_container.controls[0].content.controls[1].value)

    def test_work_mode_renders_work_item(self):
        view, *_ = self.make_view(WORK, [item("w", "Work", category=WORK)])
        self.assertEqual(len(view.list_container.controls), 1)
