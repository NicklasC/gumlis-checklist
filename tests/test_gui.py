import os
import sys
import time
import unittest
import subprocess
from playwright.sync_api import sync_playwright

class TestGumliBrowserGUI(unittest.TestCase):
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
        time.sleep(2) # Give the server a moment to start up

    @classmethod
    def tearDownClass(cls):
        print("Stopping PWA local HTTP server...")
        cls.server_process.terminate()
        cls.server_process.wait()

    def setUp(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=True)
        # Use mobile screen emulation for best responsive experience matching Gumli layout
        self.context = self.browser.new_context(viewport={"width": 410, "height": 820})
        self.page = self.context.new_page()

    def tearDown(self):
        self.browser.close()
        self.pw.stop()

    def test_snabblistan_favorite_addition_and_removal(self):
        """Verify that Snabblistan tab allows adding and removing favorite items."""
        url = f"http://localhost:8000/gumlis-checklist/"
        print(f"Loading Gumli PWA at {url}...")
        self.page.goto(url)
        
        print("Waiting for Flet/Pyodide PWA and Web Workers to boot up...")
        self.page.wait_for_timeout(15000)
        
        # 1. Enable accessibility/semantics to get HTML DOM tree representation from canvaskit
        print("Activating DOM accessibility/semantics mode...")
        acc_button = self.page.locator("flt-semantics-placeholder[role='button']").or_(self.page.locator("[aria-label='Enable accessibility']"))
        self.assertTrue(acc_button.count() > 0, "Flutter accessibility placeholder was not found on screen!")
        
        acc_button.first.focus()
        acc_button.first.press("Enter")
        self.page.wait_for_timeout(3000)
        
        # 2. Click Snabblistan tab
        print("Navigating to Snabblistan tab...")
        snabblistan_tab = self.page.locator("[aria-label='Snabblistan'][role='tab']")
        self.assertTrue(snabblistan_tab.count() > 0, "Snabblistan tab was not found in the DOM!")
        snabblistan_tab.first.click()
        self.page.wait_for_timeout(3000)
        
        # 3. Locate the new favorite text input field
        print("Verifying the input field...")
        input_field = self.page.locator("input[data-semantics-role='text-field']").or_(self.page.locator("input"))
        self.assertTrue(input_field.count() > 0, "New favorite input text field was not found!")
        
        # 4. Fill out the input field and press Enter
        print("Entering a new favorite item name...")
        test_item_name = "Testa GUI"
        input_field.first.focus()
        self.page.wait_for_timeout(1000)
        self.page.keyboard.type(test_item_name)
        self.page.wait_for_timeout(1000)
        self.page.keyboard.press("Enter")
        print("Submitted the new favorite item.")
        
        print("Waiting for favorite list update...")
        self.page.wait_for_timeout(4000)
        
        # 5. Verify that the new favorite is successfully rendered on Snabblistan tab
        print("Verifying that the new favorite is rendered on screen...")
        favorite_item = self.page.locator(f"flt-semantics:has-text('{test_item_name}')").or_(self.page.locator(f"span:has-text('{test_item_name}')"))
        self.assertTrue(favorite_item.count() > 0, f"The newly created favorite '{test_item_name}' was not found in the DOM!")
        
        # 6. Delete the favorite using the 'Ta bort favorit' delete button
        print("Locating delete button for the new favorite...")
        delete_button = self.page.locator("[aria-label='Ta bort favorit']").last
        self.assertTrue(delete_button.count() > 0, "Delete button ('Ta bort favorit') was not found in the favorites card!")
        
        print("Deleting the favorite...")
        delete_button.click()
        self.page.wait_for_timeout(3000)
        
        # 7. Verify that the favorite was successfully deleted and is no longer in the DOM
        print("Verifying that the favorite is removed from the DOM...")
        favorite_item_after = self.page.locator(f"flt-semantics:has-text('{test_item_name}')").or_(self.page.locator(f"span:has-text('{test_item_name}')"))
        self.assertEqual(favorite_item_after.count(), 0, f"The favorite '{test_item_name}' still exists in the DOM after deletion!")
        print("Success! Favorite item addition and removal GUI workflows verified successfully.")

if __name__ == "__main__":
    unittest.main()
