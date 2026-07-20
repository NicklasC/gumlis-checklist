from __future__ import annotations

import flet as ft

from src.core.theme import MINT_GREEN, TEXT_MUTED, TEXT_SECONDARY, glass_card_style


class FamilyFavoritesView(ft.Container):
    """Read-only family favorites page; creation is introduced in checkpoint 7."""

    def __init__(self, repository, member: str, bootstrap_provider, *args, **kwargs):
        self.repository = repository
        self.member = member
        self.bootstrap_provider = bootstrap_provider
        self._sync_running = False
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
                                    ft.Text("Familj – Snabblistan", size=13, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY),
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
        self.status_text.value = "Laddar …"
        try:
            bootstrap = self.bootstrap_provider.bootstrap
            if bootstrap is None:
                bootstrap = await self.repository.bootstrap()
                self.bootstrap_provider._set_bootstrap(bootstrap)
            favorites = sorted(bootstrap.favorites, key=lambda favorite: favorite.sort_order)
            self.list_container.controls = [
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(favorite.title, size=14, color=TEXT_MUTED),
                            ft.Text("Skapa i nästa steg", size=10, color=TEXT_MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    **glass_card_style(padding=10, border_radius=10, border_color="#1C3328"),
                )
                for favorite in favorites
            ] or [ft.Text("Inga aktiva familjefavoriter", color=TEXT_MUTED, size=13)]
            self.status_text.value = "Synkad nyss"
            self.status_text.color = MINT_GREEN
        except Exception:
            self.status_text.value = "Kunde inte synka Familj"
            self.status_text.color = "#F87171"
        finally:
            self._sync_running = False
            try:
                self.update()
            except Exception:
                pass
