import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.models.checklist import Checklist, CommonGroup
from src.repositories.client_storage_repo import ClientStorageRepository


class ClientStorageRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "data", "checklists.json")
        self.path_patch = patch("src.repositories.client_storage_repo.JSON_DB_PATH", self.db_path)
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.temp_dir.cleanup()

    def repository(self):
        return ClientStorageRepository(MagicMock())

    def test_initialization_creates_desktop_storage_file(self):
        self.repository()
        self.assertTrue(os.path.isfile(self.db_path))

    def test_initialization_writes_valid_json(self):
        self.repository()
        with open(self.db_path, encoding="utf-8") as handle:
            self.assertIsInstance(json.load(handle), dict)

    def test_missing_raw_storage_returns_none(self):
        repo = self.repository()
        os.remove(self.db_path)
        self.assertIsNone(repo._read_raw())

    def test_raw_round_trip_preserves_unicode(self):
        repo = self.repository()
        repo._write_raw('{"text":"räksmörgås"}')
        self.assertEqual(repo._read_raw(), '{"text":"räksmörgås"}')

    def test_corrupt_json_is_handled_as_empty_data(self):
        repo = self.repository()
        repo._write_raw("not-json")
        self.assertEqual(repo.get_all_checklists(), [])

    def test_saves_new_checklist(self):
        repo = self.repository()
        repo.save_checklist(Checklist(id="custom", title="Egen"))
        self.assertEqual(repo.get_checklist("custom").title, "Egen")

    def test_updates_checklist_without_duplicate(self):
        repo = self.repository()
        active = repo.get_checklist("active_list")
        active.title = "Ändrad"
        repo.save_checklist(active)
        matches = [item for item in repo.get_all_checklists() if item.id == "active_list"]
        self.assertEqual(len(matches), 1)

    def test_deletes_custom_checklist(self):
        repo = self.repository()
        repo.save_checklist(Checklist(id="custom", title="Egen"))
        repo.delete_checklist("custom")
        self.assertIsNone(repo.get_checklist("custom"))

    def test_returns_none_for_unknown_checklist(self):
        self.assertIsNone(self.repository().get_checklist("missing"))

    def test_saves_new_favorite_group_to_storage(self):
        repo = self.repository()
        repo.save_common_group(CommonGroup(id="custom", name="Egen", items=["En sak"]))
        raw = json.loads(repo._read_raw())
        self.assertTrue(any(group["id"] == "custom" for group in raw["common_groups"]))

    def test_updates_favorite_group_without_duplicate(self):
        repo = self.repository()
        group = next(group for group in repo.get_all_common_groups() if group.id == "todo_favorites")
        group.items.append("Ny favorit")
        repo.save_common_group(group)
        matches = [item for item in repo.get_all_common_groups() if item.id == group.id]
        self.assertEqual(len(matches), 1)

    def test_deleted_required_favorite_group_is_restored(self):
        repo = self.repository()
        repo.delete_common_group("work_favorites")
        self.assertTrue(any(group.id == "work_favorites" for group in repo.get_all_common_groups()))


if __name__ == "__main__":
    unittest.main()
