from __future__ import annotations

import inspect
import uuid
from datetime import date

import flet as ft

from src.core.theme import MINT_GREEN, SURFACE_COLOR, TEXT_MUTED, TEXT_PRIMARY, border_all
from src.models.family import FAMILY_ASSIGNEES, FamilyTask, FamilyTaskDraft, FamilyTaskStatus


class FamilyTaskEditor(ft.AlertDialog):
    """Shared create/edit dialog for active family tasks."""

    def __init__(self, on_submit, on_action=None):
        self.on_submit = on_submit
        self.on_action = on_action
        self.task: FamilyTask | None = None
        self.pending_create_id: str | None = str(uuid.uuid4())
        self._available = True
        self._busy = False
        self.heading = ft.Text("Ny familjeuppgift", color=TEXT_PRIMARY)
        self.title_field = ft.TextField(
            label="Uppgift",
            hint_text="Vad behöver göras?",
            autofocus=True,
            max_length=200,
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=14),
            label_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            border_color="#294238",
            focused_border_color=MINT_GREEN,
        )
        self.assignee_label = ft.Text(
            "Ansvarig",
            size=12,
            color=TEXT_MUTED,
        )
        self.assignee_field = ft.RadioGroup(
            value="Alla",
            on_change=self._assignee_changed,
            content=ft.Row(
                controls=[
                    ft.Radio(
                        value=name,
                        label=name,
                        active_color=MINT_GREEN,
                        label_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
                    )
                    for name in FAMILY_ASSIGNEES
                ],
                spacing=6,
                run_spacing=0,
                wrap=True,
            ),
        )
        self.assignee_selector = ft.Container(
            content=ft.Column(
                controls=[self.assignee_label, self.assignee_field],
                spacing=2,
                tight=True,
            ),
            padding=ft.Padding(left=12, top=7, right=12, bottom=7),
            border=border_all(1.0, "#294238"),
            border_radius=4,
        )
        self.deadline_field = ft.TextField(
            label="Deadline (valfritt)",
            hint_text="ÅÅÅÅ-MM-DD",
            text_style=ft.TextStyle(color=TEXT_PRIMARY, size=14),
            label_style=ft.TextStyle(color=TEXT_MUTED, size=13),
            border_color="#294238",
            focused_border_color=MINT_GREEN,
            expand=True,
        )
        self.clear_deadline_button = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            tooltip="Ta bort deadline",
            icon_color=TEXT_MUTED,
            on_click=self._clear_deadline,
        )
        self.audit_text = ft.Text("", size=11, color=TEXT_MUTED, visible=False)
        self.error_text = ft.Text("", size=12, color="#F87171", visible=False)
        self.cancel_button = ft.TextButton(content=ft.Text("Avbryt"), on_click=self._cancel)
        self.move_button = ft.TextButton(
            content=ft.Text("Flytta till Senare"),
            on_click=self._move,
            visible=False,
        )
        self.delete_button = ft.TextButton(
            content=ft.Text("Radera", color="#F87171"),
            on_click=self._request_delete,
            visible=False,
        )
        self.save_button = ft.FilledButton(
            content=ft.Text("Skapa uppgift"),
            on_click=self._submit,
        )
        super().__init__(
            modal=True,
            title=self.heading,
            content=ft.Column(
                controls=[
                    self.title_field,
                    self.assignee_selector,
                    ft.Row(
                        controls=[self.deadline_field, self.clear_deadline_button],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.audit_text,
                    self.error_text,
                ],
                spacing=10,
                tight=True,
            ),
            actions=[self.delete_button, self.move_button, self.cancel_button, self.save_button],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE_COLOR,
            scrollable=True,
        )

    def prepare(self, task: FamilyTask | None = None) -> None:
        self._available = True
        self.task = task
        self.pending_create_id = None if task else str(uuid.uuid4())
        self.heading.value = "Redigera familjeuppgift" if task else "Ny familjeuppgift"
        self.save_button.content.value = "Spara ändringar" if task else "Skapa uppgift"
        self.title_field.value = task.title if task else ""
        self.assignee_field.value = task.assignee if task else "Alla"
        self.deadline_field.value = task.deadline.isoformat() if task and task.deadline else ""
        self.audit_text.value = self._audit_summary(task) if task else ""
        self.audit_text.visible = task is not None
        self.move_button.visible = task is not None and self.on_action is not None
        self.delete_button.visible = task is not None and self.on_action is not None
        if task is not None:
            self.move_button.content.value = (
                "Flytta till Aktuell"
                if task.status == FamilyTaskStatus.LATER
                else "Flytta till Senare"
            )
        self.set_error("")
        self.set_busy(False)

    @staticmethod
    def _audit_summary(task: FamilyTask) -> str:
        def format_time(value) -> str:
            local = value.astimezone()
            return f"{local.day}/{local.month} {local:%H:%M}"

        return "\n".join(
            [
                f"Skapad av {task.created_by} · {format_time(task.created_at)}",
                f"Tilldelad av {task.assigned_by} · {format_time(task.assigned_at)}",
                f"Senast ändrad av {task.updated_by} · {format_time(task.updated_at)}",
            ]
        )

    def draft(self) -> FamilyTaskDraft:
        raw_deadline = str(self.deadline_field.value or "").strip()
        parsed_deadline = None
        if raw_deadline:
            try:
                parsed_deadline = date.fromisoformat(raw_deadline)
            except ValueError as error:
                raise ValueError("Deadline ska anges som ÅÅÅÅ-MM-DD") from error
        return FamilyTaskDraft(
            title=str(self.title_field.value or ""),
            assignee=str(self.assignee_field.value or "Alla"),
            deadline=parsed_deadline,
        )

    def load_conflict(self, latest_task: FamilyTask) -> None:
        self.prepare(latest_task)
        self.set_error(
            f"Uppgiften ändrades av {latest_task.updated_by}. "
            "Senaste versionen har laddats – kontrollera och försök igen."
        )

    def set_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = bool(message)
        self._safe_update()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.save_button.disabled = busy or not self._available
        self.cancel_button.disabled = busy
        self.move_button.disabled = busy or not self._available
        self.delete_button.disabled = busy or not self._available
        if busy:
            self.save_button.content.value = "Sparar …"
        else:
            self.save_button.content.value = "Spara ändringar" if self.task else "Skapa uppgift"
        self._safe_update()

    def set_available(self, available: bool) -> None:
        """Block server mutations after an offline failure while keeping Cancel usable."""
        self._available = available
        self.set_busy(self._busy)

    async def _submit(self, _event=None) -> None:
        try:
            draft = self.draft()
        except ValueError as error:
            self.set_error(str(error))
            return
        self.set_error("")
        self.set_busy(True)
        try:
            result = self.on_submit(self.task, draft, self)
            if inspect.isawaitable(result):
                await result
        except Exception:
            self.set_error("Kunde inte spara uppgiften. Försök igen.")
        finally:
            self.set_busy(False)

    def close(self) -> None:
        try:
            if self.page is not None:
                self.page.pop_dialog()
        except (AttributeError, RuntimeError):
            pass

    def _cancel(self, _event=None) -> None:
        self.close()

    async def _move(self, _event=None) -> None:
        if self.task is None:
            return
        target = (
            FamilyTaskStatus.CURRENT
            if self.task.status == FamilyTaskStatus.LATER
            else FamilyTaskStatus.LATER
        )
        await self._run_action(target)

    def _request_delete(self, _event=None) -> None:
        if self.page is None or self.task is None:
            return
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Radera familjeuppgift"),
            content=ft.Text("Uppgiften tas bort från appen men raden sparas i familjearket."),
            actions=[
                ft.TextButton("Avbryt", on_click=lambda _event: self.page.pop_dialog()),
                ft.TextButton(
                    content=ft.Text("Radera uppgift", color="#F87171"),
                    on_click=self._confirm_delete,
                ),
            ],
        )
        self.page.show_dialog(dialog)

    async def _confirm_delete(self, _event=None) -> None:
        await self._run_action(FamilyTaskStatus.DELETED)
        # Keep the confirmation control mounted while its asynchronous action
        # is running. The parent action closes the top confirmation dialog;
        # this second pop then closes the editor underneath it.
        if self.page is not None:
            self.page.pop_dialog()

    async def _run_action(self, action: FamilyTaskStatus) -> None:
        if self.task is None or self.on_action is None:
            return
        self.set_error("")
        self.set_busy(True)
        try:
            result = self.on_action(self.task, action, self)
            if inspect.isawaitable(result):
                await result
        except Exception:
            self.set_error("Kunde inte ändra uppgiften. Försök igen.")
        finally:
            self.set_busy(False)

    def _clear_deadline(self, _event=None) -> None:
        self.deadline_field.value = ""
        self._safe_update()

    def _assignee_changed(self, event) -> None:
        selected = str(getattr(event, "data", "") or "").strip()
        if selected in FAMILY_ASSIGNEES:
            self.assignee_field.value = selected
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass
