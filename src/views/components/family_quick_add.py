from __future__ import annotations

import flet as ft

from src.core.theme import (
    MINT_GREEN,
    SURFACE_GLASS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    border_all,
    glass_card_style,
)


class FamilyQuickAdd(ft.Container):
    """Family quick composer that hands a title to the detailed editor."""

    def __init__(self, on_continue, *args, **kwargs):
        self.on_continue = on_continue
        self._enabled = False
        self.text_field = ft.TextField(
            hint_text="Skriv något att göra...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            text_style=ft.TextStyle(
                color=TEXT_PRIMARY,
                size=13,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=ft.Colors.with_opacity(0.4, SURFACE_GLASS),
            border_color="#1E2E26",
            focused_border_color=MINT_GREEN,
            border_radius=16,
            content_padding=ft.Padding(left=12, top=6, right=12, bottom=6),
            disabled=True,
            on_submit=self._continue,
        )
        self.continue_button = ft.FilledButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.GROUP_ROUNDED, size=14),
                    ft.Text(
                        "+ Familjeuppgift",
                        size=12,
                        weight=ft.FontWeight.W_700,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                tight=True,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.with_opacity(0.12, MINT_GREEN),
                color=TEXT_PRIMARY,
                side=border_all(1.0, ft.Colors.with_opacity(0.25, MINT_GREEN)),
                padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            ),
            disabled=True,
            expand=True,
            on_click=self._continue,
        )

        super().__init__(
            *args,
            content=ft.Column(
                controls=[
                    ft.Row(controls=[self.continue_button]),
                    ft.Container(height=6),
                    self.text_field,
                ],
                tight=True,
                spacing=0,
            ),
            **glass_card_style(padding=8, border_radius=12, border_color="#1C2E25"),
            **kwargs,
        )

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.text_field.disabled = not enabled
        self.continue_button.disabled = not enabled
        self._safe_update()

    def clear(self) -> None:
        self.set_title("")

    def set_title(self, title: str) -> None:
        self.text_field.value = title
        self._safe_update()

    def _continue(self, _event=None) -> None:
        if not self._enabled:
            return
        title = str(self.text_field.value or "").strip()
        if not title:
            try:
                if self.page is not None:
                    self.page.run_task(self.text_field.focus)
            except Exception:
                pass
            return
        self.text_field.value = title
        self.on_continue(title)

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass
