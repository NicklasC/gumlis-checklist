import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from threading import Lock

from src.core.config import JSON_DB_PATH, HISTORY_RETENTION_DAYS, DEFAULT_CATEGORIES
from src.core.repository import BaseRepository
from src.models.checklist import Checklist, ChecklistItem, CommonGroup, ChecklistsData
from src.core.time_utils import history_timestamp, timestamp_as_utc

logger = logging.getLogger(__name__)

class JsonChecklistRepository(BaseRepository):
    def __init__(self, db_path: str = JSON_DB_PATH):
        self.db_path = db_path
        self._lock = Lock()
        self._ensure_db_exists()
        self.purge_expired_history()

    def _ensure_db_exists(self) -> None:
        """Ensures that the JSON database file exists and is populated with initial structures."""
        with self._lock:
            if not os.path.exists(self.db_path):
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                
                # Initialize empty structure
                data = ChecklistsData(
                    checklists=[
                        Checklist(
                            id="active_list",
                            title="Min checklista",
                            is_template=False,
                            category_order=["Att göra", "Jobb"],
                            items=[]
                        ),
                        Checklist(
                            id="later_list",
                            title="Senare",
                            is_template=False,
                            category_order=["Att göra", "Jobb"],
                            items=[]
                        ),
                        Checklist(
                            id="history_list",
                            title="Historik",
                            is_template=False,
                            category_order=["Att göra", "Jobb"],
                            items=[]
                        )
                    ],
                    common_groups=[
                        CommonGroup(id="todo_favorites", name="Privat", items=["Vattna blommorna", "Morgonmeditation", "Bädda sängen", "Gå ut med soporna"]),
                        CommonGroup(id="work_favorites", name="Jobb", items=["Kolla e-post", "Planera arbetsdagen", "Rensa inkorgen", "Fika med kollegor"])
                    ]
                )
                self._save_to_file(data)
            else:
                # Ensure history and later lists exist in checklists
                try:
                    data = self._read_from_file()
                    
                    # Check / Migrate category order and items in checklists
                    modified = False
                    for checklist in data.checklists:
                        if checklist.category_order != ["Att göra", "Jobb"]:
                            checklist.category_order = ["Att göra", "Jobb"]
                            modified = True
                        for item in checklist.items:
                            if item.category not in ["Att göra", "Jobb"]:
                                item.category = "Att göra"
                                modified = True
                    
                    # Check / Migrate common groups
                    has_todo_fav = any(g.id == "todo_favorites" for g in data.common_groups)
                    has_work_fav = any(g.id == "work_favorites" for g in data.common_groups)
                    
                    if not has_todo_fav or not has_work_fav or len(data.common_groups) != 2:
                        # We need to migrate custom items from old groups to todo_favorites
                        old_items = []
                        for g in data.common_groups:
                            if g.id not in ["todo_favorites", "work_favorites"]:
                                old_items.extend(g.items)
                        
                        todo_items = ["Vattna blommorna", "Morgonmeditation", "Bädda sängen", "Gå ut med soporna"]
                        # Add any unique old items to todo_items so they are preserved!
                        for item in old_items:
                            if item not in todo_items:
                                todo_items.append(item)
                                
                        data.common_groups = [
                            CommonGroup(id="todo_favorites", name="Privat", items=todo_items),
                            CommonGroup(id="work_favorites", name="Jobb", items=["Kolla e-post", "Planera arbetsdagen", "Rensa inkorgen", "Fika med kollegor"])
                        ]
                        modified = True
                        
                    has_later = any(c.id == "later_list" for c in data.checklists)
                    has_history = any(c.id == "history_list" for c in data.checklists)
                    
                    if not has_later:
                        later_list = Checklist(
                            id="later_list",
                            title="Senare",
                            is_template=False,
                            category_order=["Att göra", "Jobb"],
                            items=[]
                        )
                        data.checklists.append(later_list)
                        modified = True
                        
                    if not has_history:
                        history_list = Checklist(
                            id="history_list",
                            title="Historik",
                            is_template=False,
                            category_order=["Att göra", "Jobb"],
                            items=[]
                        )
                        data.checklists.append(history_list)
                        modified = True
                        
                    if modified:
                        self._save_to_file(data)
                except Exception as e:
                    logger.error(f"Error checking/initializing DB: {e}")

    def _read_from_file(self) -> ChecklistsData:
        """Reads checklists data from the JSON file."""
        with open(self.db_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return ChecklistsData()
            return ChecklistsData.model_validate_json(content)

    def _save_to_file(self, data: ChecklistsData) -> None:
        """Saves checklists data to the JSON file safely using a temporary file."""
        temp_path = self.db_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(data.model_dump_json(indent=2))
            # Atomic replacement
            if os.path.exists(temp_path):
                os.replace(temp_path, self.db_path)
        except Exception as e:
            logger.error(f"Error saving to JSON file: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise e

    def get_all_checklists(self) -> List[Checklist]:
        with self._lock:
            data = self._read_from_file()
            # Filter out history checklist so it's not treated as a standard visible active list,
            # or keep it and manage it. Let's return all, and the client can filter.
            return data.checklists

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        with self._lock:
            data = self._read_from_file()
            for checklist in data.checklists:
                if checklist.id == checklist_id:
                    return checklist
            return None

    def save_checklist(self, checklist: Checklist) -> None:
        with self._lock:
            data = self._read_from_file()
            found = False
            for idx, c in enumerate(data.checklists):
                if c.id == checklist.id:
                    data.checklists[idx] = checklist
                    found = True
                    break
            if not found:
                data.checklists.append(checklist)
            self._save_to_file(data)

    def delete_checklist(self, checklist_id: str) -> None:
        with self._lock:
            data = self._read_from_file()
            data.checklists = [c for c in data.checklists if c.id != checklist_id]
            self._save_to_file(data)

    def get_all_common_groups(self) -> List[CommonGroup]:
        with self._lock:
            data = self._read_from_file()
            return data.common_groups

    def save_common_group(self, group: CommonGroup) -> None:
        with self._lock:
            data = self._read_from_file()
            found = False
            for idx, g in enumerate(data.common_groups):
                if g.id == group.id:
                    data.common_groups[idx] = group
                    found = True
                    break
            if not found:
                data.common_groups.append(group)
            self._save_to_file(data)

    def delete_common_group(self, group_id: str) -> None:
        with self._lock:
            data = self._read_from_file()
            data.common_groups = [g for g in data.common_groups if g.id != group_id]
            self._save_to_file(data)

    def purge_expired_history(self) -> None:
        """Purge completed/history items that are older than HISTORY_RETENTION_DAYS (14 days)."""
        with self._lock:
            data = self._read_from_file()
            history_checklist = None
            for checklist in data.checklists:
                if checklist.id == "history_list":
                    history_checklist = checklist
                    break
            
            if not history_checklist:
                return

            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=HISTORY_RETENTION_DAYS)
            
            original_count = len(history_checklist.items)
            retained_items = []
            
            for item in history_checklist.items:
                try:
                    item_dt = timestamp_as_utc(history_timestamp(item))
                    if item_dt is None or item_dt >= cutoff:
                        retained_items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing item date for item {item.id}: {e}")
                    # If date parsing fails, keep the item just to be safe
                    retained_items.append(item)
            
            if len(retained_items) < original_count:
                logger.info(f"Purged {original_count - len(retained_items)} expired history items.")
                history_checklist.items = retained_items
                self._save_to_file(data)
