import os
import sys
import unittest
from datetime import datetime, timedelta
import tempfile
import shutil
from unittest.mock import MagicMock, PropertyMock, patch

# Ensure the root of the project is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.checklist import Checklist, ChecklistItem, CommonGroup, ChecklistsData
from src.repositories.json_repo import JsonChecklistRepository
from src.views.templates_view import TemplatesView

class TestChecklistApp(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_checklists.json")
        
    def tearDown(self):
        # Remove temporary directory after tests
        shutil.rmtree(self.temp_dir)

    def test_repository_initialization(self):
        """Verify that repository initializes with default checklist structure."""
        repo = JsonChecklistRepository(db_path=self.db_path)
        
        # Should have active_list, later_list, and history_list
        checklists = repo.get_all_checklists()
        self.assertEqual(len(checklists), 3)
        
        active = repo.get_checklist("active_list")
        self.assertIsNotNone(active)
        self.assertEqual(active.title, "Min checklista")
        self.assertEqual(active.category_order, ["Att göra", "Jobb"])
        
        later = repo.get_checklist("later_list")
        self.assertIsNotNone(later)
        self.assertEqual(later.title, "Senare")
        
        history = repo.get_checklist("history_list")
        self.assertIsNotNone(history)
        self.assertEqual(history.title, "Historik")

    def test_save_and_retrieve_checklist(self):
        """Verify saving and retrieving checklists."""
        repo = JsonChecklistRepository(db_path=self.db_path)
        active = repo.get_checklist("active_list")
        
        # Add an item
        item = ChecklistItem(id="test_1", title="Mjöla bröd", is_checked=False, category="Att göra")
        active.items.append(item)
        repo.save_checklist(active)
        
        # Re-fetch
        fetched = repo.get_checklist("active_list")
        self.assertEqual(len(fetched.items), 1)
        self.assertEqual(fetched.items[0].title, "Mjöla bröd")
        self.assertEqual(fetched.items[0].category, "Att göra")

    def test_history_purging(self):
        """Verify that history items older than 14 days are automatically purged on startup."""
        # Setup initial DB file with custom dates
        now = datetime.utcnow()
        old_date = now - timedelta(days=15)
        new_date = now - timedelta(days=5)
        
        old_item = ChecklistItem(
            id="old_item",
            title="Gamla städa",
            is_checked=True,
            category="Att göra",
            created_at=old_date.isoformat() + "Z"
        )
        
        new_item = ChecklistItem(
            id="new_item",
            title="Nya städa",
            is_checked=True,
            category="Att göra",
            created_at=new_date.isoformat() + "Z"
        )
        
        # Write directly to test DB path
        data = ChecklistsData(
            checklists=[
                Checklist(id="active_list", title="Active", items=[]),
                Checklist(id="history_list", title="Historik", items=[old_item, new_item])
            ],
            common_groups=[]
        )
        
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write(data.model_dump_json(indent=2))
            
        # Instantiating repo triggers the purge automatically
        repo = JsonChecklistRepository(db_path=self.db_path)
        
        # Verify history checklist items
        history = repo.get_checklist("history_list")
        self.assertEqual(len(history.items), 1)
        self.assertEqual(history.items[0].id, "new_item")

    def test_delete_common_group(self):
        """Verify that a common group can be deleted successfully."""
        repo = JsonChecklistRepository(db_path=self.db_path)
        groups = repo.get_all_common_groups()
        original_count = len(groups)
        
        # Add a temporary group
        new_group = CommonGroup(id="test_group_delete", name="Temporary Group", items=["Item 1"])
        repo.save_common_group(new_group)
        
        # Check added
        self.assertEqual(len(repo.get_all_common_groups()), original_count + 1)
        
        # Delete
        repo.delete_common_group("test_group_delete")
        
        # Check deleted
        self.assertEqual(len(repo.get_all_common_groups()), original_count)
        self.assertIsNone(next((g for g in repo.get_all_common_groups() if g.id == "test_group_delete"), None))

    def test_category_and_template_migrations(self):
        """Verify that old checklists categories are migrated to 'Att göra' and old templates merged."""
        # Setup initial DB file with old structure
        old_item_1 = ChecklistItem(id="old_item_1", title="Gamla packa", is_checked=False, category="Packning & Förskola")
        old_item_2 = ChecklistItem(id="old_item_2", title="Handla mjölk", is_checked=True, category="Inköp")
        old_group = CommonGroup(id="group_old", name="Gamla Favoriter", items=["Favorit 1"])
        
        data = ChecklistsData(
            checklists=[
                Checklist(id="active_list", title="Active", category_order=["Att göra", "Inköp"], items=[old_item_1, old_item_2]),
            ],
            common_groups=[old_group]
        )
        
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write(data.model_dump_json(indent=2))
            
        # Instantiating repo triggers the migration automatically
        repo = JsonChecklistRepository(db_path=self.db_path)
        
        # 1. Verify checklist items migrated to 'Att göra'
        active = repo.get_checklist("active_list")
        self.assertEqual(active.category_order, ["Att göra", "Jobb"])
        for item in active.items:
            self.assertEqual(item.category, "Att göra")
            
        # 2. Verify old templates merged into Privat favorites
        groups = repo.get_all_common_groups()
        self.assertEqual(len(groups), 2)
        todo_group = next(g for g in groups if g.id == "todo_favorites")
        self.assertIn("Favorit 1", todo_group.items)

    def test_three_button_routing(self):
        """Verify that task creation buttons route items to correct categories or backlog lists."""
        repo = JsonChecklistRepository(db_path=self.db_path)
        from src.views.checklist_view import ChecklistView
        
        # Mock main_view
        main_view = MagicMock()
        main_view.current_mode = "Att göra"
        
        view = ChecklistView(repo=repo, main_view=main_view)
        
        # Route to Privat Checklist
        view._add_new_item("Privat uppgift", "Att göra")
        self.assertEqual(len([i for i in view.active_list.items if i.category == "Att göra"]), 1)
        
        # Route to Work Checklist
        view._add_new_item("Jobb uppgift", "Jobb")
        self.assertEqual(len([i for i in view.active_list.items if i.category == "Jobb"]), 1)
        
        # Route context-awarely to Backlog (we are currently in 'Att göra' mode)
        view._add_new_item("Spara till senare", "Senare")
        later = repo.get_checklist("later_list")
        self.assertEqual(len(later.items), 1)
        self.assertEqual(later.items[0].category, "Att göra")

    def test_templates_view_mode_filtering(self):
        """Verify that TemplatesView filters and renders only active mode's favorites card."""
        repo = MagicMock()
        callback = MagicMock()
        
        todo_group = CommonGroup(id="todo_favorites", name="Privat", items=["Privat 1"])
        work_group = CommonGroup(id="work_favorites", name="Jobb", items=["Jobb 1"])
        repo.get_all_common_groups.return_value = [todo_group, work_group]
        
        main_view = MagicMock()
        main_view.current_mode = "Att göra"
        
        # 1. Test Privat mode renders Privat favorites card
        view = TemplatesView(repo=repo, on_template_added_to_active=callback, main_view=main_view)
        self.assertEqual(len(view.cards_container.controls), 1)
        card_content = view.cards_container.controls[0].content
        self.assertEqual(card_content.controls[0].controls[0].value, "Privat favoriter")
        
        # 2. Switch to Jobb mode and refresh
        main_view.current_mode = "Jobb"
        view._load_data()
        self.assertEqual(len(view.cards_container.controls), 1)
        card_content = view.cards_container.controls[0].content
        self.assertEqual(card_content.controls[0].controls[0].value, "Jobb favoriter")

    def test_client_storage_repo_synchronous_web(self):
        """Verify that ClientStorageRepository uses Emscripten IDBFS file operations on web."""
        import sys
        from src.repositories import client_storage_repo
        original_is_web = client_storage_repo.IS_WEB
        client_storage_repo.IS_WEB = True
        
        try:
            mock_page = MagicMock()
            repo = client_storage_repo.ClientStorageRepository(page=mock_page)
            
            # Temporary redirect the path to a test location
            original_path = repo.desktop_file_path
            import tempfile
            temp_db = tempfile.mktemp()
            repo.desktop_file_path = temp_db
            
            try:
                test_content = '{"checklists": [], "common_groups": []}'
                repo._write_raw(test_content)
                
                # Check that standard file system write happened
                with open(temp_db, "r", encoding="utf-8") as f:
                    self.assertEqual(f.read(), test_content)
                    
                # Check that standard file system read works
                self.assertEqual(repo._read_raw(), test_content)
            finally:
                if os.path.exists(temp_db):
                    os.remove(temp_db)
                repo.desktop_file_path = original_path
        finally:
            client_storage_repo.IS_WEB = original_is_web

    def test_pwa_icon_presence_and_validity(self):
        """Verify that the custom green PWA app icons and manifest exist and are valid."""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_icon_path = os.path.join(src_dir, "src", "assets", "icon.png")
        self.assertTrue(os.path.exists(src_icon_path), f"Source icon.png not found at {src_icon_path}")
        
        with open(src_icon_path, "rb") as f:
            header = f.read(8)
            is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
            is_jpeg = header.startswith(b"\xff\xd8\xff")
            self.assertTrue(is_png or is_jpeg, "Source icon.png is not a valid PNG or JPEG image")

if __name__ == "__main__":
    unittest.main()
