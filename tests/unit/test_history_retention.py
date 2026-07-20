from datetime import datetime, timedelta

from src.models.checklist import Checklist, ChecklistItem, ChecklistsData
from tests.support.repository_case import RepositoryTestCase


def history_item(item_id, created_at, completed_at=None):
    return ChecklistItem(
        id=item_id,
        title=item_id,
        category="Att göra",
        is_checked=True,
        created_at=created_at,
        completed_at=completed_at,
    )


class HistoryRetentionTests(RepositoryTestCase):
    def repository_with_items(self, items):
        self.write_data(ChecklistsData(checklists=[
            Checklist(id="active_list", title="Active"),
            Checklist(id="later_list", title="Later"),
            Checklist(id="history_list", title="History", items=items),
        ]))
        return self.repository()

    def remaining_ids(self, repo):
        return [item.id for item in repo.get_checklist("history_list").items]

    def test_removes_item_older_than_retention(self):
        old = (datetime.utcnow() - timedelta(days=15)).isoformat() + "Z"
        self.assertNotIn("old", self.remaining_ids(self.repository_with_items([history_item("old", old)])))

    def test_keeps_recent_item(self):
        recent = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        self.assertIn("recent", self.remaining_ids(self.repository_with_items([history_item("recent", recent)])))

    def test_keeps_item_just_inside_boundary(self):
        value = (datetime.utcnow() - timedelta(days=14) + timedelta(seconds=5)).isoformat() + "Z"
        self.assertIn("boundary", self.remaining_ids(self.repository_with_items([history_item("boundary", value)])))

    def test_removes_item_just_outside_boundary(self):
        value = (datetime.utcnow() - timedelta(days=14) - timedelta(seconds=5)).isoformat() + "Z"
        self.assertNotIn("boundary", self.remaining_ids(self.repository_with_items([history_item("boundary", value)])))

    def test_accepts_timestamp_without_z_suffix(self):
        recent = (datetime.utcnow() - timedelta(days=1)).isoformat()
        self.assertIn("recent", self.remaining_ids(self.repository_with_items([history_item("recent", recent)])))

    def test_keeps_item_with_invalid_timestamp(self):
        self.assertIn("invalid", self.remaining_ids(self.repository_with_items([history_item("invalid", "not-a-date")])))

    def test_removes_by_completion_time_instead_of_creation_time(self):
        recent_creation = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        old_completion = (datetime.utcnow() - timedelta(days=15)).isoformat() + "Z"
        value = history_item("completed-old", recent_creation, old_completion)
        self.assertNotIn("completed-old", self.remaining_ids(self.repository_with_items([value])))

    def test_keeps_by_completion_time_instead_of_creation_time(self):
        old_creation = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
        recent_completion = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        value = history_item("completed-recent", old_creation, recent_completion)
        self.assertIn("completed-recent", self.remaining_ids(self.repository_with_items([value])))
