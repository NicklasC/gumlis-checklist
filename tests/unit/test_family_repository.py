import json
import unittest

from src.repositories.family_repository import FamilyRepository


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

    async def test_disconnect_removes_persisted_connection(self):
        repo, storage, _ = self.make_repository({"ok": True, "member": "Thor"}, "saved")
        await repo.disconnect()
        self.assertIsNone(storage.value)

    async def test_invalid_local_state_does_not_make_network_request(self):
        repo, _, requests = self.make_repository({"ok": True, "member": "Ida"}, "not json")
        self.assertIsNone(await repo.resume())
        self.assertEqual(requests, [])
