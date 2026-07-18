"""Non-interactive application shell shown while browser data is loading."""

from datetime import datetime

import flet as ft

from src.core.theme import BG_COLOR, TEXT_PRIMARY, TEXT_SECONDARY


def _swedish_date() -> str:
    now = datetime.now()
    months = {
        1: "januari", 2: "februari", 3: "mars", 4: "april", 5: "maj", 6: "juni",
        7: "juli", 8: "augusti", 9: "september", 10: "oktober", 11: "november", 12: "december",
    }
    weekdays = {
        0: "måndag", 1: "tisdag", 2: "onsdag", 3: "torsdag", 4: "fredag", 5: "lördag", 6: "söndag",
    }
    return f"{weekdays[now.weekday()].capitalize()}, {now.day} {months[now.month]}"


def create_startup_view() -> ft.Container:
    """Build a visually stable shell without reading or mutating user data."""
    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Gumli", size=22, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                    ft.Text(_swedish_date(), size=12, weight=ft.FontWeight.W_500, color=TEXT_SECONDARY),
                ],
                spacing=2,
                tight=True,
            ),
            ft.Container(
                content=ft.Text("Privat", size=12, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY),
                padding=ft.Padding(left=14, top=8, right=14, bottom=8),
                bgcolor="#0A0E0C",
                border_radius=10,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    loading = ft.Column(
        controls=[
            ft.ProgressRing(width=28, height=28, stroke_width=2, color="#6EE7A8"),
            ft.Text("Laddar din checklista…", size=13, color=TEXT_SECONDARY),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        expand=True,
    )

    navigation = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST_OUTLINED, label="Checklista"),
            ft.NavigationBarDestination(icon=ft.Icons.BOLT_OUTLINED, label="Snabblistan"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY_OUTLINED, label="Historik"),
            ft.NavigationBarDestination(icon=ft.Icons.ALL_INBOX_OUTLINED, label="Senare"),
        ],
        selected_index=0,
        bgcolor="#0E1612",
        disabled=True,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(content=header, padding=ft.Padding(left=12, top=12, right=12, bottom=6)),
                loading,
                navigation,
            ],
            expand=True,
            spacing=0,
        ),
        bgcolor=BG_COLOR,
        expand=True,
    )
