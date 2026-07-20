from __future__ import annotations

from datetime import date

import flet as ft

from src.core.theme import (
    MINT_GREEN,
    SURFACE_GLASS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    border_all,
    glass_card_style,
)
from src.models.family import FamilyBootstrap, FamilyTask


OVERDUE_COLOR = "#F87171"


def family_task_sort_key(task: FamilyTask, today: date | None = None):
    """Sort active family tasks by urgency, then by stable creation order."""
    current_day = today or date.today()
    if task.deadline is None:
        return (3, date.max, task.created_at)
    if task.deadline < current_day:
        return (0, task.deadline, task.created_at)
    if task.deadline == current_day:
        return (1, task.deadline, task.created_at)
    return (2, task.deadline, task.created_at)


def family_deadline_text(task: FamilyTask, today: date | None = None) -> tuple[str, bool]:
    """Return a compact Swedish deadline label and whether it is overdue."""
    if task.deadline is None:
        return "", False
    current_day = today or date.today()
    days_late = (current_day - task.deadline).days
    if days_late > 0:
        suffix = "dag" if days_late == 1 else "dagar"
        return f"Försenad {days_late} {suffix}", True
    if days_late == 0:
        return "Idag", False
    return f"Deadline {task.deadline.day}/{task.deadline.month}", False


class FamilyTaskRow(ft.Container):
    """Compact, read-only task row for the first family list checkpoint."""

    def __init__(self, task: FamilyTask, today: date | None = None, *args, **kwargs):
        self.task = task
        deadline, overdue = family_deadline_text(task, today=today)
        self.title_text = ft.Text(
            task.title,
            size=14,
            weight=ft.FontWeight.W_600,
            color=TEXT_PRIMARY,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.assignee_text = ft.Text(
            f"Ansvarig: {task.assignee}",
            size=11,
            color=TEXT_SECONDARY,
        )
        self.deadline_text = ft.Text(
            deadline,
            size=11,
            color=OVERDUE_COLOR if overdue else TEXT_MUTED,
            weight=ft.FontWeight.W_600 if overdue else ft.FontWeight.W_400,
            visible=bool(deadline),
        )
        metadata = [self.assignee_text]
        if deadline:
            metadata.append(self.deadline_text)
        row_style = glass_card_style(padding=8, border_radius=10, border_color="#1C3328")
        super().__init__(
            *args,
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[self.title_text, ft.Row(controls=metadata, spacing=10)],
                            spacing=2,
                            tight=True,
                        ),
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.WARNING_AMBER_ROUNDED if overdue else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                        color=OVERDUE_COLOR if overdue else TEXT_MUTED,
                        size=18,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **row_style,
            **kwargs,
        )


class FamilyCurrentView(ft.Container):
    """Cached, synchronizing read-only Aktuell view for Familj checkpoint 3A."""

    def __init__(self, repository, member: str, *args, **kwargs):
        self.repository = repository
        self.member = member
        self.bootstrap: FamilyBootstrap | None = None
        self.selected_filter = "Alla"
        self._sync_running = False

        self.status_text = ft.Text("", size=11, color=TEXT_MUTED)
        self.member_text = ft.Text(f"Ansluten som {member}", size=11, color=MINT_GREEN)
        self.header_text = ft.Text(
            "Familjeuppgifter",
            size=13,
            weight=ft.FontWeight.W_700,
            color=TEXT_SECONDARY,
        )
        self.filter_row = ft.Row(spacing=6, tight=True)
        self.list_container = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, expand=True)
        self._rebuild_filter_buttons()

        super().__init__(
            *args,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(controls=[self.header_text, self.member_text], spacing=1, tight=True),
                            self.status_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.filter_row,
                    self.list_container,
                ],
                spacing=8,
                expand=True,
            ),
            padding=ft.Padding(left=12, top=4, right=12, bottom=6),
            expand=True,
            **kwargs,
        )

    def activate(self):
        if self._sync_running or self.page is None:
            return
        self._sync_running = True
        self.page.run_task(self._sync)

    async def _sync(self):
        try:
            cached = await self.repository.cached_bootstrap()
            if cached is not None:
                self._set_bootstrap(cached)
                self._set_status("Synkar …", TEXT_MUTED)
            else:
                self._set_status("Laddar Familj …", TEXT_MUTED)
            try:
                bootstrap = await self.repository.bootstrap()
                self._set_bootstrap(bootstrap)
                suffix = f" · {len(bootstrap.invalid_rows)} radfel" if bootstrap.invalid_rows else ""
                self._set_status(f"Synkad nyss{suffix}", MINT_GREEN)
            except Exception:
                if cached is not None:
                    self._set_status("Offline – visar sparad data", OVERDUE_COLOR)
                else:
                    self._set_status("Kunde inte synka Familj", OVERDUE_COLOR)
        finally:
            self._sync_running = False

    def _set_bootstrap(self, bootstrap: FamilyBootstrap):
        self.bootstrap = bootstrap
        self._rebuild_filter_buttons()
        self._render_tasks()

    def _visible_tasks(self) -> list[FamilyTask]:
        tasks = list(self.bootstrap.tasks if self.bootstrap else [])
        if self.selected_filter == "Mina":
            tasks = [task for task in tasks if task.assignee == self.member]
        return sorted(tasks, key=family_task_sort_key)

    def _rebuild_filter_buttons(self):
        all_count = len(self.bootstrap.tasks) if self.bootstrap else 0
        mine_count = (
            sum(task.assignee == self.member for task in self.bootstrap.tasks)
            if self.bootstrap
            else 0
        )
        self.filter_row.controls = [
            self._filter_button("Alla", all_count),
            self._filter_button("Mina", mine_count),
        ]

    def _filter_button(self, name: str, count: int):
        return ft.TextButton(
            content=ft.Text(f"{name} ({count})", size=11),
            on_click=lambda _event, value=name: self._select_filter(value),
            style=ft.ButtonStyle(
                color=MINT_GREEN if self.selected_filter == name else TEXT_MUTED,
                bgcolor=ft.Colors.with_opacity(
                    0.14 if self.selected_filter == name else 0.04,
                    MINT_GREEN,
                ),
                side=border_all(1, "#254337"),
                padding=ft.Padding(left=10, top=5, right=10, bottom=5),
            ),
        )

    def _select_filter(self, value: str):
        self.selected_filter = value
        self._rebuild_filter_buttons()
        self._render_tasks()
        self._safe_update()

    def _render_tasks(self):
        tasks = self._visible_tasks()
        if not tasks:
            empty_text = "Inga familjeuppgifter i Aktuell"
            if self.selected_filter == "Mina":
                empty_text = "Du har inga tilldelade familjeuppgifter"
            self.list_container.controls = [ft.Text(empty_text, color=TEXT_MUTED, size=13)]
        else:
            self.list_container.controls = [FamilyTaskRow(task) for task in tasks]

    def _set_status(self, value: str, color: str):
        self.status_text.value = value
        self.status_text.color = color
        self._safe_update()

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass
