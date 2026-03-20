"""Playwright E2E tests against OpenWebUI on L2.

Run via::

    ./scripts/run_e2e.sh

Or directly::

    pytest tests/e2e/ -m e2e -v --timeout=120

Requires:
    - SSH tunnel to L2 (port 3100)
    - RARE_ARCHIVE_OPENWEBUI_USER / _PASS env vars
    - playwright browsers installed (``playwright install chromium``)

NOTE: DOM selectors are initial guesses based on OpenWebUI 0.4.x markup.
First run will likely require adjustment via ``playwright codegen``.
"""

import re

import pytest

# playwright is an optional dep — guard the import so collection doesn't
# fail when running non-e2e tests.
pw = pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect, sync_playwright


RESPONSE_TIMEOUT_MS = 90_000  # 90 s for model + tool calls


@pytest.fixture(scope="session")
def browser():
    """Launch a shared Chromium instance for the whole test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def authenticated_context(browser, e2e_config):
    """Create a browser context and log in once for the session."""
    context = browser.new_context()
    page = context.new_page()

    # Navigate to OpenWebUI
    page.goto(e2e_config.url, wait_until="networkidle")

    # Login — selectors are best-effort for OpenWebUI 0.4.x
    # If these fail, run ``playwright codegen <url>`` to discover current selectors.
    page.fill('input[type="email"], input[name="email"], input[placeholder*="email" i]', e2e_config.user)
    page.fill('input[type="password"], input[name="password"]', e2e_config.password)
    page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")')

    # Wait for main chat interface to load
    page.wait_for_selector(
        'textarea, div[contenteditable="true"], #chat-input',
        timeout=15_000,
    )

    yield context
    context.close()


@pytest.mark.e2e
class TestOpenWebUIScenarios:
    """Parameterized E2E tests — one per demo scenario."""

    def test_scenario(self, authenticated_context, e2e_config, scenario):
        """Submit a clinical query and verify the response contains expected keywords."""
        page = authenticated_context.new_page()

        try:
            # Navigate to new chat
            page.goto(e2e_config.url, wait_until="networkidle")

            # Click "New Chat" if available (otherwise we're already on a fresh chat)
            new_chat = page.locator(
                'button:has-text("New Chat"), a:has-text("New Chat"), '
                'button[aria-label="New Chat"]'
            )
            if new_chat.count() > 0:
                new_chat.first.click()
                page.wait_for_timeout(1000)

            # Type the clinical query
            input_area = page.locator(
                'textarea, div[contenteditable="true"], #chat-input'
            ).first
            input_area.fill(scenario.query)

            # Submit
            submit_btn = page.locator(
                'button[type="submit"], button[aria-label="Send"], '
                'button:has-text("Send")'
            )
            if submit_btn.count() > 0:
                submit_btn.first.click()
            else:
                input_area.press("Enter")

            # Wait for response — look for assistant message container
            # OpenWebUI renders responses in divs with role or class markers.
            page.wait_for_timeout(3000)  # initial delay for model to start

            # Wait until response text appears (poll for up to RESPONSE_TIMEOUT_MS)
            response_locator = page.locator(
                '.assistant-message, [data-role="assistant"], '
                '.chat-message:last-child, .message-content:last-child'
            )

            # Wait for at least one response element to be visible
            response_locator.first.wait_for(
                state="visible", timeout=RESPONSE_TIMEOUT_MS
            )

            # Wait a bit more for the full response to render
            page.wait_for_timeout(5000)

            # Get the full page text content for keyword matching
            page_text = page.inner_text("body")

            # Assert expected keywords are present (case-insensitive)
            for keyword in scenario.expected_keywords:
                assert re.search(
                    re.escape(keyword), page_text, re.IGNORECASE
                ), f"Expected keyword '{keyword}' not found in response for {scenario.name}"

            # Screenshot for audit trail
            screenshot_path = e2e_config.screenshot_dir / f"{scenario.id}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)

        finally:
            page.close()
