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

    def test_snabblistan_group_creation_and_deletion(self):
        """Verify that Snabblistan tab plus button works, opens the dialog, and allows creating and deleting a favorite group."""
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
        
        # 3. Locate and click the 'Ny favoritgrupp' plus button
        print("Verifying and clicking the plus button...")
        plus_button = self.page.locator("flt-semantics[role='button']").first
        self.assertTrue(plus_button.count() > 0, "Plus button (role='button') not found in Snabblistan header!")
        plus_button.click()
        self.page.wait_for_timeout(3000)
        
        # 4. Verify that the AlertDialog has successfully opened
        print("Verifying that the AlertDialog is visible...")
        dialog = self.page.locator("[role='alertdialog']")
        self.assertTrue(dialog.count() > 0, "AlertDialog did not open after clicking the plus button!")
        
        dialog_title = self.page.locator("span:has-text('Skapa ny favoritgrupp')").or_(self.page.locator("[aria-label='Alert']"))
        self.assertTrue(dialog_title.count() > 0, "Dialog title was not found!")
        
        # 5. Fill out the text input with a new group name
        print("Entering a new group name...")
        input_field = self.page.locator("input[data-semantics-role='text-field']")
        self.assertTrue(input_field.count() > 0, "Dialog input text field was not found!")
        input_field.first.focus()
        self.page.wait_for_timeout(1000)
        
        test_group_name = "Mina Testfavoriter"
        self.page.keyboard.type(test_group_name)
        self.page.wait_for_timeout(1000)
        
        # 6. Click the 'Skapa' button to submit
        print("Submitting the dialog...")
        create_button = self.page.locator("flt-semantics[role='button']:has-text('Skapa')")
        self.assertTrue(create_button.count() > 0, "'Skapa' button was not found in the dialog!")
        create_button.click()
        
        print("Waiting for group list update...")
        self.page.wait_for_timeout(4000)
        
        # 7. Verify that the new group is successfully rendered on Snabblistan tab
        print("Verifying that the new group is rendered on screen...")
        group_header = self.page.locator(f"span:has-text('{test_group_name}')")
        self.assertTrue(group_header.count() > 0, f"The newly created group '{test_group_name}' was not found in the DOM!")
        
        # 8. Delete the group using the 'Ta bort grupp' delete button
        print("Locating delete button for the new group...")
        delete_button = self.page.locator("[aria-label='Ta bort grupp']").last
        self.assertTrue(delete_button.count() > 0, "Delete button ('Ta bort grupp') was not found in the group card!")
        
        print("Deleting the group...")
        delete_button.click()
        self.page.wait_for_timeout(3000)
        
        # 9. Verify that the group was successfully deleted and is no longer in the DOM
        print("Verifying that the group is removed from the DOM...")
        group_header_after = self.page.locator(f"span:has-text('{test_group_name}')")
        self.assertEqual(group_header_after.count(), 0, f"The group '{test_group_name}' still exists in the DOM after deletion!")
        print("Success! Plus button, creation, and deletion GUI workflows verified successfully.")

if __name__ == "__main__":
    unittest.main()
