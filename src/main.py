import os
import sys
import flet as ft

# Ensure the root of the project is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Pyodide PWA import compatibility shim
# If we are running in Pyodide/PWA where 'src' contents are packaged directly at the root level,
# we dynamically register a dummy 'src' module with its __path__ pointing to the root.
# This allows all 'from src.xxx' imports to work flawlessly without modification.
import types
if 'src' not in sys.modules:
    src_mod = types.ModuleType('src')
    src_mod.__path__ = [current_dir]
    sys.modules['src'] = src_mod

from src.core.theme import get_app_theme, BG_COLOR
from src.repositories.client_storage_repo import ClientStorageRepository
from src.views.main_view import MainView

def main(page: ft.Page):
    # Configure main window properties (optimized for a modern mobile screen size by default)
    page.title = "Gumli"
    page.window.width = 410
    page.window.height = 820
    page.window.min_width = 320
    page.window.min_height = 600
    page.window.resizable = True
    
    # Enable scroll on the page itself if needed, but since our views scroll internally, keep it false
    page.scroll = None
    page.padding = 0
    page.bgcolor = BG_COLOR
    
    # Apply custom premium theme (Emerald & Mint green Material 3 theme)
    page.theme = get_app_theme()
    
    # Initialize client storage repository (perfect for local desktop and web PWAs!)
    repo = ClientStorageRepository(page=page)
    
    # Mount core layout view
    app_layout = MainView(repo=repo)
    page.add(app_layout)
    page.update()

if __name__ == "__main__":
    ft.run(main)
