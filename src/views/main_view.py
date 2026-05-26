import flet as ft
from datetime import datetime

from src.core.theme import (
    BG_COLOR, MINT_GREEN, EMERALD_GREEN, TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY, border_all
)
from src.views.checklist_view import ChecklistView
from src.views.templates_view import TemplatesView
from src.views.history_view import HistoryView
from src.views.later_view import LaterView

def _get_swedish_date() -> str:
    now = datetime.now()
    months = {
        1: "januari", 2: "februari", 3: "mars", 4: "april", 5: "maj", 6: "juni",
        7: "juli", 8: "augusti", 9: "september", 10: "oktober", 11: "november", 12: "december"
    }
    days_of_week = {
        0: "måndag", 1: "tisdag", 2: "onsdag", 3: "torsdag", 4: "fredag", 5: "lördag", 6: "söndag"
    }
    day_name = days_of_week[now.weekday()]
    month_name = months[now.month]
    return f"{day_name.capitalize()}, {now.day} {month_name}"

class SegmentedToggle(ft.Container):
    def __init__(self, on_change, active_mode="Att göra"):
        self.on_change = on_change
        self.active_mode = active_mode # "Att göra" (Privat) or "Jobb"
        
        self.todo_btn = ft.Container(
            content=ft.Text("Privat", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            border_radius=8,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )
        
        self.work_btn = ft.Container(
            content=ft.Text("Jobb", size=12, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            border_radius=8,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )
        
        self.todo_gesture = ft.GestureDetector(
            content=self.todo_btn,
            on_tap=lambda e: self._toggle_mode("Att göra"),
            mouse_cursor=ft.MouseCursor.CLICK
        )
        
        self.work_gesture = ft.GestureDetector(
            content=self.work_btn,
            on_tap=lambda e: self._toggle_mode("Jobb"),
            mouse_cursor=ft.MouseCursor.CLICK
        )
        
        super().__init__(
            content=ft.Row(
                controls=[
                    self.todo_gesture,
                    self.work_gesture
                ],
                spacing=2,
                tight=True
            ),
            bgcolor="#0A0E0C",
            border=border_all(1.0, "#1F2E26"),
            border_radius=10,
            padding=2
        )
        
        self._update_ui()
        
    def _toggle_mode(self, mode):
        if self.active_mode == mode:
            return
        self.active_mode = mode
        self._update_ui()
        if self.on_change:
            self.on_change(mode)
            
    def _update_ui(self):
        if self.active_mode == "Att göra":
            self.todo_btn.bgcolor = ft.Colors.with_opacity(0.15, EMERALD_GREEN)
            self.todo_btn.content.color = MINT_GREEN
            self.work_btn.bgcolor = None
            self.work_btn.content.color = TEXT_MUTED
        else:
            self.todo_btn.bgcolor = None
            self.todo_btn.content.color = TEXT_MUTED
            self.work_btn.bgcolor = ft.Colors.with_opacity(0.15, "#8B5CF6") # Soft Indigo/Purple
            self.work_btn.content.color = "#A78BFA" # Mint pastel purple
        
        # Safe trigger if page is loaded
        try:
            self.todo_btn.update()
            self.work_btn.update()
        except Exception:
            pass

class MainView(ft.Container):
    def __init__(self, repo, *args, **kwargs):
        self.repo = repo
        self.current_mode = "Att göra" # Global mode state: "Att göra" (Privat) or "Jobb"
        
        # Pre-initialize sub-views with reference to parent to read current_mode
        self.view_checklist = ChecklistView(repo=self.repo, main_view=self)
        self.view_templates = TemplatesView(
            repo=self.repo,
            on_template_added_to_active=self._handle_template_added,
            main_view=self
        )
        self.view_history = HistoryView(
            repo=self.repo,
            on_item_restored=self._handle_item_restored,
            main_view=self
        )
        self.view_later = LaterView(
            repo=self.repo,
            on_item_promoted=self._handle_item_promoted,
            main_view=self
        )
        
        # Container to hold the active view
        self.content_area = ft.Container(
            content=self.view_checklist,
            expand=True
        )
        
        # Persistent segmented toggle
        self.toggle = SegmentedToggle(on_change=self._handle_mode_change, active_mode=self.current_mode)
        
        # Persistent Global Header
        self.header_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            value="Gumli",
                            size=22,
                            weight=ft.FontWeight.W_800,
                            color=TEXT_PRIMARY
                        ),
                        ft.Text(
                            value=_get_swedish_date(),
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=TEXT_SECONDARY
                        )
                    ],
                    spacing=2,
                    tight=True
                ),
                self.toggle
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Navigation Bar (Optimized for mobile bottom layout)
        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CHECKLIST_OUTLINED,
                    selected_icon=ft.Icons.CHECKLIST_ROUNDED,
                    label="Checklista"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BOLT_OUTLINED,
                    selected_icon=ft.Icons.BOLT_ROUNDED,
                    label="Snabblistan"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.HISTORY_OUTLINED,
                    selected_icon=ft.Icons.HISTORY_ROUNDED,
                    label="Historik"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ALL_INBOX_OUTLINED,
                    selected_icon=ft.Icons.ALL_INBOX_ROUNDED,
                    label="Senare"
                )
            ],
            selected_index=0,
            on_change=self._handle_nav_change,
            bgcolor="#0E1612",
            indicator_color=ft.Colors.with_opacity(0.12, MINT_GREEN),
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self.header_row,
                        padding=ft.Padding(left=12, top=12, right=12, bottom=6)
                    ),
                    self.content_area,
                    self.nav_bar
                ],
                expand=True,
                spacing=0
            ),
            bgcolor=BG_COLOR,
            expand=True,
            **kwargs
        )

    def initialize_data(self):
        """Safely loads active checklist data after the page connection is established."""
        self.view_checklist._load_data_and_clean()

    def _handle_mode_change(self, mode):
        """Switches global mode and triggers active view updates."""
        self.current_mode = mode
        self._refresh_active_view()

    def _handle_nav_change(self, e):
        """Switches screens and reloads their respective data for reactive UI synchronization."""
        idx = int(e.data)
        
        if idx == 0:
            self.view_checklist._load_data_and_clean()
            self.content_area.content = self.view_checklist
        elif idx == 1:
            self.view_templates._load_data()
            self.content_area.content = self.view_templates
        elif idx == 2:
            self.view_history._load_data()
            self.content_area.content = self.view_history
        elif idx == 3:
            self.view_later._load_data()
            self.content_area.content = self.view_later
            
        self.content_area.update()

    def _refresh_active_view(self):
        """Triggers data load and UI update for whatever screen is currently visible."""
        idx = self.nav_bar.selected_index
        if idx == 0:
            self.view_checklist._load_data_and_clean()
        elif idx == 1:
            self.view_templates._load_data()
        elif idx == 2:
            self.view_history._load_data()
        elif idx == 3:
            self.view_later._load_data()
        self.content_area.update()

    def _handle_template_added(self, title: str, group_name: str):
        """Callback from Snabblistan tab: adds the item to the active checklist and shows a snackbar."""
        self.view_checklist._add_favorite_item(title, group_name)
        
        # Show elegant feedback toast in Swedish
        snack = ft.SnackBar(
            content=ft.Text(f"Lade till '{title}' i checklistan!", color=TEXT_PRIMARY),
            bgcolor="#142C20",
            duration=1500,
            open=True
        )
        self.page.overlay.append(snack)
        self.page.update()

    def _handle_item_restored(self):
        """Callback from History tab when an item is restored: forces checklist view to refresh in background."""
        self.view_checklist._load_data_and_clean()
        
        snack = ft.SnackBar(
            content=ft.Text("Uppgiften återställd till checklistan!", color=TEXT_PRIMARY),
            bgcolor="#142C20",
            duration=1500,
            open=True
        )
        self.page.overlay.append(snack)
        self.page.update()

    def _handle_item_promoted(self, item):
        """Callback from LaterView when an item is promoted to today's active checklist."""
        self.view_checklist._load_data_and_clean()
        
        # Show elegant feedback snackbar in Swedish
        snack = ft.SnackBar(
            content=ft.Text(f"Flyttade '{item.title}' till idag!", color=TEXT_PRIMARY),
            bgcolor="#142C20",
            duration=1500,
            open=True
        )
        self.page.overlay.append(snack)
        self.page.update()
