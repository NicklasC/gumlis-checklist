import unittest
from unittest.mock import MagicMock

from src.views.components.quick_add import QuickAdd
from tests.support.fixtures import PRIVATE, WORK, StubMainView


class QuickAddTests(unittest.TestCase):
    def make_component(self, mode=PRIVATE):
        callback = MagicMock()
        component = QuickAdd(callback, StubMainView(mode))
        component.text_field.update = MagicMock()
        component.text_field.focus = MagicMock()
        return component, callback

    def test_private_mode_uses_private_button_label(self):
        component, _ = self.make_component(PRIVATE)
        self.assertEqual(component.todo_text.value, "+ Att göra")

    def test_work_mode_uses_work_button_label(self):
        component, _ = self.make_component(WORK)
        self.assertEqual(component.todo_text.value, "+ Jobb")

    def test_today_button_routes_to_active_mode(self):
        component, callback = self.make_component(WORK)
        component.text_field.value = "Planera"
        component._handle_button_click("today")
        callback.assert_called_once_with("Planera", WORK)

    def test_later_button_routes_to_later(self):
        component, callback = self.make_component(PRIVATE)
        component.text_field.value = "Planera"
        component._handle_button_click("Senare")
        callback.assert_called_once_with("Planera", "Senare")

    def test_enter_routes_to_active_mode(self):
        component, callback = self.make_component(WORK)
        component.text_field.value = "Planera"
        component._handle_submit_default(None)
        callback.assert_called_once_with("Planera", WORK)

    def test_submission_trims_title(self):
        component, callback = self.make_component()
        component.text_field.value = "  Planera  "
        component._handle_submit_default(None)
        callback.assert_called_once_with("Planera", PRIVATE)

    def test_submission_clears_field(self):
        component, _ = self.make_component()
        component.text_field.value = "Planera"
        component._handle_submit_default(None)
        self.assertEqual(component.text_field.value, "")

    def test_blank_submission_does_not_call_callback(self):
        component, callback = self.make_component()
        component.text_field.value = "   "
        component._handle_submit_default(None)
        callback.assert_not_called()

    def test_blank_submission_focuses_field(self):
        component, _ = self.make_component()
        component.text_field.value = ""
        component._handle_submit_default(None)
        component.text_field.focus.assert_called_once()
