"""Lazy repository for a device's private family connection."""

from __future__ import annotations

import json
from typing import Awaitable, Callable, Optional

from src.models.family import FAMILY_MEMBERS, FamilyConnection


Transport = Callable[[dict], Awaitable[dict]]
LoadConnection = Callable[[], Awaitable[Optional[str]]]
SaveConnection = Callable[[str], Awaitable[None]]
DeleteConnection = Callable[[], Awaitable[None]]


class FamilyRepository:
    def __init__(
        self,
        transport: Transport,
        load_connection: LoadConnection,
        save_connection: SaveConnection,
        delete_connection: DeleteConnection,
    ):
        self._transport = transport
        self._load_connection = load_connection
        self._save_connection = save_connection
        self._delete_connection = delete_connection

    @classmethod
    def web_default(cls) -> "FamilyRepository":
        from src.repositories import browser_storage, family_bridge

        return cls(
            transport=family_bridge.request,
            load_connection=browser_storage.read_family_connection,
            save_connection=browser_storage.write_family_connection,
            delete_connection=browser_storage.delete_family_connection,
        )

    async def connect(self, device_token: str) -> FamilyConnection:
        token = str(device_token or "").strip()
        if len(token) < 32:
            raise ValueError("Kontrollera enhetsnyckeln och försök igen")
        response = await self._transport({"action": "ping", "deviceToken": token})
        connection = self._connection_from_response(token, response)
        await self._save(connection)
        return connection

    async def resume(self) -> Optional[FamilyConnection]:
        raw = await self._load_connection()
        if not raw:
            return None
        try:
            stored = json.loads(raw)
            connection = FamilyConnection(
                device_token=str(stored["deviceToken"]),
                member=str(stored["member"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

        response = await self._transport(
            {"action": "ping", "deviceToken": connection.device_token}
        )
        verified = self._connection_from_response(connection.device_token, response)
        if verified.member != connection.member:
            await self._save(verified)
        return verified

    async def disconnect(self) -> None:
        await self._delete_connection()

    async def _save(self, connection: FamilyConnection) -> None:
        await self._save_connection(
            json.dumps(
                {"deviceToken": connection.device_token, "member": connection.member},
                ensure_ascii=False,
            )
        )

    @staticmethod
    def _connection_from_response(device_token: str, response: dict) -> FamilyConnection:
        if not isinstance(response, dict) or not response.get("ok"):
            error = response.get("error") if isinstance(response, dict) else None
            if error == "UNAUTHORIZED":
                raise PermissionError("Enhetsnyckeln känns inte igen")
            raise ConnectionError("Familjen kunde inte nås just nu")
        member = str(response.get("member") or "")
        if member not in FAMILY_MEMBERS:
            raise ConnectionError("Servern returnerade en okänd familjemedlem")
        return FamilyConnection(device_token=device_token, member=member)
