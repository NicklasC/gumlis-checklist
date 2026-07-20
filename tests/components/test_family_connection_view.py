import unittest
from unittest.mock import AsyncMock

from src.models.family import FamilyConnection
from src.core.theme import MINT_GREEN, TEXT_MUTED, TEXT_PRIMARY
from src.views.family_connection_view import FamilyConnectionView


class FamilyConnectionViewTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self):
        repository = AsyncMock()
        repository.resume.return_value = None
        repository.connect.return_value = FamilyConnection("n" * 48, "Nicklas")
        view = FamilyConnectionView(repository)
        return view, repository

    async def test_device_key_field_uses_visible_dark_theme_colors(self):
        view, _ = self.make_view()
        self.assertEqual(view.token_field.text_style.color, TEXT_PRIMARY)
        self.assertEqual(view.token_field.label_style.color, TEXT_MUTED)
        self.assertEqual(view.token_field.cursor_color, MINT_GREEN)
        self.assertFalse(view.token_field.autocorrect)
        self.assertFalse(view.token_field.enable_suggestions)
        self.assertFalse(view.token_field.smart_dashes_type)
        self.assertFalse(view.token_field.smart_quotes_type)

    async def test_successful_connection_shows_server_member(self):
        view, repository = self.make_view()
        view.token_field.value = "n" * 48
        await view._connect()
        repository.connect.assert_awaited_once_with("n" * 48)
        self.assertEqual(view.status_text.value, "Ansluten som Nicklas")
        self.assertTrue(view.disconnect_button.visible)

    async def test_wrong_key_shows_clear_error(self):
        view, repository = self.make_view()
        repository.connect.side_effect = PermissionError("Enhetsnyckeln känns inte igen")
        view.token_field.value = "x" * 48
        await view._connect()
        self.assertEqual(view.status_text.value, "Enhetsnyckeln känns inte igen")
        self.assertTrue(view.token_field.visible)

    async def test_resume_shows_persisted_member(self):
        view, repository = self.make_view()
        repository.resume.return_value = FamilyConnection("i" * 48, "Ida")
        await view._resume()
        self.assertEqual(view.status_text.value, "Ansluten som Ida")

    async def test_disconnect_returns_to_connection_form(self):
        view, repository = self.make_view()
        view._show_connected("Thor")
        await view._disconnect()
        repository.disconnect.assert_awaited_once()
        self.assertTrue(view.token_field.visible)
        self.assertFalse(view.disconnect_button.visible)
