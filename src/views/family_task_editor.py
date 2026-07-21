from __future__ import annotations

import inspect
import uuid
from datetime import date

import flet as ft

from src.core.theme import MINT_GREEN, SURFACE_COLOR, TEXT_MUTED, TEXT_PRIMARY
from src.models.family import FAMILY_ASSIGNEES, FamilyTask, FamilyTaskDraft


class FamilyTaskEditor(ft.AlertDialog):
    """Shared create/edit dialog for active family tasks."""

    def __init__(self, on_submit):
        self.on_submit = on_submit
        self.task: FamilyTask | None = None
        self.pending_create_id: str | None = str(uuid.uuid4())
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
        self.assignee_field = ft.Dropdown(
            label="Ansvarig",
            value="Alla",
            options=[ft.DropdownOption(key=name, text=name) for name in FAMILY_ASSIGNEES],
            border_color="#294238",
            focused_border_color=MINT_GREEN,
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
                    self.assignee_field,
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
            actions=[self.cancel_button, self.save_button],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=SURFACE_COLOR,
            scrollable=True,
        )

    def prepare(self, task: FamilyTask | None = None) -> None:
        self.task = task
        self.pending_create_id = None if task else str(uuid.uuid4())
        self.heading.value = "Redigera familjeuppgift" if task else "Ny familjeuppgift"
        self.save_button.content.value = "Spara ändringar" if task else "Skapa uppgift"
        self.title_field.value = task.title if task else ""
        self.assignee_field.value = task.assignee if task else "Alla"
        self.deadline_field.value = task.deadline.isoformat() if task and task.deadline else ""
        self.audit_text.value = self._audit_summary(task) if task else ""
        self.audit_text.visible = task is not None
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
        self.save_button.disabled = busy
        self.cancel_button.disabled = busy
        if busy:
            self.save_button.content.value = "Sparar …"
        else:
            self.save_button.content.value = "Spara ändringar" if self.task else "Skapa uppgift"
        self._safe_update()

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

    def _clear_deadline(self, _event=None) -> None:
        self.deadline_field.value = ""
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.update()
        except Exception:
            pass
