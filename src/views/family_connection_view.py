from __future__ import annotations

import inspect

import flet as ft

from src.core.theme import BG_COLOR, MINT_GREEN, TEXT_MUTED, TEXT_PRIMARY, border_all


class FamilyConnectionView(ft.Container):
    """Small first-run view used by the bounded family feasibility test."""

    def __init__(self, repository, on_connected=None):
        self.repository = repository
        self.on_connected = on_connected
        self._load_started = False
        self.token_field = ft.TextField(
            label="Enhetsnyckel",
            password=True,
            can_reveal_password=True,
            autofocus=False,
            autocorrect=False,
            enable_suggestions=False,
            smart_dashes_type=False,
            smart_quotes_type=False,
            enable_ime_personalized_learning=False,
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=14),
            label_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            cursor_color=MINT_GREEN,
            border_color="#294238",
            focused_border_color=MINT_GREEN,
        )
        self.status_text = ft.Text("", color=TEXT_MUTED, size=13)
        self.connect_button = ft.FilledButton(
            content=ft.Text("Anslut den här enheten"),
            on_click=self._connect,
        )
        self.disconnect_button = ft.TextButton(
            content=ft.Text("Koppla från Familj"),
            on_click=self._disconnect,
            visible=False,
        )
        self.form = ft.Column(
            controls=[
                ft.Text("Anslut Familj", size=22, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                ft.Text(
                    "Ange den privata enhetsnyckeln en gång. Den sparas endast på den här enheten.",
                    size=13,
                    color=TEXT_MUTED,
                ),
                self.token_field,
                self.connect_button,
                self.status_text,
                self.disconnect_button,
            ],
            spacing=12,
        )
        super().__init__(
            content=ft.Container(
                content=self.form,
                padding=20,
                margin=12,
                border=border_all(1.0, "#1F352B"),
                border_radius=16,
                bgcolor="#101B16",
            ),
            bgcolor=BG_COLOR,
            expand=True,
        )

    def activate(self):
        if self._load_started or self.page is None:
            return
        self._load_started = True
        self.page.run_task(self._resume)

    async def _resume(self):
        self._set_busy("Kontrollerar familjeanslutningen …")
        try:
            connection = await self.repository.resume()
            if connection is None:
                self._show_disconnected()
            else:
                self._show_connected(connection.member)
                await self._notify_connected(connection.member)
        except PermissionError as error:
            try:
                await self.repository.disconnect()
            except Exception:
                pass
            self._show_error(str(error))
        except Exception:
            self._show_error("Familjen kunde inte nås. Försök igen.")

    async def _connect(self, _event=None):
        token = str(self.token_field.value or "").strip()
        self._set_busy("Ansluter …")
        try:
            connection = await self.repository.connect(token)
            self.token_field.value = ""
            self._show_connected(connection.member)
            await self._notify_connected(connection.member)
        except (ValueError, PermissionError) as error:
            self._show_error(str(error))
        except Exception:
            self._show_error("Familjen kunde inte nås. Försök igen.")

    async def _notify_connected(self, member: str):
        if self.on_connected is None:
            return
        result = self.on_connected(member)
        if inspect.isawaitable(result):
            await result

    async def _disconnect(self, _event=None):
        await self.repository.disconnect()
        self._show_disconnected()

    def _set_busy(self, message: str):
        self.connect_button.disabled = True
        self.status_text.value = message
        self.status_text.color = TEXT_MUTED
        self._safe_update()

    def _show_connected(self, member: str):
        self.token_field.visible = False
        self.connect_button.visible = False
        self.connect_button.disabled = False
        self.disconnect_button.visible = True
        self.status_text.value = f"Ansluten som {member}"
        self.status_text.color = MINT_GREEN
        self._safe_update()

    def _show_disconnected(self):
        self.token_field.visible = True
        self.connect_button.visible = True
        self.connect_button.disabled = False
        self.disconnect_button.visible = False
        self.status_text.value = ""
        self._safe_update()

    def _show_error(self, message: str):
        self.token_field.visible = True
        self.connect_button.visible = True
        self.connect_button.disabled = False
        self.disconnect_button.visible = False
        self.status_text.value = message
        self.status_text.color = "#EF4444"
        self._safe_update()

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass
