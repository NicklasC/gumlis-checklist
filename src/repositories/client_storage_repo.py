import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import flet as ft

from src.core.config import JSON_DB_PATH, HISTORY_RETENTION_DAYS
from src.core.repository import BaseRepository
from src.models.checklist import Checklist, CommonGroup, ChecklistsData, ChecklistItem

import sys

logger = logging.getLogger(__name__)

# Detect Web/Pyodide environment to access browser storage directly and safely via Flet!
IS_WEB = sys.platform == 'emscripten'

def web_log(msg):
    print(msg)
    if IS_WEB:
        try:
            import js
            js.console.log(msg)
        except Exception:
            pass

class ClientStorageRepository(BaseRepository):
    def __init__(self, page: ft.Page):
        self.page = page
        # File fallback for local desktop running
        self.desktop_file_path = JSON_DB_PATH
        web_log(f"[REPOSITORIES] Repo init. IS_WEB: {IS_WEB}")
        self._ensure_db_exists()
        self.purge_expired_history()

    def _read_raw(self) -> Optional[str]:
        """Reads raw JSON string from either browser client_storage (web) or local file (desktop)."""
        if IS_WEB:
            # Reads directly from the persistent IDBFS virtual filesystem (already loaded at startup!)
            web_log(f"[REPOSITORIES] Reading persistent virtual file. Path: {self.desktop_file_path}")
            if os.path.exists(self.desktop_file_path):
                try:
                    with open(self.desktop_file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        web_log(f"[REPOSITORIES] Persistent virtual file read success. Length: {len(content)}")
                        return content
                except Exception as e:
                    web_log(f"[REPOSITORIES] Error reading persistent virtual file: {e}")
            else:
                web_log("[REPOSITORIES] Persistent virtual file does not exist yet.")
            return None
        else:
            if os.path.exists(self.desktop_file_path):
                try:
                    with open(self.desktop_file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading from local desktop file: {e}")
                    return None
            return None

    def _write_raw(self, content: str) -> None:
        """Writes raw JSON string to either browser client_storage (web) or local file (desktop)."""
        if IS_WEB:
            # Writes directly to the persistent IDBFS virtual filesystem
            try:
                web_log(f"[REPOSITORIES] Writing persistent virtual file. Path: {self.desktop_file_path}")
                os.makedirs(os.path.dirname(self.desktop_file_path), exist_ok=True)
                with open(self.desktop_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                web_log("[REPOSITORIES] Persistent virtual file write success.")
                
                # Asynchronously sync the written file from MEMFS back to IndexedDB (fire-and-forget!)
                import js
                import pyodide
                
                # Resolve the Emscripten FS object robustly
                FS = None
                try:
                    import pyodide_js
                    if hasattr(pyodide_js, "FS"):
                        FS = pyodide_js.FS
                except ImportError:
                    pass
                    
                if not FS:
                    try:
                        if hasattr(js, "pyodide") and hasattr(js.pyodide, "FS"):
                            FS = js.pyodide.FS
                    except Exception:
                        pass
                        
                if not FS:
                    try:
                        if hasattr(js, "FS"):
                            FS = js.FS
                    except Exception:
                        pass
                        
                if not FS:
                    web_log("[REPOSITORIES] Critical Error: Emscripten FS object could not be resolved for syncfs write!")
                    return
                
                def sync_write_callback(err):
                    if err:
                        web_log(f"[REPOSITORIES] syncfs write failed: {err}")
                    else:
                        web_log("[REPOSITORIES] syncfs write successfully saved to IndexedDB!")
                
                proxy = pyodide.ffi.create_proxy(sync_write_callback)
                FS.syncfs(False, proxy)
                
            except Exception as e:
                web_log(f"[REPOSITORIES] Error writing persistent virtual file / syncfs: {e}")
                try:
                    import traceback
                    traceback.print_exc()
                    import pyodide
                    if isinstance(e, pyodide.ffi.JsException):
                        web_log(f"[REPOSITORIES] JS Error Name: {e.name}")
                        web_log(f"[REPOSITORIES] JS Error Message: {e.message}")
                        web_log(f"[REPOSITORIES] JS Error Stack: {e.stack}")
                except Exception as e2:
                    web_log(f"[REPOSITORIES] Failed to extract JS error details: {e2}")
        else:
            try:
                os.makedirs(os.path.dirname(self.desktop_file_path), exist_ok=True)
                with open(self.desktop_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error writing to local desktop file: {e}")

    def _ensure_db_exists(self) -> None:
        """Ensures the storage exists and is populated with default structures if empty."""
        try:
            content = self._read_raw()
            if not content:
                # Initialize empty structure with default templates and groups
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
                self._save(data)
            else:
                # Ensure history_list and later_list exist for backwards compatibility
                try:
                    data = ChecklistsData.model_validate_json(content)
                except Exception:
                    # In case of validation issues, recreate defaults
                    return
                
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
                    self._save(data)
            self._db_ensured = True
        except Exception as e:
            logger.error(f"Error initializing database storage: {e}")

    def _read(self) -> ChecklistsData:
        self._ensure_db_exists()
        try:
            content = self._read_raw()
            if not content:
                return ChecklistsData()
            return ChecklistsData.model_validate_json(content)
        except Exception as e:
            logger.error(f"Error parsing database checklists: {e}")
            return ChecklistsData()

    def _save(self, data: ChecklistsData) -> None:
        try:
            self._write_raw(data.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error stringifying database checklists: {e}")

    def get_all_checklists(self) -> List[Checklist]:
        data = self._read()
        return data.checklists

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        data = self._read()
        for checklist in data.checklists:
            if checklist.id == checklist_id:
                return checklist
        return None

    def save_checklist(self, checklist: Checklist) -> None:
        data = self._read()
        found = False
        for idx, c in enumerate(data.checklists):
            if c.id == checklist.id:
                data.checklists[idx] = checklist
                found = True
                break
        if not found:
            data.checklists.append(checklist)
        self._save(data)

    def delete_checklist(self, checklist_id: str) -> None:
        data = self._read()
        data.checklists = [c for c in data.checklists if c.id != checklist_id]
        self._save(data)

    def get_all_common_groups(self) -> List[CommonGroup]:
        data = self._read()
        return data.common_groups

    def save_common_group(self, group: CommonGroup) -> None:
        data = self._read()
        found = False
        for idx, g in enumerate(data.common_groups):
            if g.id == group.id:
                data.common_groups[idx] = group
                found = True
                break
        if not found:
            data.common_groups.append(group)
        self._save(data)

    def delete_common_group(self, group_id: str) -> None:
        data = self._read()
        data.common_groups = [g for g in data.common_groups if g.id != group_id]
        self._save(data)

    def purge_expired_history(self) -> None:
        """Purge completed/history items that are older than HISTORY_RETENTION_DAYS (14 days)."""
        try:
            data = self._read()
            history_checklist = None
            for checklist in data.checklists:
                if checklist.id == "history_list":
                    history_checklist = checklist
                    break
            
            if not history_checklist:
                return

            now = datetime.utcnow()
            cutoff = now - timedelta(days=HISTORY_RETENTION_DAYS)
            
            original_count = len(history_checklist.items)
            retained_items = []
            
            for item in history_checklist.items:
                try:
                    dt_str = item.created_at
                    if dt_str.endswith("Z"):
                        dt_str = dt_str[:-1]
                    
                    item_dt = datetime.fromisoformat(dt_str)
                    
                    if item_dt >= cutoff:
                        retained_items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing item date {item.created_at} for item {item.id}: {e}")
                    retained_items.append(item)
            
            if len(retained_items) < original_count:
                logger.info(f"Purged {original_count - len(retained_items)} expired history items.")
                history_checklist.items = retained_items
                self._save(data)
        except Exception as e:
            logger.error(f"Error purging expired history: {e}")

