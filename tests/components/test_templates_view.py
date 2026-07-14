import unittest
from unittest.mock import MagicMock

import flet as ft

from src.views.templates_view import TemplatesView
from tests.support.fixtures import PRIVATE, WORK, InMemoryRepository, StubMainView


class TemplatesViewTests(unittest.TestCase):
    def make_view(self, mode=PRIVATE):
        repo = InMemoryRepository()
        callback = MagicMock()
        view = TemplatesView(repo, callback, StubMainView(mode))
        return view, repo, callback

    def active_title(self, view):
        card_content = view.cards_container.controls[0].content
        return card_content.controls[0].controls[0].value

    def test_private_mode_shows_private_group(self):
        view, *_ = self.make_view(PRIVATE)
        self.assertEqual(self.active_title(view), "Privat favoriter")

    def test_work_mode_shows_work_group(self):
        view, *_ = self.make_view(WORK)
        self.assertEqual(self.active_title(view), "Jobb favoriter")

    def test_adds_trimmed_favorite(self):
        view, repo, _ = self.make_view()
        field = ft.TextField(value="  Ny favorit  ")
        view._add_item_to_group(field, repo.groups["todo_favorites"])
        self.assertIn("Ny favorit", repo.groups["todo_favorites"].items)

    def test_blank_favorite_is_ignored(self):
        view, repo, _ = self.make_view()
        before = list(repo.groups["todo_favorites"].items)
        view._add_item_to_group(ft.TextField(value="  "), repo.groups["todo_favorites"])
        self.assertEqual(repo.groups["todo_favorites"].items, before)

    def test_duplicate_favorite_is_ignored(self):
        view, repo, _ = self.make_view()
        group = repo.groups["todo_favorites"]
        view._add_item_to_group(ft.TextField(value=group.items[0]), group)
        self.assertEqual(group.items.count(group.items[0]), 1)

    def test_add_clears_input(self):
        view, repo, _ = self.make_view()
        field = ft.TextField(value="Ny")
        view._add_item_to_group(field, repo.groups["todo_favorites"])
        self.assertEqual(field.value, "")

    def test_remove_deletes_selected_favorite(self):
        view, repo, _ = self.make_view()
        group = repo.groups["todo_favorites"]
        title = group.items[0]
        view._remove_item_from_group(title, group)
        self.assertNotIn(title, group.items)

    def test_tap_calls_callback_with_active_mode(self):
        view, _, callback = self.make_view(WORK)
        view._handle_item_tap("Kolla e-post", "Jobb")
        callback.assert_called_once_with("Kolla e-post", WORK)

    def test_empty_repository_shows_empty_state(self):
        repo = InMemoryRepository()
        repo.groups.clear()
        view = TemplatesView(repo, MagicMock(), StubMainView())
        self.assertIn("Inga favoritgrupper", view.cards_container.controls[0].content.value)
