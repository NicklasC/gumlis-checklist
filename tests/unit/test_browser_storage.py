import tempfile
import unittest
from pathlib import Path

from src.repositories import browser_storage


class FakeBridge:
    def __init__(self, value=None, fail_get=False):
        self.value = value
        self.family_bootstrap = None
        self.fail_get = fail_get
        self.put_values = []
        self.put_soon_values = []

    async def get(self):
        if self.fail_get:
            raise RuntimeError("IndexedDB unavailable")
        return self.value

    async def put(self, value):
        self.put_values.append(value)

    def putSoon(self, value):
        self.put_soon_values.append(value)

    async def getFamilyBootstrap(self):
        return self.family_bootstrap

    async def putFamilyBootstrap(self, value):
        self.family_bootstrap = value

    async def deleteFamilyBootstrap(self):
        self.family_bootstrap = None


class BrowserStorageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        browser_storage.reset_storage_state()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.legacy_path = Path(self.temp_dir.name) / "checklists.json"

    def tearDown(self):
        browser_storage.reset_storage_state()
        self.temp_dir.cleanup()

    async def test_direct_value_skips_legacy_loader(self):
        legacy_called = False

        async def legacy_loader():
            nonlocal legacy_called
            legacy_called = True
            return True

        result = await browser_storage.prepare_browser_storage(
            legacy_loader, str(self.legacy_path), FakeBridge('{"direct":true}')
        )
        self.assertEqual(result, "direct")
        self.assertFalse(legacy_called)
        self.assertEqual(browser_storage.read_cached(), '{"direct":true}')

    async def test_confirmed_legacy_value_is_migrated(self):
        self.legacy_path.write_text('{"legacy":true}', encoding="utf-8")
        bridge = FakeBridge()

        async def legacy_loader():
            return True

        result = await browser_storage.prepare_browser_storage(
            legacy_loader, str(self.legacy_path), bridge
        )
        self.assertEqual(result, "migrated")
        self.assertEqual(bridge.put_values, ['{"legacy":true}'])
        self.assertEqual(browser_storage.read_cached(), '{"legacy":true}')

    async def test_confirmed_empty_legacy_store_enables_new_writes(self):
        bridge = FakeBridge()

        async def legacy_loader():
            return True

        result = await browser_storage.prepare_browser_storage(
            legacy_loader, str(self.legacy_path), bridge
        )
        self.assertEqual(result, "empty")
        self.assertTrue(browser_storage.write_cached('{"new":true}'))
        self.assertEqual(bridge.put_soon_values, ['{"new":true}'])

    async def test_unavailable_legacy_store_never_persists_defaults(self):
        bridge = FakeBridge()

        async def legacy_loader():
            return False

        result = await browser_storage.prepare_browser_storage(
            legacy_loader, str(self.legacy_path), bridge
        )
        self.assertEqual(result, "legacy-unavailable")
        self.assertFalse(browser_storage.write_cached('{"defaults":true}'))
        self.assertEqual(bridge.put_values, [])
        self.assertEqual(bridge.put_soon_values, [])

    async def test_migrated_session_writes_directly_afterward(self):
        self.legacy_path.write_text('{"legacy":true}', encoding="utf-8")
        bridge = FakeBridge()

        async def legacy_loader():
            return True

        await browser_storage.prepare_browser_storage(legacy_loader, str(self.legacy_path), bridge)
        self.assertTrue(browser_storage.write_cached('{"updated":true}'))
        self.assertEqual(bridge.put_soon_values, ['{"updated":true}'])

    async def test_direct_database_failure_keeps_legacy_data_read_only(self):
        self.legacy_path.write_text('{"legacy":true}', encoding="utf-8")
        bridge = FakeBridge(fail_get=True)

        async def legacy_loader():
            return True

        result = await browser_storage.prepare_browser_storage(
            legacy_loader, str(self.legacy_path), bridge
        )
        self.assertEqual(result, "legacy-read-only")
        self.assertEqual(browser_storage.read_cached(), '{"legacy":true}')
        self.assertFalse(browser_storage.write_cached('{"defaults":true}'))

    async def test_family_bootstrap_cache_uses_separate_storage_key(self):
        bridge = FakeBridge()

        async def legacy_loader():
            return True

        await browser_storage.prepare_browser_storage(legacy_loader, str(self.legacy_path), bridge)
        await browser_storage.write_family_bootstrap('{"tasks":[]}')

        self.assertEqual(await browser_storage.read_family_bootstrap(), '{"tasks":[]}')
        self.assertEqual(browser_storage.read_cached(), None)

    async def test_family_bootstrap_cache_can_be_removed_without_private_data(self):
        bridge = FakeBridge()

        async def legacy_loader():
            return True

        await browser_storage.prepare_browser_storage(legacy_loader, str(self.legacy_path), bridge)
        await browser_storage.write_family_bootstrap('{"tasks":[{"id":"family"}]}')
        await browser_storage.delete_family_bootstrap()

        self.assertIsNone(await browser_storage.read_family_bootstrap())
        self.assertIsNone(browser_storage.read_cached())
