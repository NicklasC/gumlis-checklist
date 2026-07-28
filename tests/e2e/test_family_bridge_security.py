from __future__ import annotations

import os
from pathlib import Path
import unittest

from tests.support.browser_case import E2E_AVAILABLE, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "pwa_templates" / "index.html"
APPS_SCRIPT_BRIDGE = ROOT / "apps_script" / "family_api" / "Bridge.html"
TEST_NONCE = "a" * 64


@unittest.skipUnless(E2E_AVAILABLE, "Set GUMLI_RUN_E2E=1 with Playwright and a built PWA")
class FamilyBridgeSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        html = TEMPLATE.read_text(encoding="utf-8")
        marker = html.index("// Created only after the user opens Familj")
        script_start = html.rfind("<script>", 0, marker) + len("<script>")
        script_end = html.index("</script>", marker)
        cls.family_script = html[script_start:script_end]
        bridge_html = APPS_SCRIPT_BRIDGE.read_text(encoding="utf-8")
        bridge_html = bridge_html.replace(
            "<?!= allowedOriginsJson ?>",
            '["https://nicklasc.github.io"]',
        ).replace(
            "<?!= bridgeNonceJson ?>",
            f'"{TEST_NONCE}"',
        )
        bridge_marker = bridge_html.index("const allowedOrigins")
        bridge_start = bridge_html.rfind("<script>", 0, bridge_marker) + len("<script>")
        bridge_end = bridge_html.index("</script>", bridge_marker)
        cls.apps_script_bridge = bridge_html[bridge_start:bridge_end]
        cls.playwright_context = sync_playwright().start()
        headless = os.environ.get("GUMLI_HEADLESS", "1") != "0"
        cls.browser = cls.playwright_context.chromium.launch(headless=headless)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright_context.stop()
        super().tearDownClass()

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.route("https://script.google.com/**", lambda route: route.abort())

    def tearDown(self):
        self.page.close()

    def _prepare_delayed_handshake_page(self):
        self.page.set_content("<!doctype html><html><body></body></html>")
        self.page.evaluate(
            """() => {
                window.__timeoutHandlers = [];
                window.__clearedTimeouts = [];
                window.setTimeout = handler => {
                    window.__timeoutHandlers.push(handler);
                    return window.__timeoutHandlers.length;
                };
                window.clearTimeout = timeoutId => {
                    window.__clearedTimeouts.push(timeoutId);
                };
                const originalAppend = document.body.appendChild.bind(document.body);
                const sourceFrame = document.createElement('iframe');
                sourceFrame.srcdoc = '<!doctype html><html><body></body></html>';
                originalAppend(sourceFrame);
                window.__bridgeSourceFrame = sourceFrame;
                window.__sentBridgeMessages = [];
                window.__workerMessages = [];
                document.body.appendChild = node => {
                    if (node.tagName === 'IFRAME' && node.title === 'Gumli Familj API') {
                        window.__familyFrame = node;
                        return node;
                    }
                    return originalAppend(node);
                };
            }"""
        )
        self.page.wait_for_function("() => Boolean(window.__bridgeSourceFrame.contentWindow)")
        self.page.evaluate(
            """() => {
                window.__bridgeSourceFrame.contentWindow.postMessage = (message, targetOrigin) => {
                    window.__sentBridgeMessages.push({ message, targetOrigin });
                };
            }"""
        )
        self.page.add_script_tag(content=self.family_script)

    def _start_delayed_request(self, request_id):
        self.page.evaluate(
            """requestId => {
                const worker = {
                    postMessage(message) {
                        window.__workerMessages.push(message);
                    }
                };
                void window.gumliFamilyBridge.forward({
                    type: 'gumli-family-request',
                    requestId,
                    payload: { deviceToken: 'security-test-placeholder-token' }
                }, worker);
            }""",
            request_id,
        )

    def _dispatch_ready(self, nonce):
        self.page.evaluate(
            """({ nonce, origin }) => {
                window.dispatchEvent(new MessageEvent('message', {
                    data: { type: 'gumli-family-ready', bridgeNonce: nonce },
                    origin,
                    source: window.__bridgeSourceFrame.contentWindow
                }));
            }""",
            {
                "nonce": nonce,
                "origin": "https://n-security-test-script.googleusercontent.com",
            },
        )

    def test_wrong_nonce_and_broad_google_origin_cannot_capture_request(self):
        self.page.set_content("<!doctype html><html><body></body></html>")
        self.page.evaluate(
            """() => {
                const originalAppend = document.body.appendChild.bind(document.body);
                const sourceFrame = document.createElement('iframe');
                sourceFrame.srcdoc = '<!doctype html><html><body></body></html>';
                originalAppend(sourceFrame);
                window.__bridgeSourceFrame = sourceFrame;
                window.__sentBridgeMessages = [];
                window.__workerMessages = [];
                document.body.appendChild = node => {
                    if (node.tagName === 'IFRAME' && node.title === 'Gumli Familj API') {
                        window.__familyFrame = node;
                        return node;
                    }
                    return originalAppend(node);
                };
            }"""
        )
        self.page.wait_for_function("() => Boolean(window.__bridgeSourceFrame.contentWindow)")
        self.page.evaluate(
            """() => {
                window.__bridgeSourceFrame.contentWindow.postMessage = (message, targetOrigin) => {
                    window.__sentBridgeMessages.push({ message, targetOrigin });
                };
            }"""
        )
        self.page.add_script_tag(content=self.family_script)
        self.page.evaluate(
            """() => {
                const worker = {
                    postMessage(message) {
                        window.__workerMessages.push(message);
                    }
                };
                void window.gumliFamilyBridge.forward({
                    type: 'gumli-family-request',
                    requestId: 'security-test-request',
                    payload: { deviceToken: 'security-test-placeholder-token' }
                }, worker);
            }"""
        )

        frame_state = self.page.evaluate(
            """() => {
                const url = new URL(window.__familyFrame.src);
                return {
                    nonce: url.searchParams.get('bridgeNonce'),
                    queryKeys: Array.from(url.searchParams.keys()),
                    ready: window.gumliFamilyDebug.ready
                };
            }"""
        )
        self.assertRegex(frame_state["nonce"], r"^[a-f0-9]{64}$")
        self.assertEqual(frame_state["queryKeys"], ["bridgeNonce"])
        self.assertFalse(frame_state["ready"])

        self.page.evaluate(
            """() => {
                window.dispatchEvent(new MessageEvent('message', {
                    data: {
                        type: 'gumli-family-ready',
                        bridgeNonce: '0'.repeat(64)
                    },
                    origin: 'https://n-security-test-script.googleusercontent.com',
                    source: window.__bridgeSourceFrame.contentWindow
                }));
            }"""
        )
        self.assertEqual(
            self.page.evaluate(
                "() => ({ ready: gumliFamilyDebug.ready, sent: __sentBridgeMessages.length })"
            ),
            {"ready": False, "sent": 0},
        )

        self.page.evaluate(
            """nonce => {
                window.dispatchEvent(new MessageEvent('message', {
                    data: { type: 'gumli-family-ready', bridgeNonce: nonce },
                    origin: 'https://evil.googleusercontent.com',
                    source: window.__bridgeSourceFrame.contentWindow
                }));
            }""",
            frame_state["nonce"],
        )
        self.assertEqual(
            self.page.evaluate(
                "() => ({ ready: gumliFamilyDebug.ready, sent: __sentBridgeMessages.length })"
            ),
            {"ready": False, "sent": 0},
        )

        trusted_origin = "https://n-security-test-script.googleusercontent.com"
        self.page.evaluate(
            """({ nonce, origin }) => {
                window.dispatchEvent(new MessageEvent('message', {
                    data: { type: 'gumli-family-ready', bridgeNonce: nonce },
                    origin,
                    source: window.__bridgeSourceFrame.contentWindow
                }));
            }""",
            {"nonce": frame_state["nonce"], "origin": trusted_origin},
        )
        self.page.wait_for_function("() => window.__sentBridgeMessages.length === 1")

        sent = self.page.evaluate("() => window.__sentBridgeMessages[0]")
        self.assertEqual(sent["targetOrigin"], trusted_origin)
        self.assertEqual(sent["message"]["bridgeNonce"], frame_state["nonce"])
        self.assertEqual(sent["message"]["requestId"], "security-test-request")

        self.page.evaluate(
            """({ nonce, origin }) => {
                window.dispatchEvent(new MessageEvent('message', {
                    data: {
                        type: 'gumli-family-response',
                        bridgeNonce: 'f'.repeat(64),
                        requestId: 'security-test-request',
                        response: { ok: true }
                    },
                    origin,
                    source: window.__bridgeSourceFrame.contentWindow
                }));
                window.dispatchEvent(new MessageEvent('message', {
                    data: {
                        type: 'gumli-family-response',
                        bridgeNonce: nonce,
                        requestId: 'security-test-request',
                        response: { ok: true, data: { member: 'Nicklas' } }
                    },
                    origin,
                    source: window.__bridgeSourceFrame.contentWindow
                }));
            }""",
            {"nonce": frame_state["nonce"], "origin": trusted_origin},
        )
        self.page.wait_for_function("() => window.__workerMessages.length === 1")
        response = self.page.evaluate("() => window.__workerMessages[0]")
        self.assertEqual(response["response"]["data"]["member"], "Nicklas")

    def test_apps_script_bridge_rejects_wrong_source_and_nonce(self):
        self.page.route(
            "https://nicklasc.github.io/**",
            lambda route: route.fulfill(
                status=200,
                content_type="text/html",
                body="<!doctype html><html><body></body></html>",
            ),
        )
        self.page.goto("https://nicklasc.github.io/security-harness")
        self.page.evaluate(
            """() => {
                window.__bridgeMessages = [];
                window.addEventListener('message', event => {
                    window.__bridgeMessages.push({
                        data: event.data,
                        origin: event.origin,
                        sourceIsTarget:
                            event.source === document.querySelector('#target').contentWindow
                    });
                });
                const target = document.createElement('iframe');
                target.id = 'target';
                target.name = 'target';
                target.srcdoc = '<!doctype html><html><body></body></html>';
                document.body.appendChild(target);
                const sibling = document.createElement('iframe');
                sibling.id = 'sibling';
                sibling.name = 'sibling';
                sibling.srcdoc = '<!doctype html><html><body></body></html>';
                document.body.appendChild(sibling);
            }"""
        )
        self.page.wait_for_function("() => document.querySelector('#target').contentWindow")
        target = next(frame for frame in self.page.frames if frame.name == "target")
        sibling = next(frame for frame in self.page.frames if frame.name == "sibling")
        target.evaluate(
            """() => {
                window.__handledPayload = null;
                const runner = {
                    success: null,
                    failure: null,
                    withSuccessHandler(handler) {
                        this.success = handler;
                        return this;
                    },
                    withFailureHandler(handler) {
                        this.failure = handler;
                        return this;
                    },
                    handleRequest(payload) {
                        window.__handledPayload = payload;
                        this.success({ ok: true, data: { member: 'Nicklas' } });
                    }
                };
                window.google = { script: { run: runner } };
            }"""
        )
        target.add_script_tag(content=self.apps_script_bridge)
        self.page.wait_for_function(
            """() => window.__bridgeMessages.some(
                entry => entry.data?.type === 'gumli-family-ready'
            )"""
        )
        ready = self.page.evaluate(
            """() => window.__bridgeMessages.find(
                entry => entry.data?.type === 'gumli-family-ready'
            )"""
        )
        self.assertEqual(ready["data"]["bridgeNonce"], TEST_NONCE)
        self.assertTrue(ready["sourceIsTarget"])

        sibling.evaluate(
            """nonce => {
                window.top.document.querySelector('#target').contentWindow.postMessage({
                    type: 'gumli-family-request',
                    bridgeNonce: nonce,
                    requestId: 'wrong-source',
                    payload: { action: 'ping' }
                }, 'https://nicklasc.github.io');
            }""",
            TEST_NONCE,
        )
        self.page.wait_for_timeout(50)
        self.assertIsNone(target.evaluate("() => window.__handledPayload"))

        self.page.evaluate(
            """() => {
                document.querySelector('#target').contentWindow.postMessage({
                    type: 'gumli-family-request',
                    bridgeNonce: '0'.repeat(64),
                    requestId: 'wrong-nonce',
                    payload: { action: 'ping' }
                }, 'https://nicklasc.github.io');
            }"""
        )
        self.page.wait_for_timeout(50)
        self.assertIsNone(target.evaluate("() => window.__handledPayload"))

        self.page.evaluate(
            """nonce => {
                document.querySelector('#target').contentWindow.postMessage({
                    type: 'gumli-family-request',
                    bridgeNonce: nonce,
                    requestId: 'valid-request',
                    payload: { action: 'ping' }
                }, 'https://nicklasc.github.io');
            }""",
            TEST_NONCE,
        )
        target.wait_for_function("() => window.__handledPayload?.action === 'ping'")
        self.page.wait_for_function(
            """() => window.__bridgeMessages.some(
                entry => entry.data?.type === 'gumli-family-response'
            )"""
        )
        response = self.page.evaluate(
            """() => window.__bridgeMessages.find(
                entry => entry.data?.type === 'gumli-family-response'
            )"""
        )
        self.assertEqual(response["data"]["bridgeNonce"], TEST_NONCE)
        self.assertEqual(response["data"]["requestId"], "valid-request")
        self.assertEqual(response["data"]["response"]["data"]["member"], "Nicklas")

    def test_embedded_gumli_never_creates_family_frame_or_forwards_token(self):
        self.page.set_content(
            """<!doctype html><html><body>
                <iframe id="embedded" srcdoc="<!doctype html><html><body></body></html>"></iframe>
            </body></html>"""
        )
        embedded = next(frame for frame in self.page.frames if frame != self.page.main_frame)
        embedded.add_script_tag(content=self.family_script)
        embedded.evaluate(
            """() => {
                window.__workerMessages = [];
                const worker = {
                    postMessage(message) {
                        window.__workerMessages.push(message);
                    }
                };
                void window.gumliFamilyBridge.forward({
                    type: 'gumli-family-request',
                    requestId: 'embedded-security-test',
                    payload: { deviceToken: 'security-test-placeholder-token' }
                }, worker);
            }"""
        )
        embedded.wait_for_function("() => window.__workerMessages.length === 1")
        state = embedded.evaluate(
            """() => ({
                frameCreated: window.gumliFamilyDebug.frameCreated,
                lastError: window.gumliFamilyDebug.lastError,
                workerError: window.__workerMessages[0]?.response?.error ?? null,
                familyFrames: document.querySelectorAll(
                    'iframe[title="Gumli Familj API"]'
                ).length
            })"""
        )
        self.assertEqual(
            state,
            {
                "frameCreated": False,
                "lastError": "BRIDGE_ERROR",
                "workerError": "BRIDGE_ERROR",
                "familyFrames": 0,
            },
        )

    def test_late_ready_after_timeout_is_ignored_and_retry_gets_new_nonce(self):
        self._prepare_delayed_handshake_page()
        self._start_delayed_request("timed-out-request")
        first_nonce = self.page.evaluate(
            "() => new URL(window.__familyFrame.src).searchParams.get('bridgeNonce')"
        )
        self.page.evaluate("() => window.__timeoutHandlers[0]()")
        self.page.wait_for_function("() => window.__workerMessages.length === 1")
        timeout_response = self.page.evaluate("() => window.__workerMessages[0]")
        self.assertEqual(timeout_response["response"]["error"], "TIMEOUT")

        self._dispatch_ready(first_nonce)
        self.page.wait_for_timeout(25)
        self.assertEqual(
            self.page.evaluate("() => window.__sentBridgeMessages.length"),
            0,
        )
        self.assertEqual(
            self.page.evaluate("() => window.__workerMessages.length"),
            1,
        )

        self._start_delayed_request("retry-request")
        second_nonce = self.page.evaluate(
            "() => new URL(window.__familyFrame.src).searchParams.get('bridgeNonce')"
        )
        self.assertRegex(second_nonce, r"^[a-f0-9]{64}$")
        self.assertNotEqual(second_nonce, first_nonce)

    def test_one_timeout_does_not_abort_another_pending_handshake(self):
        self._prepare_delayed_handshake_page()
        self._start_delayed_request("first-request")
        self._start_delayed_request("second-request")
        nonce = self.page.evaluate(
            "() => new URL(window.__familyFrame.src).searchParams.get('bridgeNonce')"
        )

        self.page.evaluate("() => window.__timeoutHandlers[0]()")
        self.page.wait_for_function("() => window.__workerMessages.length === 1")
        first_response = self.page.evaluate("() => window.__workerMessages[0]")
        self.assertEqual(first_response["requestId"], "first-request")
        self.assertEqual(first_response["response"]["error"], "TIMEOUT")
        self.assertTrue(
            self.page.evaluate("() => window.gumliFamilyDebug.frameCreated")
        )

        self._dispatch_ready(nonce)
        self.page.wait_for_function("() => window.__sentBridgeMessages.length === 1")
        sent = self.page.evaluate("() => window.__sentBridgeMessages[0]")
        self.assertEqual(sent["message"]["requestId"], "second-request")
        self.assertEqual(
            self.page.evaluate("() => window.__workerMessages.length"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
