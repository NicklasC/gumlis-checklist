import unittest
from unittest.mock import MagicMock

from src.views.components.family_quick_add import FamilyQuickAdd


class FamilyQuickAddTests(unittest.TestCase):
    def test_uses_same_prompt_and_clear_family_action(self):
        component = FamilyQuickAdd(MagicMock())

        self.assertEqual(component.text_field.hint_text, "Skriv något att göra...")
        self.assertEqual(
            component.continue_button.content.controls[1].value,
            "+ Familjeuppgift",
        )

    def test_continue_trims_title_without_clearing_before_save(self):
        callback = MagicMock()
        component = FamilyQuickAdd(callback)
        component.set_enabled(True)
        component.text_field.value = "  Töm soporna  "

        component._continue()

        callback.assert_called_once_with("Töm soporna")
        self.assertEqual(component.text_field.value, "Töm soporna")

    def test_blank_or_disabled_composer_does_not_open_editor(self):
        callback = MagicMock()
        component = FamilyQuickAdd(callback)
        component.text_field.value = "Töm soporna"

        component._continue()
        component.set_enabled(True)
        component.text_field.value = "   "
        component._continue()

        callback.assert_not_called()

    def test_successful_create_can_clear_composer(self):
        component = FamilyQuickAdd(MagicMock())
        component.text_field.value = "Töm soporna"

        component.clear()

        self.assertEqual(component.text_field.value, "")
