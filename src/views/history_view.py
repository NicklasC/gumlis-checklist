from datetime import datetime, date
import flet as ft

from src.core.theme import (
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY,
    EMERALD_GREEN, MINT_GREEN, CATEGORY_COLORS,
    glass_card_style, SURFACE_COLOR, TEXT_DISABLED, border_all
)
from src.core.time_utils import history_date, history_timestamp
from src.models.checklist import ChecklistItem, Checklist

class HistoryView(ft.Container):
    def __init__(self, repo, on_item_restored, main_view, *args, **kwargs):
        self.repo = repo
        self.on_item_restored = on_item_restored
        self.main_view = main_view
        self.history_list = None
        
        # Main scrollable list
        self.history_container = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            expand=True
        )
        
        # Compact section header
        self.header_row = ft.Row(
            controls=[
                ft.Text(
                    value="Avklarade uppgifter",
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
                    self.history_container
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
        """Loads completed history and renders it."""
        self.history_list = self.repo.get_checklist("history_list")
        if not self.history_list:
            self.history_list = Checklist(
                id="history_list",
                title="Historik",
                items=[]
            )
            self.repo.save_checklist(self.history_list)
            
        self._refresh_history()

    def _refresh_history(self):
        self.history_container.controls.clear()
        active_mode = self.main_view.current_mode
        
        # Filter history items by current global mode
        items_to_render = [item for item in self.history_list.items if item.category == active_mode]
        
        if not items_to_render:
            empty_msg = "Ingen privat historik än" if active_mode == "Att göra" else "Ingen jobb-historik än"
            self.history_container.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=48, color=ft.Colors.with_opacity(0.3, MINT_GREEN)),
                            ft.Text(value=empty_msg, size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(value="När du bockar av uppgifter kommer de att sparas här.", size=11, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER)
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
                self.history_container.update()
            return

        # Group history items by date
        grouped_items = {}
        for item in items_to_render:
            try:
                item_date = history_date(item)
            except Exception:
                item_date = date.today()
            
            grouped_items.setdefault(item_date, []).append(item)

        # Sort dates in reverse (newest first)
        sorted_dates = sorted(grouped_items.keys(), reverse=True)

        for day in sorted_dates:
            day_items = grouped_items[day]
            day_items.sort(key=history_timestamp, reverse=True)
            
            date_header_str = self._format_swedish_date(day)
            
            section_header = ft.Container(
                content=ft.Text(
                    value=date_header_str.upper(),
                    size=11,
                    weight=ft.FontWeight.W_700,
                    color=TEXT_SECONDARY
                ),
                padding=ft.Padding(left=4, top=6, right=0, bottom=2)
            )
            self.history_container.controls.append(section_header)
            
            rows = []
            for idx, item in enumerate(day_items):
                category_color = EMERALD_GREEN if item.category == "Att göra" else "#8B5CF6"
                
                item_row = ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=MINT_GREEN, size=16),
                                ft.Container(
                                    content=ft.Text(
                                        value=item.title,
                                        size=12,
                                        color=TEXT_DISABLED,
                                        style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1
                                    ),
                                    expand=True
                                )
                            ],
                            expand=True,
                            spacing=8
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.REPLAY_ROUNDED,
                                    icon_color=MINT_GREEN,
                                    icon_size=14,
                                    tooltip="Återställ till checklistan",
                                    on_click=lambda e, itm=item: self._restore_item(itm),
                                    width=24,
                                    height=24,
                                    padding=0
                                )
                            ],
                            tight=True,
                            spacing=2
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
                
                rows.append(item_row)
                
                if idx < len(day_items) - 1:
                    rows.append(ft.Divider(height=1, color="#16261E", thickness=1))

            day_card = ft.Container(
                content=ft.Column(controls=rows, spacing=4, tight=True),
                **glass_card_style(padding=8, border_radius=10, border_color="#182A21")
            )
            self.history_container.controls.append(day_card)

        if self._is_mounted():
            self.history_container.update()

    def _format_swedish_date(self, target_date: date) -> str:
        """Formats a date into warm natural Swedish."""
        today = date.today()
        diff = (today - target_date).days
        
        if diff == 0:
            return "Idag"
        elif diff == 1:
            return "Igår"
        
        months = {
            1: "januari", 2: "februari", 3: "mars", 4: "april", 5: "maj", 6: "juni",
            7: "juli", 8: "augusti", 9: "september", 10: "oktober", 11: "november", 12: "december"
        }
        
        days_of_week = {
            0: "måndag", 1: "tisdag", 2: "onsdag", 3: "torsdag", 4: "fredag", 5: "lördag", 6: "söndag"
        }
        
        day_name = days_of_week[target_date.weekday()]
        month_name = months[target_date.month]
        
        return f"{day_name}, {target_date.day} {month_name}"

    def _restore_item(self, item: ChecklistItem):
        """Restores a completed item back to the active checklist (maintaining category)."""
        # 1. Remove from history
        self.history_list.items = [i for i in self.history_list.items if i.id != item.id]
        self.repo.save_checklist(self.history_list)
        
        # 2. Add back to active checklist (marked as unchecked)
        active_list = self.repo.get_checklist("active_list")
        if active_list:
            item.is_checked = False
            item.completed_at = None
            item.created_at = datetime.utcnow().isoformat() + "Z"
            active_list.items.append(item)
            self.repo.save_checklist(active_list)
            
        # 3. Reload views
        self._refresh_history()
        
        # 4. Trigger parent callback if registered
        if self.on_item_restored:
            self.on_item_restored()
