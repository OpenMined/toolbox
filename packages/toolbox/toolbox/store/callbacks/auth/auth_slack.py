#!/usr/bin/env python3
"""
Slack Authentication using Playwright

This script uses Playwright to authenticate with Slack and extract client tokens.
Based on the slackdump Go implementation for browser authentication.

Usage:
    python slack_auth.py <workspace_name>

Requirements:
    pip install playwright typer
    playwright install
"""

import asyncio
import os
from pathlib import Path
from pprint import pprint
import re
import sys
import time
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse, parse_qs
from urllib.parse import parse_qs

import typer
from playwright.async_api import async_playwright, Page, Request, Response, Cookie
from slack_sdk import WebClient

from toolbox.settings import settings


MACOS_CHROME_USER_DATA_DIR = Path(
    "~/Library/Application Support/Google/Chrome"
).expanduser()


class SlackAuth:
    """Slack authentication using Playwright browser automation."""

    SLACK_DOMAIN = ".slack.com"
    TOKEN_PATTERN = re.compile(r"xoxc-[0-9]+-[0-9]+-[0-9]+-[0-9a-z]{64}")
    REQUEST_TIMEOUT = 600000  # 10 minutes in milliseconds

    def __init__(
        self,
        workspace: str,
        headless: bool = False,
        browser_type: str = "chromium",
    ):
        """
        Initialize SlackAuth.

        Args:
            workspace: Slack workspace name (e.g., "mycompany")
            headless: Run browser in headless mode
            browser_type: Browser type ("firefox", "chromium", "webkit")
        """
        if sys.platform != "darwin":
            raise RuntimeError("This script currently only supports macOS (darwin).")

        self.workspace = workspace.lower().strip()
        self.headless = headless
        self.browser_type = browser_type
        self.page_closed = False

        if not self.workspace:
            raise ValueError("Workspace name cannot be empty")

    async def authenticate(self) -> Tuple[str, List[Dict]]:
        """
        Authenticate with Slack and extract client token and cookies.

        Returns:
            Tuple of (token, cookies) where cookies is a list of cookie dictionaries
        """
        async with async_playwright() as p:
            # Launch browser
            browser = await self._launch_browser(p)

            try:
                # Use a persistent context with a custom user data dir to look more like a real browser
                # import tempfile

                # user_data_dir = tempfile.mkdtemp(prefix="slackauth-profile-")

                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                    viewport={"width": 1280, "height": 900},
                    ignore_https_errors=False,
                    storage_state=None,
                    record_video_dir=None,
                    record_har_path=None,
                    accept_downloads=True,
                    color_scheme="light",
                    timezone_id="America/Los_Angeles",
                    permissions=["geolocation", "notifications"],
                    base_url=None,
                    extra_http_headers={
                        "sec-ch-ua": '"Chromium";v="120", "Not:A-Brand";v="99"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Macintosh"',
                    },
                )

                # Disable cookie consent nag screen
                await context.add_cookies(
                    [
                        {
                            "name": "OptanonAlertBoxClosed",
                            "value": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 600)
                            ),
                            "domain": self.SLACK_DOMAIN,
                            "path": "/",
                            "expires": int(time.time())
                            + (30 * 24 * 60 * 60),  # 30 days
                        }
                    ]
                )

                # Create page and set up monitoring
                page = await context.new_page()
                page.on("close", self._on_page_close)

                # Navigate to workspace
                workspace_url = f"https://{self.workspace}{self.SLACK_DOMAIN}"
                print(f"Opening browser to: {workspace_url}")
                await page.goto(workspace_url)

                # Wait for authentication and extract token
                token = await self._wait_for_token(page)

                # Get cookies from the context
                cookies = await context.cookies()

                return token, self._convert_cookies(cookies)

            finally:
                await browser.close()

    async def _launch_browser(self, playwright):
        """Launch the specified browser with arguments to bypass Google 'not secure' warning."""
        browser_types = {
            "chromium": playwright.chromium,
        }

        if self.browser_type not in browser_types:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")

        browser_launcher = browser_types[self.browser_type]

        # Use Chromium by default for best compatibility with Google Auth
        launch_args = []
        if self.browser_type == "chromium":
            # These flags help bypass "not secure" and automation detection
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-domain-reliability",
                "--disable-features=site-per-process,TranslateUI,BlinkGenPropertyTrees",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--password-store=basic",
                "--use-mock-keychain",
                "--lang=en-US",
            ]
        return await browser_launcher.launch(
            headless=self.headless,
            args=launch_args,
            # channel="chrome",  # Uncomment if you have Chrome installed and want to use it
        )

    def _on_page_close(self):
        """Handle page close event."""
        self.page_closed = True
        print("Browser page was closed")

    async def _wait_for_token(self, page: Page) -> str:
        """
        Wait for Slack authentication and extract token from API request.

        Args:
            page: Playwright page object

        Returns:
            Extracted client token
        """
        workspace_url = f"https://{self.workspace}{self.SLACK_DOMAIN}"
        api_pattern = f"{workspace_url}/api/api.features*"

        print("Waiting for authentication...")
        print("Please log in to Slack in the browser window that opened.")

        try:
            # Wait for the API request that contains the token
            async with page.expect_request(
                api_pattern, timeout=self.REQUEST_TIMEOUT
            ) as request_info:
                pass

            request = await request_info.value
            token = await self._extract_token(request)

            if not token:
                raise ValueError("Could not extract token from request")

            print(f"Successfully extracted token: {token[:20]}...")
            return token

        except Exception as e:
            if self.page_closed:
                raise RuntimeError(
                    "Browser was closed before authentication completed"
                ) from e
            raise RuntimeError(f"Authentication failed: {e}") from e

    async def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract token from a Playwright request.

        Args:
            request: Playwright request object

        Returns:
            Extracted token or None if not found
        """
        try:
            if request.method == "GET":
                return self._extract_token_from_url(request.url)
            elif request.method == "POST":
                return await self._extract_token_from_post(request)
            else:
                print(f"Unsupported request method: {request.method}")
                return None

        except Exception as e:
            print(f"Error extracting token: {e}")
            return None

    def _extract_token_from_url(self, url: str) -> Optional[str]:
        """Extract token from URL query parameters."""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            if "token" in query_params:
                token = query_params["token"][0]
                if self.TOKEN_PATTERN.match(token):
                    return token
                else:
                    print(f"Invalid token format: {token}")
                    return None
            else:
                print("No token found in URL parameters")
                return None

        except Exception as e:
            print(f"Error parsing URL: {e}")
            return None

    async def _extract_token_from_post(self, request: Request) -> Optional[str]:
        """Extract token from POST request body."""
        try:
            # Get the request body
            post_data = request.post_data
            if not post_data:
                print("No POST data found")
                return None

            # Check content type
            content_type = request.headers.get("content-type", "")

            if "multipart/form-data" in content_type:
                # Extract boundary from content-type
                boundary = self._extract_boundary(content_type)
                if boundary:
                    return self._extract_token_from_multipart(post_data, boundary)
            elif "application/x-www-form-urlencoded" in content_type:
                return self._extract_token_from_form_data(post_data)
            else:
                print(f"Unsupported content type: {content_type}")
                return None

        except Exception as e:
            print(f"Error extracting token from POST: {e}")
            return None

    def _extract_boundary(self, content_type: str) -> Optional[str]:
        """Extract boundary from multipart content-type header."""
        try:
            parts = content_type.split(";")
            for part in parts:
                part = part.strip()
                if part.startswith("boundary="):
                    return part[9:]  # Remove 'boundary=' prefix
            return None
        except Exception:
            return None

    def _extract_token_from_multipart(self, data: str, boundary: str) -> Optional[str]:
        """Extract token from multipart form data."""
        try:
            # Simple multipart parsing - look for token field
            parts = data.split(f"--{boundary}")
            for part in parts:
                if 'name="token"' in part:
                    lines = part.split("\r\n")
                    for i, line in enumerate(lines):
                        if line.strip() == "" and i + 1 < len(lines):
                            token = lines[i + 1].strip()
                            if self.TOKEN_PATTERN.match(token):
                                return token
            return None
        except Exception as e:
            print(f"Error parsing multipart data: {e}")
            return None

    def _extract_token_from_form_data(self, data: str) -> Optional[str]:
        """Extract token from URL-encoded form data."""
        try:
            params = parse_qs(data)
            if "token" in params:
                token = params["token"][0]
                if self.TOKEN_PATTERN.match(token):
                    return token
            return None
        except Exception as e:
            print(f"Error parsing form data: {e}")
            return None

    def _convert_cookies(self, playwright_cookies: List[Cookie]) -> List[Dict]:
        """Convert Playwright cookies to standard dictionary format."""
        converted = []

        for cookie in playwright_cookies:
            cookie_dict = {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
                "expires": cookie.get("expires", -1),
                "httpOnly": cookie.get("httpOnly", False),
                "secure": cookie.get("secure", False),
                "sameSite": cookie.get("sameSite", "Lax"),
            }
            converted.append(cookie_dict)

        return converted

    def format_cookies_for_http(self, cookies: List[Dict]) -> str:
        """Format cookies for HTTP Cookie header."""
        cookie_parts = []
        for cookie in cookies:
            cookie_parts.append(f"{cookie['name']}={cookie['value']}")
        return "; ".join(cookie_parts)

    def get_d_cookie(self, cookies: List[Dict]) -> Optional[str]:
        """Extract the 'd' cookie value (xoxd-* session token)."""
        for cookie in cookies:
            if cookie["name"] == "d":
                return cookie["value"]
        return None


app = typer.Typer(help="Slack Authentication using Playwright")


def do_browser_auth(workspace: str, browser: str):  # Validate browser choice
    if browser not in ["firefox", "chromium", "webkit"]:
        typer.echo(f"Error: Unsupported browser type: {browser}")
        typer.echo("Supported browsers: firefox, chromium, webkit")
        raise typer.Exit(1)

    async def run_auth():
        try:
            auth = SlackAuth(
                workspace,
                headless=False,
                browser_type=browser,
            )
            token, cookies = await auth.authenticate()

            typer.echo(f"Token: {token}")
            d_cookie = auth.get_d_cookie(cookies)
            if d_cookie:
                typer.echo(f"Session Cookie (d): {d_cookie}")
            typer.echo(f"Cookie Header: {auth.format_cookies_for_http(cookies)}")
            typer.echo(f"Total cookies: {len(cookies)}")
            return token, d_cookie
        except KeyboardInterrupt:
            typer.echo("\nAuthentication cancelled by user")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1)

    # Run the async function
    if settings.skip_slack_auth:
        print("Skipping Slack authentication, reading from env")
        token = os.getenv("SLACK_TOKEN")
        d_cookie = os.getenv("SLACK_D_COOKIE")
        return token, d_cookie

    token, d_cookie = asyncio.run(run_auth())
    print("")
    headers = {
        "Cookie": f"d={d_cookie}",
        "User-Agent": "Mozilla/5.0 (compatible; Python)",
    }
    client = WebClient(token=token, headers=headers)

    response = client.conversations_history(channel="D01LM1NMJ0J", limit=3)
    pprint(response["messages"])
    return token, d_cookie


@app.command()
def authenticate(
    workspace: str = typer.Argument(
        ..., help="Slack workspace name (e.g., 'mycompany')"
    ),
    browser: str = typer.Option("firefox", "--browser", help="Browser type to use"),
):
    """Authenticate with Slack and extract client token."""
    do_browser_auth(workspace, browser)


if __name__ == "__main__":
    app()
