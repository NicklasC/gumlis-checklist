"""Lazy repository for a device's private family connection."""

from __future__ import annotations

import json
import uuid
from typing import Awaitable, Callable, Optional

from pydantic import ValidationError

from src.models.family import (
    FAMILY_MEMBERS,
    FamilyBootstrap,
    FamilyConnection,
    FamilyTask,
    FamilyTaskDraft,
    FamilyTaskPage,
    FamilyTaskStatus,
)


Transport = Callable[[dict], Awaitable[dict]]
LoadConnection = Callable[[], Awaitable[Optional[str]]]
SaveConnection = Callable[[str], Awaitable[None]]
DeleteConnection = Callable[[], Awaitable[None]]
LoadBootstrapCache = Callable[[], Awaitable[Optional[str]]]
SaveBootstrapCache = Callable[[str], Awaitable[None]]


class FamilyVersionConflict(RuntimeError):
    def __init__(self, latest_task: FamilyTask):
        super().__init__("Uppgiften har ändrats på en annan enhet")
        self.latest_task = latest_task


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

    async def cache_bootstrap(self, bootstrap: FamilyBootstrap) -> None:
        await self._save_bootstrap(bootstrap)

    async def list_later(self) -> FamilyTaskPage:
        return await self._list_task_page("listLater")

    async def list_history(self) -> FamilyTaskPage:
        return await self._list_task_page("listHistory")

    async def create_task(
        self,
        draft: FamilyTaskDraft,
        task_id: Optional[str] = None,
    ) -> FamilyTask:
        connection = await self._require_connection()
        stable_id = str(task_id or uuid.uuid4()).strip()
        if not stable_id or len(stable_id) > 128:
            raise ValueError("Uppgiften har ett ogiltigt ID")
        response = await self._transport(
            {
                "action": "createTask",
                "deviceToken": connection.device_token,
                "task": {
                    "id": stable_id,
                    "title": draft.title,
                    "assignee": draft.assignee,
                    "deadline": draft.deadline.isoformat() if draft.deadline else None,
                },
            }
        )
        return self._mutation_task(response)

    async def update_task(self, task: FamilyTask, draft: FamilyTaskDraft) -> FamilyTask:
        connection = await self._require_connection()
        response = await self._transport(
            {
                "action": "updateTask",
                "deviceToken": connection.device_token,
                "task": {
                    "id": task.id,
                    "version": task.version,
                    "title": draft.title,
                    "assignee": draft.assignee,
                    "deadline": draft.deadline.isoformat() if draft.deadline else None,
                },
            }
        )
        return self._mutation_task(response)

    async def change_status(
        self,
        task: FamilyTask,
        status: FamilyTaskStatus,
    ) -> FamilyTask:
        if status not in (FamilyTaskStatus.CURRENT, FamilyTaskStatus.LATER):
            raise ValueError("Ogiltig statusändring")
        return await self._status_mutation("changeStatus", task, status=status)

    async def complete_task(self, task: FamilyTask) -> FamilyTask:
        return await self._status_mutation(
            "changeStatus",
            task,
            status=FamilyTaskStatus.COMPLETED,
        )

    async def delete_task(self, task: FamilyTask) -> FamilyTask:
        return await self._status_mutation("deleteTask", task)

    async def _status_mutation(
        self,
        action: str,
        task: FamilyTask,
        status: FamilyTaskStatus | None = None,
    ) -> FamilyTask:
        connection = await self._require_connection()
        payload = {"id": task.id, "version": task.version}
        if status is not None:
            payload["status"] = status.value
        response = await self._transport(
            {
                "action": action,
                "deviceToken": connection.device_token,
                "task": payload,
            }
        )
        return self._mutation_task(response)

    async def _list_task_page(self, action: str) -> FamilyTaskPage:
        connection = await self._require_connection()
        response = await self._transport(
            {"action": action, "deviceToken": connection.device_token}
        )
        data = self._response_data(response)
        try:
            return FamilyTaskPage.model_validate(
                {
                    "tasks": data.get("tasks", []),
                    "invalid_rows": data.get("invalidRows", []),
                    "server_time": response.get("server_time"),
                }
            )
        except (AttributeError, TypeError, ValidationError) as error:
            raise ConnectionError("Familjen returnerade ogiltiga data") from error

    async def _require_connection(self) -> FamilyConnection:
        connection = await self._stored_connection()
        if connection is None:
            raise PermissionError("Anslut enheten till Familj först")
        return connection

    @staticmethod
    def _mutation_task(response: dict) -> FamilyTask:
        if isinstance(response, dict) and response.get("error") == "VERSION_CONFLICT":
            data = response.get("data")
            latest = data.get("latestTask") if isinstance(data, dict) else None
            try:
                raise FamilyVersionConflict(FamilyTask.model_validate(latest))
            except FamilyVersionConflict:
                raise
            except (TypeError, ValidationError) as error:
                raise ConnectionError("Familjen returnerade en ogiltig konflikt") from error
        data = FamilyRepository._response_data(response)
        try:
            return FamilyTask.model_validate(data.get("task"))
        except (AttributeError, TypeError, ValidationError) as error:
            raise ConnectionError("Familjen returnerade en ogiltig uppgift") from error

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
            if error == "NOT_FOUND":
                raise LookupError("Uppgiften finns inte längre")
            if error == "TIMEOUT":
                raise TimeoutError("Familjen är upptagen – försök igen")
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
