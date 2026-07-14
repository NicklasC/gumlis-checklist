import os

from src.models.checklist import Checklist, ChecklistItem, CommonGroup
from tests.support.repository_case import RepositoryTestCase


class RepositoryInitializationTests(RepositoryTestCase):
    def test_creates_database_file(self):
        self.repository()
        self.assertTrue(os.path.isfile(self.db_path))

    def test_creates_exactly_three_standard_lists(self):
        self.assertEqual(len(self.repository().get_all_checklists()), 3)

    def test_creates_active_list(self):
        self.assertIsNotNone(self.repository().get_checklist("active_list"))

    def test_creates_later_list(self):
        self.assertIsNotNone(self.repository().get_checklist("later_list"))

    def test_creates_history_list(self):
        self.assertIsNotNone(self.repository().get_checklist("history_list"))

    def test_creates_private_favorites(self):
        groups = self.repository().get_all_common_groups()
        self.assertTrue(any(group.id == "todo_favorites" for group in groups))

    def test_creates_work_favorites(self):
        groups = self.repository().get_all_common_groups()
        self.assertTrue(any(group.id == "work_favorites" for group in groups))


class ChecklistCrudTests(RepositoryTestCase):
    def test_returns_none_for_unknown_checklist(self):
        self.assertIsNone(self.repository().get_checklist("missing"))

    def test_saves_new_checklist(self):
        repo = self.repository()
        repo.save_checklist(Checklist(id="custom", title="Custom"))
        self.assertEqual(repo.get_checklist("custom").title, "Custom")

    def test_updates_existing_checklist_without_duplicate(self):
        repo = self.repository()
        active = repo.get_checklist("active_list")
        active.title = "Updated"
        repo.save_checklist(active)
        matches = [entry for entry in repo.get_all_checklists() if entry.id == "active_list"]
        self.assertEqual(len(matches), 1)

    def test_persists_checklist_item(self):
        repo = self.repository()
        active = repo.get_checklist("active_list")
        active.items.append(ChecklistItem(id="one", title="Mjölka bröd", category="Att göra"))
        repo.save_checklist(active)
        self.assertEqual(repo.get_checklist("active_list").items[0].title, "Mjölka bröd")

    def test_deletes_checklist(self):
        repo = self.repository()
        repo.delete_checklist("later_list")
        self.assertIsNone(repo.get_checklist("later_list"))


class FavoriteGroupCrudTests(RepositoryTestCase):
    def test_saves_new_group(self):
        repo = self.repository()
        repo.save_common_group(CommonGroup(id="custom", name="Custom", items=["One"]))
        self.assertTrue(any(group.id == "custom" for group in repo.get_all_common_groups()))

    def test_updates_group_without_duplicate(self):
        repo = self.repository()
        group = next(group for group in repo.get_all_common_groups() if group.id == "todo_favorites")
        group.items.append("Ny")
        repo.save_common_group(group)
        matches = [entry for entry in repo.get_all_common_groups() if entry.id == group.id]
        self.assertEqual(len(matches), 1)

    def test_deletes_group(self):
        repo = self.repository()
        repo.delete_common_group("work_favorites")
        self.assertFalse(any(group.id == "work_favorites" for group in repo.get_all_common_groups()))


class RepositoryFileSafetyTests(RepositoryTestCase):
    def test_save_leaves_no_temporary_file(self):
        repo = self.repository()
        repo.save_checklist(Checklist(id="custom", title="Custom"))
        self.assertFalse(os.path.exists(self.db_path + ".tmp"))

    def test_empty_existing_file_can_be_read(self):
        with open(self.db_path, "w", encoding="utf-8"):
            pass
        checklists = self.repository().get_all_checklists()
        self.assertIsInstance(checklists, list)
