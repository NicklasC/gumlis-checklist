"""Lazy repository for a device's private family connection."""

from __future__ import annotations

import json
from typing import Awaitable, Callable, Optional

from pydantic import ValidationError

from src.models.family import FAMILY_MEMBERS, FamilyBootstrap, FamilyConnection


Transport = Callable[[dict], Awaitable[dict]]
LoadConnection = Callable[[], Awaitable[Optional[str]]]
SaveConnection = Callable[[str], Awaitable[None]]
DeleteConnection = Callable[[], Awaitable[None]]
LoadBootstrapCache = Callable[[], Awaitable[Optional[str]]]
SaveBootstrapCache = Callable[[str], Awaitable[None]]


class FamilyRepository:
    _INVISIBLE_COPY_CHARACTERS = {"\u200b", "\u200c", "\u200d", "\ufeff"}

    def __init__(
        self,
        transport: Transport,
        load_connection: LoadConnection,
        save_connection: SaveConnection,
        delete_connection: DeleteConnection,
        load_bootstrap_cache: Optional[LoadBootstrapCache] = None,
        save_bootstrap_cache: Optional[SaveBootstrapCache] = None,
    ):
        self._transport = transport
        self._load_connection = load_connection
        self._save_connection = save_connection
        self._delete_connection = delete_connection
        self._load_bootstrap_cache = load_bootstrap_cache
        self._save_bootstrap_cache = save_bootstrap_cache

    @classmethod
    def web_default(cls) -> "FamilyRepository":
        from src.repositories import browser_storage, family_bridge

        return cls(
            transport=family_bridge.request,
            load_connection=browser_storage.read_family_connection,
            save_connection=browser_storage.write_family_connection,
            delete_connection=browser_storage.delete_family_connection,
            load_bootstrap_cache=browser_storage.read_family_bootstrap,
            save_bootstrap_cache=browser_storage.write_family_bootstrap,
        )

    async def connect(self, device_token: str) -> FamilyConnection:
        token = self._normalize_device_token(device_token)
        if len(token) < 32:
            raise ValueError("Kontrollera enhetsnyckeln och försök igen")
        response = await self._transport({"action": "ping", "deviceToken": token})
        connection = self._connection_from_response(token, response)
        await self._save(connection)
        return connection

    @classmethod
    def _normalize_device_token(cls, device_token: str) -> str:
        token = "".join(
            character
            for character in str(device_token or "")
            if not character.isspace() and character not in cls._INVISIBLE_COPY_CHARACTERS
        )
        if len(token) >= 2 and token[0] == token[-1] and token[0] in "`'\"":
            token = token[1:-1]
        return token

    async def resume(self) -> Optional[FamilyConnection]:
        connection = await self._stored_connection()
        if connection is None:
            return None

        response = await self._transport(
            {"action": "ping", "deviceToken": connection.device_token}
        )
        verified = self._connection_from_response(connection.device_token, response)
        if verified.member != connection.member:
            await self._save(verified)
        return verified

    async def bootstrap(self) -> FamilyBootstrap:
        connection = await self._stored_connection()
        if connection is None:
            raise PermissionError("Anslut enheten till Familj först")
        response = await self._transport(
            {"action": "bootstrap", "deviceToken": connection.device_token}
        )
        data = self._response_data(response)
        try:
            bootstrap = FamilyBootstrap.model_validate(
                {
                    "tasks": data.get("tasks", []),
                    "members": data.get("members", []),
                    "favorites": data.get("favorites", []),
                    "invalid_rows": data.get("invalidRows", []),
                    "server_time": response.get("server_time"),
                }
            )
            await self._save_bootstrap(bootstrap)
            return bootstrap
        except (AttributeError, TypeError, ValidationError) as error:
            raise ConnectionError("Familjen returnerade ogiltiga data") from error

    async def cached_bootstrap(self) -> Optional[FamilyBootstrap]:
        """Return the last valid family bootstrap without contacting the server."""
        if self._load_bootstrap_cache is None:
            return None
        try:
            raw = await self._load_bootstrap_cache()
            if not raw:
                return None
            return FamilyBootstrap.model_validate(json.loads(raw))
        except (TypeError, ValueError, json.JSONDecodeError, ValidationError):
            return None

    async def _save_bootstrap(self, bootstrap: FamilyBootstrap) -> None:
        if self._save_bootstrap_cache is None:
            return
        try:
            await self._save_bootstrap_cache(
                json.dumps(bootstrap.model_dump(mode="json"), ensure_ascii=False)
            )
        except Exception:
            # A cache write must never turn a successful live sync into an error.
            return

    async def disconnect(self) -> None:
        await self._delete_connection()

    async def _save(self, connection: FamilyConnection) -> None:
        await self._save_connection(
            json.dumps(
                {"deviceToken": connection.device_token, "member": connection.member},
                ensure_ascii=False,
            )
        )

    async def _stored_connection(self) -> Optional[FamilyConnection]:
        raw = await self._load_connection()
        if not raw:
            return None
        try:
            stored = json.loads(raw)
            return FamilyConnection(
                device_token=str(stored["deviceToken"]),
                member=str(stored["member"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _response_data(response: dict) -> dict:
        if not isinstance(response, dict) or not response.get("ok"):
            error = response.get("error") if isinstance(response, dict) else None
            if error == "UNAUTHORIZED":
                raise PermissionError("Enhetsnyckeln känns inte igen")
            if error == "INVALID_INPUT":
                raise ValueError("Familjen kunde inte läsa de angivna uppgifterna")
            raise ConnectionError("Familjen kunde inte nås just nu")
        data = response.get("data")
        if data is None:
            return response
        if not isinstance(data, dict):
            raise ConnectionError("Familjen returnerade ogiltiga data")
        return data

    @staticmethod
    def _connection_from_response(device_token: str, response: dict) -> FamilyConnection:
        data = FamilyRepository._response_data(response)
        member = str(data.get("member") or "")
        if member not in FAMILY_MEMBERS:
            raise ConnectionError("Servern returnerade en okänd familjemedlem")
        return FamilyConnection(device_token=device_token, member=member)
