import json
import unittest
from datetime import date
from unittest.mock import AsyncMock

from src.models.family import FamilyTask, FamilyTaskDraft
from src.repositories.family_repository import FamilyRepository, FamilyVersionConflict


def mutation_task(**overrides):
    value = {
        "id": "family-1",
        "title": "Töm soporna",
        "status": "Aktuell",
        "assignee": "Alla",
        "assigned_by": "Nicklas",
        "assigned_at": "2026-07-20T18:00:00+02:00",
        "created_by": "Nicklas",
        "created_at": "2026-07-20T18:00:00+02:00",
        "deadline": None,
        "updated_by": "Nicklas",
        "updated_at": "2026-07-20T18:00:00+02:00",
        "completed_by": None,
        "completed_at": None,
        "version": 1,
    }
    value.update(overrides)
    return value


class FakeConnectionStorage:
    def __init__(self, value=None):
        self.value = value

    async def load(self):
        return self.value

    async def save(self, value):
        self.value = value

    async def delete(self):
        self.value = None


class FamilyRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def make_repository(self, response, stored=None):
        storage = FakeConnectionStorage(stored)
        requests = []

        async def transport(payload):
            requests.append(payload)
            return response

        repository = FamilyRepository(transport, storage.load, storage.save, storage.delete)
        return repository, storage, requests

    async def test_connect_verifies_and_persists_server_derived_member(self):
        repo, storage, requests = self.make_repository({"ok": True, "member": "Nicklas"})
        token = "n" * 48
        connection = await repo.connect(token)
        self.assertEqual(connection.member, "Nicklas")
        self.assertEqual(requests, [{"action": "ping", "deviceToken": token}])
        self.assertEqual(json.loads(storage.value)["member"], "Nicklas")

    async def test_connect_accepts_stable_response_envelope(self):
        response = {
            "ok": True,
            "data": {"member": "Nicklas"},
            "error": None,
            "server_time": "2026-07-20T19:00:00+02:00",
            "api_version": "family-v1",
        }
        repo, _, _ = self.make_repository(response)
        self.assertEqual((await repo.connect("n" * 48)).member, "Nicklas")

    async def test_wrong_key_is_not_persisted(self):
        repo, storage, _ = self.make_repository({"ok": False, "error": "UNAUTHORIZED"})
        with self.assertRaises(PermissionError):
            await repo.connect("x" * 48)
        self.assertIsNone(storage.value)

    async def test_connect_removes_mobile_clipboard_artifacts(self):
        repo, storage, requests = self.make_repository({"ok": True, "member": "Nicklas"})
        token = "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_-ab"
        connection = await repo.connect(f"`\u200b{token}\ufeff`\n")
        self.assertEqual(connection.device_token, token)
        self.assertEqual(requests, [{"action": "ping", "deviceToken": token}])
        self.assertEqual(json.loads(storage.value)["deviceToken"], token)

    async def test_resume_reuses_persisted_connection(self):
        token = "i" * 48
        stored = json.dumps({"deviceToken": token, "member": "Ida"})
        repo, _, requests = self.make_repository({"ok": True, "member": "Ida"}, stored)
        connection = await repo.resume()
        self.assertEqual(connection.member, "Ida")
        self.assertEqual(requests[0]["deviceToken"], token)

    async def test_bootstrap_parses_tasks_members_and_favorites(self):
        token = "n" * 48
        stored = json.dumps({"deviceToken": token, "member": "Nicklas"})
        response = {
            "ok": True,
            "data": {
                "tasks": [
                    {
                        "id": "family-1",
                        "title": "Töm soporna",
                        "status": "Aktuell",
                        "assignee": "Alla",
                        "assigned_by": "Nicklas",
                        "assigned_at": "2026-07-20T18:00:00+02:00",
                        "created_by": "Nicklas",
                        "created_at": "2026-07-20T18:00:00+02:00",
                        "deadline": None,
                        "updated_by": "Nicklas",
                        "updated_at": "2026-07-20T18:00:00+02:00",
                        "completed_by": None,
                        "completed_at": None,
                        "version": 1,
                    }
                ],
                "members": [{"name": "Nicklas", "active": True, "sort_order": 1}],
                "favorites": [],
                "invalidRows": [],
            },
            "error": None,
            "server_time": "2026-07-20T19:00:00+02:00",
            "api_version": "family-v1",
        }
        repo, _, requests = self.make_repository(response, stored)
        bootstrap = await repo.bootstrap()
        self.assertEqual(bootstrap.tasks[0].title, "Töm soporna")
        self.assertEqual(requests, [{"action": "bootstrap", "deviceToken": token}])

    async def test_bootstrap_persists_valid_cache(self):
        token = "t" * 48
        storage = FakeConnectionStorage(json.dumps({"deviceToken": token, "member": "Nicklas"}))
        cached = []

        async def transport(payload):
            return {
                "ok": True,
                "data": {"tasks": [], "members": [], "favorites": [], "invalidRows": []},
                "server_time": "2026-07-20T12:00:00+00:00",
            }

        async def save_cache(value):
            cached.append(value)

        repo = FamilyRepository(
            transport,
            storage.load,
            storage.save,
            storage.delete,
            save_bootstrap_cache=save_cache,
        )

        await repo.bootstrap()

        self.assertEqual(len(cached), 1)
        self.assertEqual(json.loads(cached[0])["tasks"], [])

    async def test_bootstrap_succeeds_when_cache_write_fails(self):
        token = "t" * 48
        storage = FakeConnectionStorage(json.dumps({"deviceToken": token, "member": "Nicklas"}))

        async def transport(payload):
            return {
                "ok": True,
                "data": {"tasks": [], "members": [], "favorites": [], "invalidRows": []},
                "server_time": "2026-07-20T12:00:00+00:00",
            }

        async def save_cache(value):
            raise RuntimeError("cache unavailable")

        repo = FamilyRepository(
            transport,
            storage.load,
            storage.save,
            storage.delete,
            save_bootstrap_cache=save_cache,
        )

        self.assertEqual((await repo.bootstrap()).tasks, [])

    async def test_cached_bootstrap_ignores_invalid_cache(self):
        storage = FakeConnectionStorage()

        async def load_cache():
            return "not-json"

        repo = FamilyRepository(
            AsyncMock(),
            storage.load,
            storage.save,
            storage.delete,
            load_bootstrap_cache=load_cache,
        )

        self.assertIsNone(await repo.cached_bootstrap())

    async def test_cached_bootstrap_restores_valid_cache_without_network(self):
        storage = FakeConnectionStorage()
        cached = json.dumps(
            {
                "tasks": [],
                "members": [],
                "favorites": [],
                "invalid_rows": [],
                "server_time": "2026-07-20T12:00:00+00:00",
            }
        )

        async def load_cache():
            return cached

        transport = AsyncMock()
        repo = FamilyRepository(
            transport,
            storage.load,
            storage.save,
            storage.delete,
            load_bootstrap_cache=load_cache,
        )

        restored = await repo.cached_bootstrap()

        self.assertIsNotNone(restored)
        self.assertEqual(restored.tasks, [])
        transport.assert_not_awaited()

    async def test_bootstrap_requires_connected_device(self):
        repo, _, requests = self.make_repository({"ok": True})
        with self.assertRaises(PermissionError):
            await repo.bootstrap()
        self.assertEqual(requests, [])

    async def test_list_later_and_history_use_separate_read_actions(self):
        token = "n" * 48
        stored = json.dumps({"deviceToken": token, "member": "Nicklas"})
        requests = []

        async def transport(payload):
            requests.append(payload)
            return {
                "ok": True,
                "data": {"tasks": [], "invalidRows": []},
                "server_time": "2026-07-20T12:00:00+00:00",
            }

        storage = FakeConnectionStorage(stored)
        repo = FamilyRepository(transport, storage.load, storage.save, storage.delete)

        self.assertEqual((await repo.list_later()).tasks, [])
        self.assertEqual((await repo.list_history()).tasks, [])
        self.assertEqual(
            requests,
            [
                {"action": "listLater", "deviceToken": token},
                {"action": "listHistory", "deviceToken": token},
            ],
        )

    async def test_create_task_sends_stable_id_without_member_identity(self):
        token = "n" * 48
        stored = json.dumps({"deviceToken": token, "member": "Nicklas"})
        repo, _, requests = self.make_repository(
            {"ok": True, "data": {"task": mutation_task()}},
            stored,
        )

        created = await repo.create_task(
            FamilyTaskDraft(title="Töm soporna", assignee="Ida", deadline=date(2026, 7, 28)),
            task_id="family-1",
        )

        self.assertEqual(created.id, "family-1")
        self.assertEqual(
            requests,
            [
                {
                    "action": "createTask",
                    "deviceToken": token,
                    "task": {
                        "id": "family-1",
                        "title": "Töm soporna",
                        "assignee": "Ida",
                        "deadline": "2026-07-28",
                    },
                }
            ],
        )
        self.assertNotIn("member", requests[0])

    async def test_update_task_sends_expected_version(self):
        token = "n" * 48
        stored = json.dumps({"deviceToken": token, "member": "Nicklas"})
        response_task = mutation_task(title="Gå med soporna", assignee="Thor", version=2)
        repo, _, requests = self.make_repository(
            {"ok": True, "data": {"task": response_task}},
            stored,
        )

        updated = await repo.update_task(
            FamilyTask.model_validate(mutation_task()),
            FamilyTaskDraft(title="Gå med soporna", assignee="Thor"),
        )

        self.assertEqual(updated.version, 2)
        self.assertEqual(requests[0]["task"]["version"], 1)
        self.assertNotIn("member", requests[0])

    async def test_update_task_exposes_latest_row_on_version_conflict(self):
        token = "n" * 48
        stored = json.dumps({"deviceToken": token, "member": "Nicklas"})
        latest = mutation_task(title="Redan ändrad", updated_by="Ida", version=2)
        repo, _, _ = self.make_repository(
            {
                "ok": False,
                "error": "VERSION_CONFLICT",
                "data": {"latestTask": latest},
            },
            stored,
        )

        with self.assertRaises(FamilyVersionConflict) as caught:
            await repo.update_task(
                FamilyTask.model_validate(mutation_task()),
                FamilyTaskDraft(title="Min ändring"),
            )

        self.assertEqual(caught.exception.latest_task.title, "Redan ändrad")
        self.assertEqual(caught.exception.latest_task.updated_by, "Ida")

    async def test_disconnect_removes_persisted_connection(self):
        repo, storage, _ = self.make_repository({"ok": True, "member": "Thor"}, "saved")
        await repo.disconnect()
        self.assertIsNone(storage.value)

    async def test_invalid_local_state_does_not_make_network_request(self):
        repo, _, requests = self.make_repository({"ok": True, "member": "Ida"}, "not json")
        self.assertIsNone(await repo.resume())
        self.assertEqual(requests, [])
