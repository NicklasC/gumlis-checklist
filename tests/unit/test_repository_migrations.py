from src.models.checklist import Checklist, ChecklistItem, ChecklistsData, CommonGroup
from tests.support.fixtures import PRIVATE, WORK
from tests.support.repository_case import RepositoryTestCase


class RepositoryMigrationTests(RepositoryTestCase):
    def migrated_repository(self):
        data = ChecklistsData(
            checklists=[Checklist(
                id="active_list",
                title="Active",
                category_order=["Inköp", "Planering"],
                items=[
                    ChecklistItem(id="old", title="Old", category="Inköp"),
                    ChecklistItem(id="work", title="Work", category=WORK),
                ],
            )],
            common_groups=[CommonGroup(id="legacy", name="Legacy", items=["Bevarad favorit"])],
        )
        self.write_data(data)
        return self.repository()

    def test_normalizes_category_order(self):
        self.assertEqual(self.migrated_repository().get_checklist("active_list").category_order, [PRIVATE, WORK])

    def test_migrates_unknown_item_category_to_private(self):
        items = self.migrated_repository().get_checklist("active_list").items
        self.assertEqual(next(item for item in items if item.id == "old").category, PRIVATE)

    def test_preserves_work_category(self):
        items = self.migrated_repository().get_checklist("active_list").items
        self.assertEqual(next(item for item in items if item.id == "work").category, WORK)

    def test_creates_missing_later_list(self):
        self.assertIsNotNone(self.migrated_repository().get_checklist("later_list"))

    def test_creates_missing_history_list(self):
        self.assertIsNotNone(self.migrated_repository().get_checklist("history_list"))

    def test_creates_exactly_two_supported_groups(self):
        self.assertEqual(len(self.migrated_repository().get_all_common_groups()), 2)

    def test_preserves_legacy_favorite_in_private_group(self):
        groups = self.migrated_repository().get_all_common_groups()
        private = next(group for group in groups if group.id == "todo_favorites")
        self.assertIn("Bevarad favorit", private.items)

    def test_does_not_duplicate_default_favorite(self):
        self.write_data(ChecklistsData(
            checklists=[Checklist(id="active_list", title="Active")],
            common_groups=[CommonGroup(id="legacy", name="Legacy", items=["Vattna blommorna"])],
        ))
        private = next(group for group in self.repository().get_all_common_groups() if group.id == "todo_favorites")
        self.assertEqual(private.items.count("Vattna blommorna"), 1)

    def test_current_data_stays_semantically_equal(self):
        repo = self.repository()
        before = repo.get_all_checklists()
        self.assertEqual(self.repository().get_all_checklists(), before)
