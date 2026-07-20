from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.models.checklist import Checklist, ChecklistItem, ChecklistsData, CommonGroup

PRIVATE = "Att göra"
WORK = "Jobb"


def item(item_id, title, *, category=PRIVATE, checked=False, age_days=0, completed_at=None):
    created = datetime.utcnow() - timedelta(days=age_days)
    return ChecklistItem(
        id=item_id,
        title=title,
        category=category,
        is_checked=checked,
        created_at=created.isoformat() + "Z",
        completed_at=completed_at,
    )


def default_data():
    return ChecklistsData(
        checklists=[
            Checklist(id="active_list", title="Min checklista", category_order=[PRIVATE, WORK]),
            Checklist(id="later_list", title="Senare", category_order=[PRIVATE, WORK]),
            Checklist(id="history_list", title="Historik", category_order=[PRIVATE, WORK]),
        ],
        common_groups=[
            CommonGroup(id="todo_favorites", name="Privat", items=["Vattna blommorna"]),
            CommonGroup(id="work_favorites", name="Jobb", items=["Kolla e-post"]),
        ],
    )


class InMemoryRepository:
    def __init__(self, data=None):
        source = data or default_data()
        self.checklists = {entry.id: deepcopy(entry) for entry in source.checklists}
        self.groups = {entry.id: deepcopy(entry) for entry in source.common_groups}
        self.saved_checklist_ids = []
        self.saved_group_ids = []

    def get_all_checklists(self):
        return list(self.checklists.values())

    def get_checklist(self, checklist_id):
        return self.checklists.get(checklist_id)

    def save_checklist(self, checklist):
        self.checklists[checklist.id] = checklist
        self.saved_checklist_ids.append(checklist.id)

    def delete_checklist(self, checklist_id):
        self.checklists.pop(checklist_id, None)

    def get_all_common_groups(self):
        return list(self.groups.values())

    def save_common_group(self, group):
        self.groups[group.id] = group
        self.saved_group_ids.append(group.id)

    def delete_common_group(self, group_id):
        self.groups.pop(group_id, None)


@dataclass
class StubMainView:
    current_mode: str = PRIVATE
