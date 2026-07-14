import unittest
from unittest.mock import MagicMock

from src.views.main_view import MainView
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
