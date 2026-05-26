import os
import sys
import time
import unittest
import subprocess
from playwright.sync_api import sync_playwright

class TestPWARestartPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deploy_dir = r"d:\Dev\personal-projects\nicklasc.github.io"
        cls.port = 8000
        
        # Start Python's built-in HTTP server to serve the PWA files
        print(f"Starting PWA local HTTP server on port {cls.port}...")
        cls.server_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(cls.port)],
            cwd=cls.deploy_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        print("Stopping PWA local HTTP server...")
        cls.server_process.terminate()
        cls.server_process.wait()

    def test_pwa_restart_persistence(self):
        """Verify that items added in the PWA remain after reloading/re-opening the application."""
        with sync_playwright() as pw:
            # We use persistent context to emulate standard browser local storage persistence!
            import tempfile
            user_data_dir = tempfile.mkdtemp()
            
            browser_context = pw.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                viewport={"width": 410, "height": 820}
            )
            
            page = browser_context.new_page()
            page.on("console", lambda msg: print(f"[BROWSER PHASE 1 CONSOLE] {msg.text}"))
            url = f"http://localhost:8000/gumlis-checklist/"
            
            # --- PHASE 1: Add Item ---
            print("\n[PHASE 1] Loading Gumli PWA...")
            page.goto(url)
            print("Waiting for PWA boot...")
            page.wait_for_timeout(15000)
            
            print("Activating DOM accessibility/semantics mode...")
            acc_button = page.locator("flt-semantics-placeholder[role='button']").or_(page.locator("[aria-label='Enable accessibility']"))
            acc_button.first.focus()
            acc_button.first.press("Enter")
            page.wait_for_timeout(3000)
            
            print("Navigating to Snabblistan tab...")
            snabblistan_tab = page.locator("[aria-label='Snabblistan'][role='tab']")
            snabblistan_tab.first.click()
            page.wait_for_timeout(3000)
            
            print("Adding unique favorite 'Verifiera PWA Persistens'...")
            input_field = page.locator("input[data-semantics-role='text-field']").or_(page.locator("input"))
            input_field.first.focus()
            page.wait_for_timeout(1000)
            page.keyboard.type("Verifiera PWA Persistens")
            page.wait_for_timeout(1000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(4000)
            
            # Verify it's on screen
            favorite_item = page.locator("flt-semantics:has-text('Verifiera PWA Persistens')").or_(page.locator("span:has-text('Verifiera PWA Persistens')"))
            self.assertTrue(favorite_item.count() > 0, "Item was not added in Phase 1!")
            print("Phase 1 Success: Item added to screen successfully!")
            
            # Close browser context to simulate closing the application
            browser_context.close()
            
            # --- PHASE 2: Restart & Verify ---
            print("\n[PHASE 2] Restarting browser and reloading Gumli PWA...")
            browser_context2 = pw.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                viewport={"width": 410, "height": 820}
            )
            
            page2 = browser_context2.new_page()
            page2.on("console", lambda msg: print(f"[BROWSER PHASE 2 CONSOLE] {msg.text}"))
            page2.goto(url)
            print("Waiting for PWA boot...")
            page2.wait_for_timeout(15000)
            
            print("Activating DOM accessibility/semantics mode...")
            acc_button2 = page2.locator("flt-semantics-placeholder[role='button']").or_(page2.locator("[aria-label='Enable accessibility']"))
            acc_button2.first.focus()
            acc_button2.first.press("Enter")
            page2.wait_for_timeout(3000)
            
            print("Navigating to Snabblistan tab...")
            snabblistan_tab2 = page2.locator("[aria-label='Snabblistan'][role='tab']")
            snabblistan_tab2.first.click()
            page2.wait_for_timeout(3000)
            
            print("Checking if unique favorite is still present in the list...")
            favorite_item2 = page2.locator("flt-semantics:has-text('Verifiera PWA Persistens')").or_(page2.locator("span:has-text('Verifiera PWA Persistens')"))
            
            # Check presence
            is_present = favorite_item2.count() > 0
            if is_present:
                print("SUCCESS: Unique item 'Verifiera PWA Persistens' is still in the list after restarting browser!")
            else:
                print("FAILURE: Unique item is missing after browser restart.")
                
            # Cleanup the item before exiting
            if is_present:
                print("Cleaning up unique favorite...")
                delete_button = page2.locator("[aria-label='Ta bort favorit']").last
                delete_button.click()
                page2.wait_for_timeout(3000)
                
            browser_context2.close()
            self.assertTrue(is_present, "State was lost after closing/restarting browser!")

if __name__ == "__main__":
    unittest.main()
