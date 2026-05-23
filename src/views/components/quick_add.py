import flet as ft
from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, EMERALD_GREEN, MINT_GREEN,
    SURFACE_GLASS, glass_card_style, border_all
)

class QuickAdd(ft.Container):
    def __init__(self, on_add_item, main_view=None, *args, **kwargs):
        self.on_add_item = on_add_item
        self.main_view = main_view
        
        # TextField for entering text (occupies 100% width on the bottom row)
        self.text_field = ft.TextField(
            hint_text="Skriv något att göra...",
            hint_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.with_opacity(0.4, SURFACE_GLASS),
            border_color="#1E2E26",
            focused_border_color=MINT_GREEN,
            border_radius=16,
            content_padding=ft.Padding(left=12, top=6, right=12, bottom=6),
            expand=True,
            on_submit=self._handle_submit_default,
            autofocus=False
        )
        
        # Primary Action Button (Today checklist - dynamically styled Privat/Jobb)
        self.todo_icon = ft.Icon(ft.Icons.HOME_ROUNDED, color=EMERALD_GREEN, size=14)
        self.todo_text = ft.Text("+ Att göra", size=12, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY)
        self.todo_btn = ft.Container(
            content=ft.Row(
                controls=[
                    self.todo_icon,
                    self.todo_text
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4
            ),
            bgcolor=ft.Colors.with_opacity(0.1, EMERALD_GREEN),
            border=border_all(1.0, ft.Colors.with_opacity(0.2, EMERALD_GREEN)),
            border_radius=10,
            padding=ft.Padding(left=4, top=8, right=4, bottom=8),
            expand=True
        )
        
        # Secondary Action Button (Context backlog - Amber)
        self.later_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHEDULE_ROUNDED, color="#F59E0B", size=14),
                    ft.Text("+ Senare", size=12, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4
            ),
            bgcolor=ft.Colors.with_opacity(0.1, "#F59E0B"),
            border=border_all(1.0, ft.Colors.with_opacity(0.2, "#F59E0B")),
            border_radius=10,
            padding=ft.Padding(left=4, top=8, right=4, bottom=8),
            expand=True
        )
        
        # GestureDetector wrapping for clicks
        self.todo_gesture = ft.GestureDetector(
            content=self.todo_btn,
            on_tap=lambda e: self._handle_button_click("today"),
            mouse_cursor=ft.MouseCursor.CLICK
        )
        
        self.later_gesture = ft.GestureDetector(
            content=self.later_btn,
            on_tap=lambda e: self._handle_button_click("Senare"),
            mouse_cursor=ft.MouseCursor.CLICK
        )
        
        # Main layout container
        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.todo_gesture,
                            self.later_gesture
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(height=6), # Compact spacing
                    ft.Row(
                        controls=[
                            self.text_field
                        ],
                        expand=True
                    )
                ],
                tight=True,
                spacing=0
            ),
            **glass_card_style(padding=8, border_radius=12, border_color="#1C2E25"),
            **kwargs
        )
        
        self._update_button_style()

    def _update_button_style(self):
        """Adapts the primary add button styling and labels to current global mode."""
        active_mode = "Att göra"
        if self.main_view:
            active_mode = self.main_view.current_mode
            
        if active_mode == "Att göra":
            self.todo_icon.name = ft.Icons.HOME_ROUNDED
            self.todo_icon.color = EMERALD_GREEN
            self.todo_text.value = "+ Att göra"
            self.todo_btn.bgcolor = ft.Colors.with_opacity(0.1, EMERALD_GREEN)
            self.todo_btn.border = border_all(1.0, ft.Colors.with_opacity(0.2, EMERALD_GREEN))
        else:
            self.todo_icon.name = ft.Icons.WORK_ROUNDED
            self.todo_icon.color = "#8B5CF6"
            self.todo_text.value = "+ Jobb"
            self.todo_btn.bgcolor = ft.Colors.with_opacity(0.1, "#8B5CF6")
            self.todo_btn.border = border_all(1.0, ft.Colors.with_opacity(0.2, "#8B5CF6"))
            
        try:
            self.todo_icon.update()
            self.todo_text.update()
            self.todo_btn.update()
        except Exception:
            pass

    def _handle_button_click(self, action_type: str):
        title = self.text_field.value.strip()
        if not title:
            self.text_field.focus()
            return
            
        active_mode = "Att göra"
        if self.main_view:
            active_mode = self.main_view.current_mode
            
        if action_type == "today":
            category = active_mode
        else:
            category = "Senare"
            
        if self.on_add_item:
            self.on_add_item(title, category)
            
        self.text_field.value = ""
        self.text_field.update()

    def _handle_submit_default(self, e):
        title = self.text_field.value.strip()
        if not title:
            self.text_field.focus()
            return
            
        # By default, hitting Enter will submit to the active global view mode today
        default_cat = "Att göra"
        if self.main_view:
            default_cat = self.main_view.current_mode
            
        if self.on_add_item:
            self.on_add_item(title, default_cat)
            
        self.text_field.value = ""
        self.text_field.update()
