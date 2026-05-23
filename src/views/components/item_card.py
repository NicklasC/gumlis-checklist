import flet as ft
from src.models.checklist import ChecklistItem
from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, TEXT_DISABLED,
    EMERALD_GREEN, MINT_GREEN, CATEGORY_COLORS,
    active_item_style, checked_item_style
)

class ItemCard(ft.Container):
    def __init__(
        self,
        item: ChecklistItem,
        on_check_changed,
        on_deleted,
        on_move_to_later=None,
        *args,
        **kwargs
    ):
        self.item = item
        self.on_check_changed = on_check_changed
        self.on_deleted = on_deleted
        self.on_move_to_later = on_move_to_later
        
        # Determine styling based on checked state
        style = checked_item_style() if item.is_checked else active_item_style()
        
        # Left-side category indicator bar
        category_color = CATEGORY_COLORS.get(item.category, "#6B7280")
        self.indicator = ft.Container(
            width=4,
            height=16,
            bgcolor=category_color,
            border_radius=2
        )
        
        # Checkbox icon (custom premium design)
        self.check_button = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE if item.is_checked else ft.Icons.RADIO_BUTTON_UNCHECKED,
            icon_color=MINT_GREEN if item.is_checked else TEXT_MUTED,
            icon_size=20,
            width=32,
            height=32,
            padding=0,
            tooltip="Markera som klar" if not item.is_checked else "Markera som ogjord",
            on_click=self._handle_check_click,
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT_BACK)
        )
        
        # Text label (with strike-through if checked)
        self.text_label = ft.Text(
            value=item.title,
            size=14,
            weight=ft.FontWeight.W_500,
            color=TEXT_DISABLED if item.is_checked else TEXT_PRIMARY,
            text_align=ft.TextAlign.LEFT,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=2,
            style=ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH if item.is_checked else ft.TextDecoration.NONE
            )
        )
        
        # Move to later button
        self.move_later_button = ft.IconButton(
            icon=ft.Icons.MOVE_TO_INBOX_ROUNDED,
            icon_color=TEXT_MUTED,
            icon_size=18,
            width=32,
            height=32,
            padding=0,
            tooltip="Flytta till Senare",
            on_click=self._handle_move_later_click,
            visible=on_move_to_later is not None and not item.is_checked,
            mouse_cursor=ft.MouseCursor.CLICK
        )
        
        # Delete button (only visible on hover or compact trailing action)
        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.with_opacity(0.6, ft.Colors.RED_400),
            icon_size=18,
            width=32,
            height=32,
            padding=0,
            tooltip="Radera",
            on_click=self._handle_delete_click,
            animate_opacity=200,
            mouse_cursor=ft.MouseCursor.CLICK
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            self.indicator,
                            self.check_button,
                            ft.Container(
                                content=self.text_label,
                                expand=True,
                                padding=ft.Padding(left=2, top=0, right=6, bottom=0)
                            )
                        ],
                        expand=True,
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Row(
                        controls=[
                            self.move_later_button,
                            self.delete_button
                        ],
                        spacing=6,
                        tight=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **style,
            **kwargs
        )

    def _handle_check_click(self, e):
        # Toggle checked state
        self.item.is_checked = not self.item.is_checked
        
        # Animate scale of the check button
        self.check_button.scale = 1.2
        self.check_button.update()
        
        # Apply updated styling
        self._update_appearance()
        
        # Reset check button scale
        self.check_button.scale = 1.0
        self.check_button.update()
        
        # Invoke callback
        if self.on_check_changed:
            self.on_check_changed(self.item)

    def _handle_delete_click(self, e):
        if self.on_deleted:
            self.on_deleted(self.item)

    def _handle_move_later_click(self, e):
        if self.on_move_to_later:
            self.on_move_to_later(self.item)

    def _update_appearance(self):
        """Helper to update visual elements when checked state toggles."""
        if self.item.is_checked:
            self.check_button.icon = ft.Icons.CHECK_CIRCLE
            self.check_button.icon_color = MINT_GREEN
            self.text_label.color = TEXT_DISABLED
            self.text_label.style.decoration = ft.TextDecoration.LINE_THROUGH
            if hasattr(self, 'move_later_button'):
                self.move_later_button.visible = False
            
            # Apply checked style properties
            for k, v in checked_item_style().items():
                setattr(self, k, v)
        else:
            self.check_button.icon = ft.Icons.RADIO_BUTTON_UNCHECKED
            self.check_button.icon_color = TEXT_MUTED
            self.text_label.color = TEXT_PRIMARY
            self.text_label.style.decoration = ft.TextDecoration.NONE
            if hasattr(self, 'move_later_button'):
                self.move_later_button.visible = self.on_move_to_later is not None
            
            # Apply active style properties
            for k, v in active_item_style().items():
                setattr(self, k, v)
        
        self.update()
