import unittest
from unittest.mock import MagicMock

from src.views.components.item_card import ItemCard
from tests.support.fixtures import item


class ItemCardTests(unittest.TestCase):
    def make_card(self, checked=False, with_later=True):
        on_check = MagicMock()
        on_delete = MagicMock()
        on_later = MagicMock() if with_later else None
        value = item("one", "Test", checked=checked)
        card = ItemCard(value, on_check, on_delete, on_later)
        card.update = MagicMock()
        card.check_button.update = MagicMock()
        return card, on_check, on_delete, on_later

    def test_unchecked_item_has_complete_tooltip(self):
        card, *_ = self.make_card()
        self.assertEqual(card.check_button.tooltip, "Markera som klar")

    def test_checked_item_has_undo_tooltip(self):
        card, *_ = self.make_card(checked=True)
        self.assertEqual(card.check_button.tooltip, "Markera som ogjord")

    def test_later_button_is_visible_for_unchecked_item(self):
        card, *_ = self.make_card()
        self.assertTrue(card.move_later_button.visible)

    def test_later_button_is_hidden_for_checked_item(self):
        card, *_ = self.make_card(checked=True)
        self.assertFalse(card.move_later_button.visible)

    def test_check_click_toggles_state(self):
        card, *_ = self.make_card()
        card._handle_check_click(None)
        self.assertTrue(card.item.is_checked)

    def test_check_click_calls_callback(self):
        card, on_check, *_ = self.make_card()
        card._handle_check_click(None)
        on_check.assert_called_once_with(card.item)

    def test_checked_text_is_struck_through(self):
        card, *_ = self.make_card()
        card._handle_check_click(None)
        self.assertEqual(card.text_label.style.decoration.name, "LINE_THROUGH")

    def test_delete_click_calls_callback(self):
        card, _, on_delete, _ = self.make_card()
        card._handle_delete_click(None)
        on_delete.assert_called_once_with(card.item)

    def test_move_later_click_calls_callback(self):
        card, _, _, on_later = self.make_card()
        card._handle_move_later_click(None)
        on_later.assert_called_once_with(card.item)

    def test_move_later_is_hidden_without_callback(self):
        card, *_ = self.make_card(with_later=False)
        self.assertFalse(card.move_later_button.visible)
