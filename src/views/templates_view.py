import uuid
import flet as ft

from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY,
    EMERALD_GREEN, MINT_GREEN, glass_card_style,
    SURFACE_COLOR, SURFACE_GLOW, border_all
)
from src.models.checklist import CommonGroup

class TemplatesView(ft.Container):
    def __init__(self, repo, on_template_added_to_active, main_view, *args, **kwargs):
        self.repo = repo
        self.on_template_added_to_active = on_template_added_to_active
        self.main_view = main_view
        self.groups = []
        
        # Main layout container
        self.cards_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            expand=True
        )
        
        # Compact section header
        self.header_row = ft.Row(
            controls=[
                ft.Text(
                    value="Hantera favoriter",
                    size=13,
                    weight=ft.FontWeight.W_700,
                    color=TEXT_SECONDARY
                )
            ]
        )

        self._load_data()

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.header_row, padding=ft.Padding(left=2, top=0, right=2, bottom=4)),
                    self.cards_container
                ],
                expand=True,
                spacing=0
            ),
            padding=ft.Padding(left=12, top=4, right=12, bottom=6),
            expand=True,
            **kwargs
        )

    def _is_mounted(self):
        try:
            return self.page is not None
        except (RuntimeError, AttributeError):
            return False

    def _load_data(self):
        """Loads template groups from storage."""
        self.groups = self.repo.get_all_common_groups()
        self._refresh_cards()

    def _refresh_cards(self):
        """Renders only the favorites card corresponding to active global mode."""
        self.cards_container.controls.clear()
        
        active_mode = self.main_view.current_mode
        active_group = None
        for group in self.groups:
            if active_mode == "Att göra" and group.id == "todo_favorites":
                active_group = group
                break
            elif active_mode == "Jobb" and group.id == "work_favorites":
                active_group = group
                break
                
        if not active_group and self.groups:
            active_group = self.groups[0]
            
        if active_group:
            card = self._build_group_card(active_group)
            self.cards_container.controls.append(card)
        else:
            self.cards_container.controls.append(
                ft.Container(
                    content=ft.Text("Inga favoritgrupper tillgängliga.", size=12, color=TEXT_MUTED),
                    padding=ft.Padding(left=0, top=16, right=0, bottom=16)
                )
            )
            
        if self._is_mounted():
            self.cards_container.update()

    def _build_group_card(self, group: CommonGroup) -> ft.Container:
        pills = []
        active_mode = self.main_view.current_mode
        pill_color = EMERALD_GREEN if active_mode == "Att göra" else "#8B5CF6"
        
        for item in group.items:
            pills.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.GestureDetector(
                                mouse_cursor=ft.MouseCursor.CLICK,
                                on_tap=lambda e, val=item, gname=group.name: self._handle_item_tap(val, gname),
                                content=ft.Text(
                                    value=item,
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=TEXT_PRIMARY
                                )
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=11,
                                icon_color=ft.Colors.RED_300,
                                tooltip="Ta bort favorit",
                                width=18,
                                height=18,
                                padding=0,
                                on_click=lambda e, val=item, grp=group: self._remove_item_from_group(val, grp)
                            )
                        ],
                        tight=True,
                        spacing=4
                    ),
                    bgcolor=ft.Colors.with_opacity(0.15, SURFACE_GLOW),
                    border=border_all(1.0, "#23332A"),
                    border_radius=8,
                    padding=ft.Padding(left=6, top=4, right=6, bottom=4),
                )
            )

        # Field to add a new favorite item inside this group
        new_item_field = ft.TextField(
            hint_text="Skriv ny favorit...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, size=12),
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=12),
            bgcolor=ft.Colors.with_opacity(0.2, SURFACE_COLOR),
            border_color="#1E2E26",
            focused_border_color=MINT_GREEN,
            border_radius=10,
            content_padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            height=28,
            expand=True,
        )
        
        new_item_field.on_submit = lambda e, grp=group, tf=new_item_field: self._add_item_to_group(tf, grp)

        add_btn = ft.IconButton(
            icon=ft.Icons.ADD_ROUNDED,
            icon_color=TEXT_PRIMARY,
            bgcolor=EMERALD_GREEN,
            icon_size=12,
            width=28,
            height=28,
            on_click=lambda e, grp=group, tf=new_item_field: self._add_item_to_group(tf, grp),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        group_title = "Privat favoriter" if group.id == "todo_favorites" else "Jobb favoriter"

        card_content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            value=group_title,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row(
                        controls=pills,
                        wrap=True,
                        spacing=6,
                        run_spacing=6
                    ),
                    padding=ft.Padding(left=0, top=2, right=0, bottom=6) if pills else 0
                ),
                ft.Row(
                    controls=[
                        new_item_field,
                        add_btn
                    ],
                    spacing=6
                )
            ],
            spacing=4,
            tight=True
        )

        return ft.Container(
            content=card_content,
            **glass_card_style(padding=12, border_radius=14, border_color="#1C2E25")
        )

    def _handle_item_tap(self, title: str, group_name: str):
        """Triggers callback to add favorite item directly to checklist."""
        active_mode = self.main_view.current_mode
        if self.on_template_added_to_active:
            self.on_template_added_to_active(title, active_mode)

    def _add_item_to_group(self, text_field: ft.TextField, group: CommonGroup):
        title = text_field.value.strip()
        if not title:
            return
        
        # Avoid duplicate favorites in group
        if title not in group.items:
            group.items.append(title)
            self.repo.save_common_group(group)
            
        text_field.value = ""
        self._load_data()

    def _remove_item_from_group(self, item_title: str, group: CommonGroup):
        if item_title in group.items:
            group.items.remove(item_title)
            self.repo.save_common_group(group)
            self._load_data()
