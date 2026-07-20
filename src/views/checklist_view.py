import uuid
from datetime import datetime
import flet as ft

from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY,
    EMERALD_GREEN, MINT_GREEN, CATEGORY_COLORS,
    glass_card_style, SURFACE_COLOR, border_all
)
from src.core.time_utils import now_local_iso
from src.models.checklist import Checklist, ChecklistItem
from src.views.components.item_card import ItemCard
from src.views.components.quick_add import QuickAdd

class ChecklistView(ft.Container):
    def __init__(self, repo, main_view, *args, **kwargs):
        self.repo = repo
        self.main_view = main_view
        self.active_list = None
        self.common_groups = []
        self.snabblistan_expanded = False
        
        # Main list container
        self.list_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            expand=True
        )
        
        # Expandable Snabblistan drawer
        self.snabblistan_container = ft.Container(
            content=ft.Column(tight=True),
            visible=False,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )
        
        # Compact Header Row (just favorites button and section indicator)
        self.header_row = ft.Row(
            controls=[
                ft.Text(
                    value="Mina uppgifter",
                    size=13,
                    weight=ft.FontWeight.W_700,
                    color=TEXT_SECONDARY
                ),
                ft.IconButton(
                    icon=ft.Icons.BOLT_ROUNDED,
                    icon_color=MINT_GREEN,
                    icon_size=20,
                    tooltip="Snabblistan",
                    on_click=self._toggle_snabblistan,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.with_opacity(0.1, MINT_GREEN),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # Initialize active list and run daily clean-up
        self._load_data_and_clean()
        
        # Quick add component (passing self.main_view to adapt to global mode)
        self.quick_add = QuickAdd(
            on_add_item=self._add_new_item,
            main_view=self.main_view
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.header_row, padding=ft.Padding(left=2, top=0, right=2, bottom=4)),
                    self.snabblistan_container,
                    ft.Container(
                        content=self.list_container,
                        expand=True,
                        padding=ft.Padding(left=0, top=2, right=0, bottom=2)
                    ),
                    ft.Container(content=self.quick_add, padding=ft.Padding(left=0, top=6, right=0, bottom=0))
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

    def _load_data_and_clean(self):
        """Loads checklist, runs daily cleanup, and fetches template favorites."""
        self.active_list = self.repo.get_checklist("active_list")
        if not self.active_list:
            self.active_list = Checklist(
                id="active_list",
                title="Min checklista",
                items=[]
            )
            self.repo.save_checklist(self.active_list)
            
        # Daily Clean-up if date changed
        today_str = datetime.now().date().isoformat()
        if self.active_list.last_cleaned_date != today_str:
            self._perform_daily_cleanup(today_str)
            
        self.common_groups = self.repo.get_all_common_groups()
        
        self._refresh_snabblistan()
        self._refresh_checklist_items()
        
        # Trigger quick_add dynamic style update if it has been created
        if hasattr(self, "quick_add") and self.quick_add:
            self.quick_add._update_button_style()

    def _perform_daily_cleanup(self, today_str: str):
        """Archives checked tasks to history and resets the daily flag."""
        checked_items = [item for item in self.active_list.items if item.is_checked]
        if checked_items:
            history_list = self.repo.get_checklist("history_list")
            if not history_list:
                history_list = Checklist(
                    id="history_list",
                    title="Historik",
                    items=[]
                )
            
            completed_at = now_local_iso()
            for item in checked_items:
                if not item.completed_at:
                    item.completed_at = completed_at
                item.is_checked = True
                history_list.items.append(item)
                
            self.repo.save_checklist(history_list)
            
            # Remove completed from active checklist
            self.active_list.items = [item for item in self.active_list.items if not item.is_checked]
            
        self.active_list.last_cleaned_date = today_str
        self.repo.save_checklist(self.active_list)

    def _refresh_snabblistan(self):
        """Builds context-aware Snabblistan quick-add drawer corresponding to active mode."""
        pills = []
        active_mode = self.main_view.current_mode
        
        # Select Privat (todo_favorites) or Jobb (work_favorites) group
        active_group = None
        for group in self.common_groups:
            if active_mode == "Att göra" and group.id == "todo_favorites":
                active_group = group
                break
            elif active_mode == "Jobb" and group.id == "work_favorites":
                active_group = group
                break
                
        if not active_group and self.common_groups:
            active_group = self.common_groups[0]
            
        if active_group:
            pill_color = EMERALD_GREEN if active_mode == "Att göra" else "#8B5CF6"
            for item_name in active_group.items:
                pills.append(
                    ft.GestureDetector(
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_tap=lambda e, name=item_name, mode=active_mode: self._add_favorite_item(name, mode),
                        content=ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.BOLT_ROUNDED, color=pill_color, size=12),
                                    ft.Text(value=item_name, size=12, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)
                                ],
                                tight=True,
                                spacing=4
                            ),
                            bgcolor=ft.Colors.with_opacity(0.08, pill_color),
                            border=border_all(1.0, ft.Colors.with_opacity(0.2, pill_color)),
                            border_radius=8,
                            padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                        )
                    )
                )

        if not pills:
            self.snabblistan_container.content = ft.Container(
                content=ft.Text("Inga sparade favoriter för det här läget.", size=12, color=TEXT_MUTED),
                padding=ft.Padding(left=0, top=8, right=0, bottom=8)
            )
            return

        mode_label = "Privata" if active_mode == "Att göra" else "Jobb"
        self.snabblistan_container.content = ft.Column(
            controls=[
                ft.Text(f"{mode_label} favoriter (Klicka för att lägga till)", size=11, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                ft.Container(
                    content=ft.Row(
                        controls=pills,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=8,
                    ),
                    padding=ft.Padding(left=0, top=2, right=0, bottom=4)
                )
            ],
            spacing=4,
            tight=True
        )

    def _toggle_snabblistan(self, e):
        self.snabblistan_expanded = not self.snabblistan_expanded
        self.snabblistan_container.visible = self.snabblistan_expanded
        self.update()

    def _refresh_checklist_items(self):
        """Displays active checklist items filtered by global Privat/Jobb mode."""
        self.list_container.controls.clear()
        active_mode = self.main_view.current_mode
        
        # Filter active checklist items by current mode
        items_to_render = [item for item in self.active_list.items if item.category == active_mode]
        
        if not items_to_render:
            empty_msg = "Allt klart på den privata listan!" if active_mode == "Att göra" else "Allt klart på jobb-listan!"
            self.list_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.CHECKLIST_ROUNDED, size=48, color=ft.Colors.with_opacity(0.3, MINT_GREEN)),
                            ft.Text(value=empty_msg, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(value="Skriv in en uppgift eller välj från Snabblistan.", size=11, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER)
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

        # Split unchecked and checked items for rendering
        unchecked = [item for item in items_to_render if not item.is_checked]
        checked = [item for item in items_to_render if item.is_checked]

        # Sort within subgroups by creation date
        unchecked.sort(key=lambda x: x.created_at)
        checked.sort(key=lambda x: x.created_at)

        # Render item cards (unchecked first, then checked)
        for item in unchecked + checked:
            card = ItemCard(
                item=item,
                on_check_changed=self._handle_item_check,
                on_deleted=self._handle_item_delete,
                on_move_to_later=self._handle_item_move_to_later
            )
            self.list_container.controls.append(card)

        if self._is_mounted():
            self.list_container.update()

    def _add_new_item(self, title: str, category: str):
        """Explicitly routes and saves a new task."""
        if category == "Senare":
            # Context-aware later backlog insertion
            active_mode = self.main_view.current_mode
            self._add_to_later(title, active_mode)
        else:
            new_item = ChecklistItem(
                id=f"item_{uuid.uuid4().hex[:8]}",
                title=title,
                is_checked=False,
                category=category
            )
            self.active_list.items.append(new_item)
            self.repo.save_checklist(self.active_list)
            
            # Show quiet success toast if item routed to the other, currently hidden category
            current_mode = self.main_view.current_mode
            if category != current_mode and self._is_mounted():
                swedish_cat = "Jobb" if category == "Jobb" else "Privat"
                snack = ft.SnackBar(
                    content=ft.Text(f"Lagt till '{title}' i {swedish_cat}!", color=TEXT_PRIMARY),
                    bgcolor="#142C20",
                    duration=1500,
                    open=True
                )
                self.page.overlay.append(snack)
                self.page.update()
                
            self._refresh_checklist_items()

    def _add_to_later(self, title: str, category: str):
        """Adds a task directly to the later backlog."""
        later_list = self.repo.get_checklist("later_list")
        if not later_list:
            later_list = Checklist(id="later_list", title="Senare", items=[])
            
        new_item = ChecklistItem(
            id=f"item_{uuid.uuid4().hex[:8]}",
            title=title,
            is_checked=False,
            category=category
        )
        later_list.items.append(new_item)
        self.repo.save_checklist(later_list)
        
        # Show Swedish success toast
        if self._is_mounted():
            swedish_cat = "Jobb senare" if category == "Jobb" else "Privat senare"
            snack = ft.SnackBar(
                content=ft.Text(f"Flyttade '{title}' till {swedish_cat}!", color=TEXT_PRIMARY),
                bgcolor="#142C20",
                duration=1500,
                open=True
            )
            self.page.overlay.append(snack)
            self.page.update()

    def _add_favorite_item(self, title: str, category: str):
        """Instantly adds a favorite template item to the active checklist."""
        new_item = ChecklistItem(
            id=f"item_{uuid.uuid4().hex[:8]}",
            title=title,
            is_checked=False,
            category=category
        )
        
        # Avoid duplicate active items in active list
        exists = any(i.title == title and i.category == category and not i.is_checked for i in self.active_list.items)
        if exists:
            return

        self.active_list.items.append(new_item)
        self.repo.save_checklist(self.active_list)
        self._refresh_checklist_items()

    def _handle_item_check(self, item: ChecklistItem):
        item.completed_at = now_local_iso() if item.is_checked else None
        self.repo.save_checklist(self.active_list)
        self._refresh_checklist_items()

    def _handle_item_delete(self, item: ChecklistItem):
        self.active_list.items = [i for i in self.active_list.items if i.id != item.id]
        self.repo.save_checklist(self.active_list)
        self._refresh_checklist_items()

    def _handle_item_move_to_later(self, item: ChecklistItem):
        """Moves item from active_list to later_list, maintaining its category."""
        # 1. Remove from active
        self.active_list.items = [i for i in self.active_list.items if i.id != item.id]
        self.repo.save_checklist(self.active_list)
        
        # 2. Add to later
        later_list = self.repo.get_checklist("later_list")
        if not later_list:
            later_list = Checklist(id="later_list", title="Senare", items=[])
            
        item.is_checked = False
        item.completed_at = None
        item.created_at = datetime.utcnow().isoformat() + "Z"
        later_list.items.append(item)
        self.repo.save_checklist(later_list)
        
        self._refresh_checklist_items()
        
        # 3. Show Snackbar
        if self._is_mounted():
            swedish_cat = "Jobb senare" if item.category == "Jobb" else "Privat senare"
            snack = ft.SnackBar(
                content=ft.Text(f"Flyttade '{item.title}' till {swedish_cat}!", color=TEXT_PRIMARY),
                bgcolor="#142C20",
                duration=1500,
                open=True
            )
            self.page.overlay.append(snack)
            self.page.update()
