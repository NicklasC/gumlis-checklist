from __future__ import annotations

import functools
import os
import threading
import time
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from tests.support.paths import DEPLOY_APP

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - exercised by environments without dev dependencies
    sync_playwright = None


RUN_E2E = os.environ.get("GUMLI_RUN_E2E") == "1"
E2E_AVAILABLE = RUN_E2E and sync_playwright is not None and DEPLOY_APP.is_dir()
e2e_test = unittest.skipUnless(E2E_AVAILABLE, "Set GUMLI_RUN_E2E=1 with Playwright and a built PWA")


class QuietPwaHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".wasm": "application/wasm",
        ".json": "application/json",
    }

    def log_message(self, format, *args):
        return


class PwaServer:
    def __enter__(self):
        handler = functools.partial(QuietPwaHandler, directory=str(DEPLOY_APP.parent))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}/gumlis-checklist/"
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class BrowserTestCase(unittest.TestCase):
    viewport = {"width": 410, "height": 820}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server_context = PwaServer()
        cls.server = cls.server_context.__enter__()
        cls.playwright_context = sync_playwright().start()
        headless = os.environ.get("GUMLI_HEADLESS", "1") != "0"
        cls.browser = cls.playwright_context.chromium.launch(headless=headless)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright_context.stop()
        cls.server_context.__exit__(None, None, None)
        super().tearDownClass()

    def setUp(self):
        self.context = self.browser.new_context(viewport=self.viewport)
        self.page = self.context.new_page()
        self.console_errors = []
        self.console_messages = []
        self.page_errors = []
        self.failed_requests = []
        self.current_mode = "Privat"
        self.page.on("console", self._capture_console)
        self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        self.page.on(
            "requestfailed",
            lambda request: self.failed_requests.append(f"{request.url}: {request.failure}"),
        )
        self.boot()

    def tearDown(self):
        self.context.close()

    def _capture_console(self, message):
        self.console_messages.append(f"{message.type}: {message.text}")
        if message.type == "error":
            self.console_errors.append(message.text)

    def boot(self):
        self.page.goto(self.server.base_url)
        accessibility = self.page.locator("flt-semantics-placeholder[role='button']").or_(
            self.page.locator("[aria-label='Enable accessibility']")
        )
        accessibility.first.wait_for(state="visible", timeout=90_000)
        deadline = time.monotonic() + 90
        while not any("Python worker initialized" in entry for entry in self.console_messages):
            if time.monotonic() >= deadline:
                raise AssertionError("The Python worker did not initialize within 90 seconds")
            self.page.wait_for_timeout(100)
        self.page.wait_for_timeout(500)
        # Flutter deliberately positions this semantics activator outside the
        # rendered canvas. Keyboard activation follows the path used by
        # assistive technology in current Flutter web builds.
        accessibility.first.focus()
        accessibility.first.press("Enter")
        try:
            self.page.get_by_role("tab", name="Checklista").wait_for(state="visible", timeout=90_000)
        except Exception as error:
            state = self.page.evaluate(
                """() => ({
                    url: location.href,
                    title: document.title,
                    loadingClass: document.querySelector('#loading')?.className ?? null,
                    loadingText: document.querySelector('#loading')?.textContent?.trim() ?? null,
                    canvases: document.querySelectorAll('canvas').length,
                    semantics: document.querySelectorAll('flt-semantics').length,
                    placeholder: document.querySelectorAll('flt-semantics-placeholder').length,
                    pyodideConfigured: Boolean(window.flet?.pyodide),
                    pythonModuleName: window.flet?.pythonModuleName ?? null
                })"""
            )
            details = "\n".join(
                [
                    f"state: {state}",
                    *(f"log: {entry}" for entry in self.console_messages[-100:]),
                    *(f"console: {entry}" for entry in self.console_errors),
                    *(f"page: {entry}" for entry in self.page_errors),
                    *(f"request: {entry}" for entry in self.failed_requests),
                ]
            ) or "no browser, page, or request errors"
            raise AssertionError(f"The PWA did not expose its navigation semantics. Diagnostics:\n{details}") from error
        # The Flutter semantics tree can be visible just before Pyodide has
        # finished attaching Python event handlers.
        self.page.wait_for_timeout(500)

    def select_tab(self, name):
        tab = self.page.get_by_role("tab", name=name)
        tab.click()
        # Each destination is constructed lazily in Python. Give the newly
        # mounted controls time to receive their event handlers.
        self.page.wait_for_timeout(800)

    def set_mode(self, name):
        self.page.get_by_role("button", name=name, exact=True).click()
        self.page.wait_for_timeout(500)
        self.current_mode = name

    def checklist_input(self):
        return self.page.get_by_role("textbox", name="Skriv något att göra...")

    def add_checklist_item(self, title):
        field = self.checklist_input()
        field.fill(title)
        add_label = "+ Jobb" if self.current_mode == "Jobb" else "+ Att göra"
        self.page.get_by_role("button", name=add_label, exact=True).click()
        self.page.get_by_text(title, exact=True).wait_for(state="visible", timeout=10_000)

    def submit_checklist_item_with_enter(self, title):
        field = self.checklist_input()
        field.fill(title)
        field.press("Enter")
        self.page.get_by_text(title, exact=True).wait_for(state="visible", timeout=10_000)

    def wait_for_storage_flush(self):
        # Browser persistence uses Emscripten syncfs asynchronously; UI state
        # can update before IndexedDB has received the write.
        self.page.wait_for_timeout(1_000)

    def assert_no_unexpected_console_errors(self):
        ignored = ("favicon",)
        unexpected = [entry for entry in self.console_errors if not any(value in entry for value in ignored)]
        self.assertEqual(unexpected, [])
