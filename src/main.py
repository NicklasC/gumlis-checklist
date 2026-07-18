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
from src.core.config import JSON_DB_PATH
from src.repositories.browser_storage import prepare_browser_storage
from src.repositories.client_storage_repo import ClientStorageRepository
from src.views.main_view import MainView
from src.views.startup_view import create_startup_view

IS_WEB = sys.platform == 'emscripten'


def web_log(message: str):
    if IS_WEB:
        import js
        js.console.log(f"[GUMLI STARTUP] {message}")


def startup_mark(name: str):
    """Expose startup milestones to browser diagnostics without noisy production logs."""
    if IS_WEB:
        try:
            import js
            # Python runs in a worker. deploy.py patches python.js so these
            # messages become marks on the main page's diagnostics object.
            js.self.postMessage(f"__gumli_startup__:{name}")
        except Exception:
            # Telemetry must never delay or prevent application startup.
            pass

async def load_indexeddb_storage():
    """Load the legacy IDBFS store only for one-time migration."""
    import js
    import pyodide
    import asyncio
    web_log("starting IndexedDB mount")
    
    # Resolve the Emscripten FS object robustly (needed because in Web Workers,
    # FS might not be a direct property of the js global scope, but is on pyodide_js or js.pyodide)
    FS = None
    try:
        import pyodide_js
        if hasattr(pyodide_js, "FS"):
            FS = pyodide_js.FS
            print("[INDEXEDDB] Found FS via pyodide_js")
    except ImportError:
        pass
        
    if not FS:
        try:
            if hasattr(js, "pyodide") and hasattr(js.pyodide, "FS"):
                FS = js.pyodide.FS
                print("[INDEXEDDB] Found FS via js.pyodide")
        except Exception:
            pass
            
    if not FS:
        try:
            if hasattr(js, "FS"):
                FS = js.FS
                print("[INDEXEDDB] Found FS via js.FS")
        except Exception:
            pass
            
    if not FS:
        print("[INDEXEDDB] Critical Error: Emscripten FS object could not be resolved!")
        return False

    try:
        # Create persistent directory
        if not FS.analyzePath('/home/data').exists:
            FS.mkdir('/home/data')
        
        # Mount Emscripten IDBFS to the directory
        is_mounted = any(m.mountpoint == '/home/data' for m in FS.mounts)
        if not is_mounted:
            FS.mount(FS.filesystems.IDBFS, pyodide.ffi.to_js({}), '/home/data')
            print("[INDEXEDDB] Mounted IDBFS to /home/data successfully!")
    except Exception as e:
        print(f"[INDEXEDDB] Error mounting IDBFS: {e}")
        import traceback
        traceback.print_exc()
        try:
            import pyodide
            if isinstance(e, pyodide.ffi.JsException):
                print(f"[INDEXEDDB] JS Error Name: {e.name}")
                print(f"[INDEXEDDB] JS Error Message: {e.message}")
                print(f"[INDEXEDDB] JS Error Stack: {e.stack}")
        except Exception as e2:
            print(f"[INDEXEDDB] Failed to extract JS error details: {e2}")
        return False

    # Asynchronously load files from browser's IndexedDB into Pyodide's MEMFS
    future = asyncio.get_running_loop().create_future()
    
    def sync_callback(err):
        if future.done():
            return
        if err:
            print(f"[INDEXEDDB] syncfs failed: {err}")
            future.set_exception(Exception(f"syncfs failed: {err}"))
        else:
            print("[INDEXEDDB] syncfs load completed successfully!")
            future.set_result(True)
            
    try:
        proxy = pyodide.ffi.create_proxy(sync_callback)
        FS.syncfs(True, proxy)
        # IndexedDB can occasionally leave syncfs without invoking its
        # callback (for example after an interrupted browser shutdown). The
        # app must still start; an empty/in-memory repository is safer than an
        # indefinitely blocked loading screen.
        await asyncio.wait_for(future, timeout=5)
        return True
    except asyncio.TimeoutError:
        print("[INDEXEDDB] syncfs load timed out; continuing without persisted data")
        return False
    except Exception as e:
        print(f"[INDEXEDDB] Error during syncfs: {e}")
        return False

async def main(page: ft.Page):
    web_log("main entered")
    startup_mark("python-main-entered")
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

    if IS_WEB:
        # Present a stable, non-interactive app shell while persistent data is
        # synchronized. It does not construct a repository or write defaults.
        page.add(create_startup_view())
        page.update()
        startup_mark("app-shell-visible")

        storage_source = await prepare_browser_storage(load_indexeddb_storage, JSON_DB_PATH)
        web_log(f"Browser storage ready: {storage_source}")
        startup_mark("storage-ready")
    
    # Initialize client storage repository (perfect for local desktop and web PWAs!)
    repo = ClientStorageRepository(page=page)
    web_log("repository initialized")
    
    # Mount core layout view
    app_layout = MainView(repo=repo)
    if IS_WEB:
        page.controls.clear()
    page.add(app_layout)
    page.update()
    web_log("main view mounted")
    
    # Safely initialize database and load checklists after client_storage is fully synchronized
    app_layout.initialize_data()
    page.update()
    startup_mark("checklist-visible")
if __name__ == "__main__":
    ft.run(main)
