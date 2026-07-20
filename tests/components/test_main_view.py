import unittest
from unittest.mock import MagicMock

from src.views.main_view import FAMILY_MODE, MainView
from tests.support.fixtures import PRIVATE, WORK, InMemoryRepository


class MainViewTests(unittest.TestCase):
    def make_view(self):
        return MainView(InMemoryRepository())

    def test_defaults_to_private_mode(self):
        self.assertEqual(self.make_view().current_mode, PRIVATE)

    def test_defaults_to_checklist_page(self):
        view = self.make_view()
        self.assertIs(view.content_area.content, view.view_checklist)

    def test_mode_change_updates_global_mode(self):
        view = self.make_view()
        view._refresh_active_view = MagicMock()
        view._handle_mode_change(WORK)
        self.assertEqual(view.current_mode, WORK)

    def test_mode_change_refreshes_active_view(self):
        view = self.make_view()
        view._refresh_active_view = MagicMock()
        view._handle_mode_change(WORK)
        view._refresh_active_view.assert_called_once()

    def test_navigation_has_four_destinations(self):
        self.assertEqual(len(self.make_view().nav_bar.destinations), 4)

    def test_navigation_labels_are_stable(self):
        labels = [destination.label for destination in self.make_view().nav_bar.destinations]
        self.assertEqual(labels, ["Checklista", "Snabblistan", "Historik", "Senare"])

    def test_secondary_views_are_not_created_during_startup(self):
        view = self.make_view()
        self.assertIsNone(view.view_templates)
        self.assertIsNone(view.view_history)
        self.assertIsNone(view.view_later)
        self.assertIsNone(view.view_family)

    def test_secondary_view_is_created_on_first_request(self):
        view = self.make_view()
        created = view._ensure_view(1)
        self.assertIs(created, view.view_templates)
        self.assertIsNotNone(created)

    def test_lazily_created_view_is_reused(self):
        view = self.make_view()
        self.assertIs(view._ensure_view(2), view._ensure_view(2))

    def test_unknown_navigation_destination_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_view()._ensure_view(99)

    def test_family_repository_and_view_are_lazy(self):
        family_repository = MagicMock()
        factory = MagicMock(return_value=family_repository)
        view = MainView(InMemoryRepository(), family_repository_factory=factory)
        self.assertIsNone(view.view_family)
        factory.assert_not_called()

        family_view = view._ensure_family_view()
        factory.assert_called_once_with()
        self.assertIs(family_view.repository, family_repository)

    def test_family_mode_does_not_reload_private_repository_view(self):
        family_repository = MagicMock()
        view = MainView(
            InMemoryRepository(),
            family_repository_factory=MagicMock(return_value=family_repository),
        )
        view._refresh_active_view = MagicMock()
        family_view = view._ensure_family_view()
        family_view.activate = MagicMock()
        view.content_area.update = MagicMock()

        view._handle_mode_change(FAMILY_MODE)

        self.assertEqual(view.current_mode, FAMILY_MODE)
        self.assertIs(view.content_area.content, family_view)
        view._refresh_active_view.assert_not_called()
        family_view.activate.assert_called_once_with()

    def test_switching_from_family_to_private_replaces_family_view(self):
        view = MainView(
            InMemoryRepository(),
            family_repository_factory=MagicMock(return_value=MagicMock()),
        )
        view.content_area.update = MagicMock()
        view._ensure_family_view().activate = MagicMock()
        view._handle_mode_change(FAMILY_MODE)

        view._handle_mode_change(PRIVATE)

        self.assertEqual(view.current_mode, PRIVATE)
        self.assertIs(view.content_area.content, view.view_checklist)

    def test_switching_from_family_to_work_replaces_family_view(self):
        view = MainView(
            InMemoryRepository(),
            family_repository_factory=MagicMock(return_value=MagicMock()),
        )
        view.content_area.update = MagicMock()
        view._ensure_family_view().activate = MagicMock()
        view._handle_mode_change(FAMILY_MODE)

        view._handle_mode_change(WORK)

        self.assertEqual(view.current_mode, WORK)
        self.assertIs(view.content_area.content, view.view_checklist)

    def test_connected_family_uses_separate_bottom_pages(self):
        repository = MagicMock()
        view = MainView(InMemoryRepository(), family_repository_factory=MagicMock(return_value=repository))
        view._ensure_family_view()
        view.family_member = "Nicklas"

        current = view._ensure_family_page(0)
        favorites = view._ensure_family_page(1)
        history = view._ensure_family_page(2)
        later = view._ensure_family_page(3)

        self.assertIs(view._ensure_family_page(0), current)
        self.assertIsNot(favorites, current)
        self.assertIsNot(history, current)
        self.assertIsNot(later, current)
