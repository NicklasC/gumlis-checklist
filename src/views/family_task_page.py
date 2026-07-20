from __future__ import annotations

import flet as ft

from src.core.theme import MINT_GREEN, TEXT_MUTED, TEXT_SECONDARY
from src.models.family import FamilyTaskPage
from src.views.family_current_view import FamilyTaskRow


class FamilyTaskPageView(ft.Container):
    """Shared read-only shell for Familjens Senare and Historik pages."""

    def __init__(self, repository, member: str, title: str, action: str, empty_text: str, *args, **kwargs):
        self.repository = repository
        self.member = member
        self.title = title
        self.action = action
        self.empty_text = empty_text
        self.task_page: FamilyTaskPage | None = None
        self.selected_filter = "Alla"
        self._sync_running = False

        self.status_text = ft.Text("", size=11, color=TEXT_MUTED)
        self.member_text = ft.Text(f"Ansluten som {member}", size=11, color=MINT_GREEN)
        self.filter_row = ft.Row(spacing=6, tight=True)
        self.list_container = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, expand=True)
        self._rebuild_filter_buttons()

        super().__init__(
            *args,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY),
                                    self.member_text,
                                ],
                                spacing=1,
                                tight=True,
                            ),
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
        if self.page is None or self._sync_running:
            return
        self._sync_running = True
        self.page.run_task(self._sync)

    async def _sync(self):
        self._set_status("Laddar …", TEXT_MUTED)
        try:
            self.task_page = await self._load_page()
            self._rebuild_filter_buttons()
            self._render_tasks()
            suffix = f" · {len(self.task_page.invalid_rows)} radfel" if self.task_page.invalid_rows else ""
            self._set_status(f"Synkad nyss{suffix}", MINT_GREEN)
        except Exception:
            self._set_status("Kunde inte synka Familj", "#F87171")
        finally:
            self._sync_running = False

    async def _load_page(self) -> FamilyTaskPage:
        if self.action == "listLater":
            return await self.repository.list_later()
        return await self.repository.list_history()

    def _visible_tasks(self):
        tasks = list(self.task_page.tasks if self.task_page else [])
        if self.selected_filter == "Mina":
            tasks = [task for task in tasks if task.assignee == self.member]
        return tasks

    def _rebuild_filter_buttons(self):
        all_count = len(self.task_page.tasks) if self.task_page else 0
        mine_count = (
            sum(task.assignee == self.member for task in self.task_page.tasks)
            if self.task_page
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
                bgcolor=ft.Colors.with_opacity(0.14 if self.selected_filter == name else 0.04, MINT_GREEN),
            ),
        )

    def _select_filter(self, value: str):
        self.selected_filter = value
        self._rebuild_filter_buttons()
        self._render_tasks()
        self._safe_update()

    def _render_tasks(self):
        tasks = self._visible_tasks()
        self.list_container.controls = (
            [ft.Text(self.empty_text, color=TEXT_MUTED, size=13)]
            if not tasks
            else [FamilyTaskRow(task) for task in tasks]
        )

    def _set_status(self, value: str, color: str):
        self.status_text.value = value
        self.status_text.color = color
        self._safe_update()

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass


class FamilyLaterView(FamilyTaskPageView):
    def __init__(self, repository, member: str, *args, **kwargs):
        super().__init__(
            repository,
            member,
            title="Familj – Senare",
            action="listLater",
            empty_text="Inga familjeuppgifter i Senare",
            *args,
            **kwargs,
        )


class FamilyHistoryView(FamilyTaskPageView):
    def __init__(self, repository, member: str, *args, **kwargs):
        super().__init__(
            repository,
            member,
            title="Familj – Historik",
            action="listHistory",
            empty_text="Ingen familjehistorik de senaste 14 dagarna",
            *args,
            **kwargs,
        )
