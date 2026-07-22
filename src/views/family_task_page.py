from __future__ import annotations

import flet as ft

from src.core.theme import MINT_GREEN, TEXT_MUTED, TEXT_SECONDARY
from src.models.family import FamilyTaskPage, FamilyTaskStatus
from src.repositories.family_repository import FamilyVersionConflict
from src.views.family_current_view import FamilyTaskRow, OVERDUE_COLOR
from src.views.family_task_editor import FamilyTaskEditor


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
        self.editor = (
            FamilyTaskEditor(self._save_editor, self._task_action)
            if action == "listLater"
            else None
        )
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
        if self.action == "listHistory":
            tasks.sort(key=lambda task: task.completed_at, reverse=True)
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
            else [
                FamilyTaskRow(
                    task,
                    on_open=self._open_edit if self.action == "listLater" else None,
                    on_complete=(
                        self._start_completion if self.action == "listLater" else None
                    ),
                )
                for task in tasks
            ]
        )

    def _open_edit(self, task):
        if self.editor is None:
            return
        self.editor.prepare(task)
        try:
            if self.page is not None:
                self.page.show_dialog(self.editor)
        except (AttributeError, RuntimeError):
            pass

    def _start_completion(self, task):
        if self.page is not None:
            self.page.run_task(self._complete_task, task)

    async def _complete_task(self, task):
        try:
            saved = await self.repository.complete_task(task)
            self._upsert_task(saved)
            self._set_status("Uppgiften slutförd", MINT_GREEN)
        except FamilyVersionConflict as conflict:
            self._upsert_task(conflict.latest_task)
            self._set_status(
                f"Uppgiften ändrades av {conflict.latest_task.updated_by}",
                OVERDUE_COLOR,
            )
        except (ValueError, PermissionError, LookupError, TimeoutError) as error:
            self._set_status(str(error), OVERDUE_COLOR)
        except Exception:
            self._set_status("Kunde inte slutföra uppgiften. Försök igen.", OVERDUE_COLOR)

    async def _save_editor(self, task, draft, editor):
        try:
            saved = await self.repository.update_task(task, draft)
            self._upsert_task(saved)
            editor.close()
            self._set_status("Ändringar sparade", MINT_GREEN)
        except FamilyVersionConflict as conflict:
            self._upsert_task(conflict.latest_task)
            editor.load_conflict(conflict.latest_task)
        except (ValueError, PermissionError, LookupError, TimeoutError) as error:
            editor.set_error(str(error))
        except Exception:
            editor.set_error("Kunde inte spara uppgiften. Försök igen.")

    def _upsert_task(self, task):
        if self.task_page is None:
            return
        tasks = [existing for existing in self.task_page.tasks if existing.id != task.id]
        if task.status.value == "Senare":
            tasks.append(task)
        self.task_page = self.task_page.model_copy(update={"tasks": tasks})
        self._rebuild_filter_buttons()
        self._render_tasks()
        self._safe_update()

    async def _task_action(self, task, action, editor):
        try:
            saved = (
                await self.repository.delete_task(task)
                if action == FamilyTaskStatus.DELETED
                else await self.repository.change_status(task, action)
            )
            self._upsert_task(saved)
            editor.close()
            self._set_status(
                "Uppgiften raderad"
                if action == FamilyTaskStatus.DELETED
                else "Uppgiften flyttad",
                MINT_GREEN,
            )
        except FamilyVersionConflict as conflict:
            self._upsert_task(conflict.latest_task)
            editor.load_conflict(conflict.latest_task)
        except (ValueError, PermissionError, LookupError, TimeoutError) as error:
            editor.set_error(str(error))
        except Exception:
            editor.set_error("Kunde inte ändra uppgiften. Försök igen.")

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
