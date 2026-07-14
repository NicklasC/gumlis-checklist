import unittest
from unittest.mock import MagicMock

from src.views.main_view import SegmentedToggle
from tests.support.fixtures import PRIVATE, WORK


class SegmentedToggleTests(unittest.TestCase):
    def test_defaults_to_private(self):
        toggle = SegmentedToggle(MagicMock())
        self.assertEqual(toggle.active_mode, PRIVATE)

    def test_switches_to_work(self):
        toggle = SegmentedToggle(MagicMock())
        toggle._toggle_mode(WORK)
        self.assertEqual(toggle.active_mode, WORK)

    def test_switch_calls_callback(self):
        callback = MagicMock()
        toggle = SegmentedToggle(callback)
        toggle._toggle_mode(WORK)
        callback.assert_called_once_with(WORK)

    def test_selecting_active_mode_does_not_call_callback(self):
        callback = MagicMock()
        toggle = SegmentedToggle(callback)
        toggle._toggle_mode(PRIVATE)
        callback.assert_not_called()

    def test_work_mode_highlights_work_button(self):
        toggle = SegmentedToggle(MagicMock())
        toggle._toggle_mode(WORK)
        self.assertIsNotNone(toggle.work_btn.bgcolor)

    def test_private_mode_highlights_private_button(self):
        toggle = SegmentedToggle(MagicMock(), active_mode=PRIVATE)
        self.assertIsNotNone(toggle.todo_btn.bgcolor)
