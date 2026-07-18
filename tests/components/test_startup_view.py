import unittest

import flet as ft

from src.views.startup_view import create_startup_view


class StartupViewTests(unittest.TestCase):
    def setUp(self):
        self.view = create_startup_view()
        self.column = self.view.content

    def test_shell_matches_main_navigation_structure(self):
        navigation = self.column.controls[-1]
        self.assertIsInstance(navigation, ft.NavigationBar)
        self.assertEqual(
            [destination.label for destination in navigation.destinations],
            ["Checklista", "Snabblistan", "Historik", "Senare"],
        )

    def test_shell_navigation_is_not_interactive(self):
        self.assertTrue(self.column.controls[-1].disabled)

    def test_shell_identifies_application(self):
        header = self.column.controls[0].content
        self.assertEqual(header.controls[0].controls[0].value, "Gumli")

    def test_shell_has_loading_feedback(self):
        loading = self.column.controls[1]
        self.assertTrue(any(isinstance(control, ft.ProgressRing) for control in loading.controls))
        self.assertTrue(any(getattr(control, "value", "") == "Laddar din checklista…" for control in loading.controls))
