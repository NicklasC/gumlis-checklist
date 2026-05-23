import uuid
from datetime import datetime
import flet as ft

from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY,
    EMERALD_GREEN, MINT_GREEN, CATEGORY_COLORS,
    glass_card_style, SURFACE_GLASS, border_all, active_item_style
)
from src.models.checklist import ChecklistItem, Checklist

class LaterView(ft.Container):
    def __init__(self, repo, on_item_promoted, main_view, *args, **kwargs):
        self.repo = repo
        self.on_item_promoted = on_item_promoted
        self.main_view = main_view
        self.later_list = None
        
        # Main scrollable list container
        self.list_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            expand=True
        )
        
        # Compact section header
        self.header_row = ft.Row(
            controls=[
                ft.Text(
                    value="Spara till senare",
                    size=13,
                    weight=ft.FontWeight.W_700,
                    color=TEXT_SECONDARY
                )
            ]
        )
        
        # Text input at the bottom (full-width)
        self.text_field = ft.TextField(
            hint_text="Lägg till i Senare...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.with_opacity(0.4, SURFACE_GLASS),
            border_color="#1E2E26",
            focused_border_color=MINT_GREEN,
            border_radius=16,
            content_padding=ft.Padding(left=12, top=6, right=12, bottom=6),
            expand=True,
            on_submit=self._handle_submit,
            autofocus=False
        )
        
        self.submit_btn = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD_ROUNDED,
            icon_color=TEXT_PRIMARY,
            bgcolor=EMERALD_GREEN,
            icon_size=16,
            width=32,
            height=32,
            tooltip="Lägg till i Senare",
            on_click=self._handle_submit,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10)
            )
        )
        
        self.quick_add_container = ft.Container(
            content=ft.Row(
                controls=[
                    self.text_field,
                    self.submit_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            **glass_card_style(padding=8, border_radius=12, border_color="#1C2E25")
        )

        self._load_data()

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.header_row, padding=ft.Padding(left=2, top=0, right=2, bottom=4)),
                    ft.Container(
                        content=self.list_container,
                        expand=True,
                        padding=ft.Padding(left=0, top=2, right=0, bottom=2)
                    ),
                    ft.Container(content=self.quick_add_container, padding=ft.Padding(left=0, top=6, right=0, bottom=0))
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
        """Loads later items and renders them."""
        self.later_list = self.repo.get_checklist("later_list")
        if not self.later_list:
            self.later_list = Checklist(
                id="later_list",
                title="Senare",
                items=[]
            )
            self.repo.save_checklist(self.later_list)
            
        self._refresh_list()

    def _refresh_list(self):
        self.list_container.controls.clear()
        active_mode = self.main_view.current_mode
        
        # Filter backlog items by global mode
        items_to_render = [item for item in self.later_list.items if item.category == active_mode]
        
        if not items_to_render:
            empty_msg = "Inga privata uppgifter i Senare" if active_mode == "Att göra" else "Inga jobb-uppgifter i Senare"
            self.list_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.ALL_INBOX_ROUNDED, size=48, color=ft.Colors.with_opacity(0.3, MINT_GREEN)),
                            ft.Text(value=empty_msg, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(value="Skriv in en uppgift nedan för att spara till senare.", size=11, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding(left=0, top=40, right=0, bottom=40)
                )
            )
            if self._is_mounted():
                self.list_container.update()
            return

        # Render items as glassmorphic cards
        color = EMERALD_GREEN if active_mode == "Att göra" else "#8B5CF6"
        for item in items_to_render:
            indicator = ft.Container(
                width=4,
                height=16,
                bgcolor=color,
                border_radius=2
            )
            
            text_label = ft.Text(
                value=item.title,
                size=14,
                weight=ft.FontWeight.W_500,
                color=TEXT_PRIMARY,
                text_align=ft.TextAlign.LEFT,
                overflow=ft.TextOverflow.ELLIPSIS,
                max_lines=2
            )
            
            # Action button: Move to today
            promote_btn = ft.IconButton(
                icon=ft.Icons.TODAY_ROUNDED,
                icon_color=MINT_GREEN,
                icon_size=18,
                tooltip="Flytta till idag",
                on_click=lambda e, itm=item: self._promote_item(itm),
                width=32,
                height=32,
                padding=0
            )
            
            # Action button: Delete
            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                icon_color=ft.Colors.with_opacity(0.6, ft.Colors.RED_400),
                icon_size=18,
                tooltip="Ta bort",
                on_click=lambda e, itm=item: self._delete_item(itm),
                width=32,
                height=32,
                padding=0
            )
            
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                indicator,
                                ft.Container(
                                    content=text_label,
                                    expand=True,
                                    padding=ft.Padding(left=6, top=0, right=6, bottom=0)
                                )
                            ],
                            expand=True,
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[
                                promote_btn,
                                delete_btn
                            ],
                            tight=True,
                            spacing=6
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                **active_item_style()
            )
            
            self.list_container.controls.append(card)

        if self._is_mounted():
            self.list_container.update()

    def _handle_submit(self, e):
        title = self.text_field.value.strip()
        if not title:
            self.text_field.focus()
            return
            
        active_mode = self.main_view.current_mode
        new_item = ChecklistItem(
            id=f"item_{uuid.uuid4().hex[:8]}",
            title=title,
            is_checked=False,
            category=active_mode
        )
        self.later_list.items.append(new_item)
        self.repo.save_checklist(self.later_list)
        
        self.text_field.value = ""
        self.text_field.update()
        
        self._refresh_list()

    def _delete_item(self, item: ChecklistItem):
        self.later_list.items = [i for i in self.later_list.items if i.id != item.id]
        self.repo.save_checklist(self.later_list)
        self._refresh_list()

    def _promote_item(self, item: ChecklistItem):
        """Removes the item from later_list and moves it to active_list (today) maintaining category."""
        # 1. Remove from later_list
        self.later_list.items = [i for i in self.later_list.items if i.id != item.id]
        self.repo.save_checklist(self.later_list)
        
        # 2. Add to active_list (maintains original category!)
        active_list = self.repo.get_checklist("active_list")
        if active_list:
            item.is_checked = False
            item.created_at = datetime.utcnow().isoformat() + "Z"
            active_list.items.append(item)
            self.repo.save_checklist(active_list)
            
        # 3. Refresh list
        self._refresh_list()
        
        # 4. Trigger callback to update main checklist and show snackbar
        if self.on_item_promoted:
            self.on_item_promoted(item)
