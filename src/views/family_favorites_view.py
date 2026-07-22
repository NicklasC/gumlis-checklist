from __future__ import annotations

import uuid

import flet as ft

from src.core.theme import (
    MINT_GREEN,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    glass_card_style,
)
from src.models.family import FamilyFavorite, FamilyTask, FamilyTaskDraft


class FamilyFavoriteButton(ft.Semantics):
    """Accessible, compact action for creating a task from one favorite."""

    def __init__(self, favorite: FamilyFavorite, on_create, disabled: bool = False):
        self.favorite = favorite
        self.action = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BOLT_ROUNDED, color=MINT_GREEN, size=19),
                    ft.Text(
                        favorite.title,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=TEXT_PRIMARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, color=TEXT_MUTED, size=20),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            disabled=disabled,
            on_click=(lambda _event: on_create(favorite)) if not disabled else None,
            **glass_card_style(padding=10, border_radius=10, border_color="#1C3328"),
        )
        super().__init__(
            label=f"Lägg till {favorite.title} för Alla",
            button=True,
            exclude_semantics=True,
            content=self.action,
        )


class FamilyFavoritesView(ft.Container):
    """Family favorites that create ordinary current tasks with one tap."""

    def __init__(self, repository, member: str, bootstrap_provider, *args, **kwargs):
        self.repository = repository
        self.member = member
        self.bootstrap_provider = bootstrap_provider
        self._sync_running = False
        self._creating_favorite_id: str | None = None
        self._pending_create_ids: dict[str, str] = {}
        self.status_text = ft.Text("", size=11, color=TEXT_MUTED)
        self.list_container = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, expand=True)
        super().__init__(
            *args,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Familj – Snabblistan",
                                        size=13,
                                        weight=ft.FontWeight.W_700,
                                        color=TEXT_SECONDARY,
                                    ),
                                    ft.Text(f"Ansluten som {member}", size=11, color=MINT_GREEN),
                                ],
                                spacing=1,
                                tight=True,
                            ),
                            self.status_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
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
            bootstrap = self.bootstrap_provider.bootstrap
            if bootstrap is None:
                bootstrap = await self.repository.bootstrap()
                self.bootstrap_provider._set_bootstrap(bootstrap)
            self._render_favorites()
            self._set_status("Synkad nyss", MINT_GREEN)
        except Exception:
            self._set_status("Kunde inte synka Familj", "#F87171")
        finally:
            self._sync_running = False
            self._safe_update()

    def _favorites(self) -> list[FamilyFavorite]:
        bootstrap = self.bootstrap_provider.bootstrap
        if bootstrap is None:
            return []
        return sorted(
            (favorite for favorite in bootstrap.favorites if favorite.active),
            key=lambda favorite: favorite.sort_order,
        )

    def _render_favorites(self):
        favorites = self._favorites()
        self.list_container.controls = (
            [ft.Text("Inga aktiva familjefavoriter", color=TEXT_MUTED, size=13)]
            if not favorites
            else [
                FamilyFavoriteButton(
                    favorite,
                    self._start_create,
                    disabled=self._creating_favorite_id is not None,
                )
                for favorite in favorites
            ]
        )

    def _start_create(self, favorite: FamilyFavorite):
        try:
            page = self.page
        except RuntimeError:
            return
        if self._creating_favorite_id is not None:
            return
        self._creating_favorite_id = favorite.id
        self._render_favorites()
        self._set_status("Lägger till …", TEXT_MUTED)
        page.run_task(self._create_from_favorite, favorite)

    async def _create_from_favorite(self, favorite: FamilyFavorite):
        if self._creating_favorite_id not in (None, favorite.id):
            return
        self._creating_favorite_id = favorite.id
        task_id = self._pending_create_ids.setdefault(favorite.id, str(uuid.uuid4()))
        try:
            saved = await self.repository.create_task(
                FamilyTaskDraft(title=favorite.title, assignee="Alla", deadline=None),
                task_id=task_id,
            )
            self.bootstrap_provider._upsert_task(saved)
            await self.repository.cache_bootstrap(self.bootstrap_provider.bootstrap)
            self._pending_create_ids.pop(favorite.id, None)
            self._set_status("Synkad nyss", MINT_GREEN)
            self._show_confirmation(saved)
        except (ValueError, PermissionError, LookupError, TimeoutError) as error:
            self._set_status(str(error), "#F87171")
        except Exception:
            self._set_status("Kunde inte lägga till uppgiften. Försök igen.", "#F87171")
        finally:
            self._creating_favorite_id = None
            self._render_favorites()
            self._safe_update()

    def _show_confirmation(self, task: FamilyTask):
        snack = ft.SnackBar(
            content=ft.Text("Tillagd för Alla", color=TEXT_PRIMARY),
            action=ft.SnackBarAction(
                label="Redigera",
                text_color=MINT_GREEN,
                on_click=lambda _event: self.bootstrap_provider._open_edit(task),
            ),
            bgcolor="#142C20",
            duration=5000,
            open=True,
        )
        try:
            page = self.page
            page.overlay.append(snack)
            page.update()
        except (AttributeError, RuntimeError):
            pass
        return snack

    def _set_status(self, value: str, color: str):
        self.status_text.value = value
        self.status_text.color = color
        self._safe_update()

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass
