import asyncio
import json
import random
import time
from datetime import datetime
from http.cookiejar import Cookie
from pathlib import Path
from typing import Any, Callable

import browser_cookie3
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from omni.data_fetchers.job_queue import DataFetcherJobQueue
from omni.data_fetchers.x_utils import parse_tweets_json
from omni.db import get_tweet_store

BASE_DIR = Path.home() / ".omni"
DATA_FETCHER_DIR = BASE_DIR / "scraper_data"
COOKIES_FILE = DATA_FETCHER_DIR / "x_cookies.json"
DATA_DIR = DATA_FETCHER_DIR / "data"


def cookie_to_playwright_cookie(cookie: Cookie) -> dict:
    cookie_dict = {
        "name": cookie.name,
        "value": cookie.value,
        "domain": cookie.domain.lstrip("."),  # Playwright expects no leading dot
        "path": cookie.path,
        "secure": bool(cookie.secure),
        "httpOnly": getattr(cookie, "httponly", False)
        or cookie.get_nonstandard_attr("HttpOnly", False),
    }
    # Optional: expires
    if cookie.expires is not None:
        cookie_dict["expires"] = cookie.expires
    return cookie_dict


def get_cookies_from_brave() -> list[Cookie]:
    """Extract auth cookies from browser"""
    x_cookies = []
    for c in browser_cookie3.brave(domain_name="x.com"):
        if c.domain == ".x.com" and c.name in ["auth_token"]:
            x_cookies.append(c)
            print("Found x auth_token")

    print(x_cookies)
    return x_cookies


def save_cookies_to_file(cookies: list[dict]) -> None:
    """Save cookies to a JSON file"""
    DATA_FETCHER_DIR.mkdir(parents=True, exist_ok=True)
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
        print(f"Saved {len(cookies)} cookies to {COOKIES_FILE}")


def load_cookies_from_file() -> list[dict] | None:
    """Load cookies from a JSON file"""
    if COOKIES_FILE.is_file():
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
            print(f"Loaded {len(cookies)} cookies from {COOKIES_FILE}")
            return cookies
    return


def get_cookies_for_playwright(reload: bool = True) -> list[dict]:
    """Get cookies in Playwright format"""
    cookies = load_cookies_from_file()
    if cookies is not None and not reload:
        return cookies

    x_cookies = get_cookies_from_brave()
    cookies = [cookie_to_playwright_cookie(c) for c in x_cookies]

    save_cookies_to_file(cookies)
    return cookies


async def setup_browser(
    x_cookies: list[dict],
    headless: bool = False,
) -> tuple[Browser, BrowserContext, Page]:
    """Setup browser with authentication cookies"""

    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=headless)
    context = await browser.new_context()

    # Set cookies before navigating
    await context.add_cookies(x_cookies)

    # Print all cookies currently in the context
    cookies_in_context = await context.cookies()
    print("All cookies in context after setting:")
    for cookie in cookies_in_context:
        print(cookie)

    page = await context.new_page()

    return browser, context, page


def save_home_timeline(json_data: Any) -> None:
    """Default save function for timeline data"""

    dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"home_latest_timeline_{dt_str}.json"
    output_path = DATA_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(json_data, f)
    print(f"Saved JSON to {filename}")


def is_home_timeline_url(url: str) -> bool:
    """Check if URL is a home timeline API endpoint"""
    if "graphql" in url and ("HomeLatestTimeline" in url or "HomeTimeline" in url):
        return True
    return False


async def scroll_vertical_mousewheel(
    page: Page,
    duration: int,
    distance_range: tuple[int, int] = (200, 1000),
    delay_range: tuple[float, float] = (1, 5),
):
    start_time = time.time()

    while time.time() - start_time < duration:
        scroll_distance = random.randint(*distance_range)
        await page.mouse.wheel(0, scroll_distance)
        await asyncio.sleep(random.uniform(*delay_range))


async def fetch_timeline(
    page: Page,
    duration: int = 60,
    save_fn: Callable[[Any], None] = save_home_timeline,
):
    """Fetch timeline data from X/Twitter"""

    async def handle_timeline_request(request):
        """Intercept and save timeline API responses"""
        if is_home_timeline_url(request.url):
            response = await request.response()
            if response is not None:
                try:
                    json_data = await response.json()
                    save_fn(json_data)
                except Exception as e:
                    print(f"Failed to get JSON from response: {e}")
            print("API call to HomeLatestTimeline")

    # Setup request interception
    page.on("request", handle_timeline_request)

    # Navigate to X.com
    await page.goto("https://x.com")
    await asyncio.sleep(3)

    # Click "Following" to switch to chronological timeline
    following_span = await page.query_selector("span:has-text('Following')")
    if following_span:
        await click_element_human_like(page, following_span)
        print("Clicked the 'Following' button.")
    else:
        print("Could not find the 'Following' button.")

    # Keep scraping for specified duration
    await scroll_vertical_mousewheel(page, duration)


async def click_element_human_like(page: Page, element):
    """Click a button with human-like mouse movement"""
    box = await element.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)

        # Move and click
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await page.mouse.click(x, y)
        return True
    return False


async def get_follow_button(page: Page, handle: str):
    """Get the follow button element for a specific user by their handle"""
    username = handle.lstrip("@").lower()

    # Use evaluate to find button with case-insensitive matching
    follow_button = await page.evaluate_handle(
        """
        (username) => {
            const buttons = document.querySelectorAll('[data-testid*="-follow"]:not([data-testid*="-unfollow"])');
            for (const button of buttons) {
                const ariaLabel = button.getAttribute('aria-label');
                if (ariaLabel && ariaLabel.toLowerCase().includes('@' + username)) {
                    return button;
                }
            }
            return null;
        }
    """,
        username,
    )

    # Convert handle to element or return None
    element = follow_button.as_element() if follow_button else None
    return element


async def get_unfollow_button(page: Page, handle: str):
    """Get the unfollow button element for a specific user by their handle"""
    username = handle.lstrip("@").lower()

    # Use evaluate to find button with case-insensitive matching
    unfollow_button = await page.evaluate_handle(
        """
        (username) => {
            const buttons = document.querySelectorAll('[data-testid*="-unfollow"]');
            for (const button of buttons) {
                const ariaLabel = button.getAttribute('aria-label');
                if (ariaLabel && ariaLabel.toLowerCase().includes('@' + username)) {
                    return button;
                }
            }
            return null;
        }
    """,
        username,
    )

    # Convert handle to element or return None
    element = unfollow_button.as_element() if unfollow_button else None
    return element


async def follow_user(page: Page, handle: str):
    """Follow a specific user by their handle"""

    # Navigate to user's profile
    profile_url = f"https://x.com/{handle.lstrip('@')}"
    await page.goto(profile_url)
    await asyncio.sleep(3)

    # Find follow button for this specific user using partial aria-label (for localization)
    follow_button = await get_follow_button(page, handle)

    if follow_button:
        clicked = await click_element_human_like(page, follow_button)
        if clicked:
            # Wait and verify
            await asyncio.sleep(random.uniform(1.5, 3))
            following_button = await get_unfollow_button(page, handle)
            if following_button:
                print(f"Successfully followed {handle}")
            else:
                print(f"Follow may have failed for {handle}")
    elif await get_unfollow_button(page, handle):
        print(f"Already following {handle}")
    else:
        print(f"Could not find follow button for {handle}, user may not exist.")


async def follow_users(
    page: Page, handles: list[str], delay_range: tuple[float, float] = (2, 5)
):
    """Follow multiple users with random delays between each"""

    for i, handle in enumerate(handles):
        print(f"\n[{i + 1}/{len(handles)}] Processing {handle}")
        await follow_user(page, handle)

        # Add random delay between follows (except after the last one)
        if i < len(handles) - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            print(f"Waiting {delay:.1f} seconds before next follow...")
            await asyncio.sleep(delay)

    print(f"\nCompleted processing {len(handles)} handles")


async def run_x_fetcher(
    fetch_timeline_duration: int = 0,
    handles_to_follow: list[str] = None,
    headless: bool = False,
    timeline_save_fn: Callable[[Any], None] = save_home_timeline,
):
    """Run the X data fetcher.

    Args:
        fetch_timeline_duration (int, optional): Duration to fetch the timeline. Defaults to None.
        handles_to_follow (list[str], optional): List of user handles to follow. Defaults to None.
        headless (bool, optional): Run browser in headless mode. Defaults to False.
    """

    if not fetch_timeline_duration and not handles_to_follow:
        print("Nothing to do, exiting.")
        return

    # Get auth cookies
    cookies = get_cookies_for_playwright()
    if not cookies:
        print("No auth cookies found. Please login to X.com in your browser first.")
        return

    # Setup browser with cookies
    browser, context, page = await setup_browser(cookies, headless=headless)

    try:
        if handles_to_follow:
            await follow_users(page, handles_to_follow)
        if fetch_timeline_duration:
            if handles_to_follow:
                print("Waiting before starting timeline fetching...")
                await asyncio.sleep(random.uniform(2, 5))
            await fetch_timeline(
                page,
                fetch_timeline_duration,
                save_fn=timeline_save_fn,
            )

    finally:
        await browser.close()


def save_tweets_to_file(json_data: Any) -> None:
    """Default save function for timeline data"""

    dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"home_latest_timeline_{dt_str}.json"
    output_path = DATA_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(json_data, f)
    print(f"Saved JSON to {filename}")


def save_tweets_to_store(json_data: Any) -> None:
    # Parse tweets from JSON
    tweets = parse_tweets_json(json_data)

    if tweets:
        # NOTE tweet store is initialized here because sqlite3 is not
        # thread-safe.
        store = get_tweet_store()
        store.insert_docs(
            tweets,
            create_embeddings=True,
            overwrite=True,
        )
        store.close()
        print(f"Saved {len(tweets)} tweets to store.")
    else:
        print("No tweets found in JSON data")


class XDataFetcher(DataFetcherJobQueue):
    def __init__(
        self,
        max_job_age=300,
        max_queue_size=None,
        worker_delay=0,
        headless: bool = True,
        timeline_save_fn: Callable[[Any], None] = save_tweets_to_store,
    ):
        super().__init__(max_job_age, max_queue_size, worker_delay)
        self.headless = headless
        self.timeline_save_fn = timeline_save_fn

    def start(
        self,
        download_schedule: int | tuple[int, int] | None = None,
    ) -> None:
        """Start the data fetcher, with optional regular timeline downloading.

        Args:
            download_schedule (int | tuple[int, int] | None, optional): Interval in seconds or
                (min, max) tuple for random interval. If None, no scheduled downloading. Defaults to None.

        """
        if download_schedule:
            self.add_schedule(
                func=self._fetch_timeline_job,
                interval=download_schedule,
                kwargs={"fetch_timeline_duration": 60},
            )

        return super().start()

    def add_follow_users_job(
        self, handles: list[str], fetch_timeline_duration: int = 0
    ):
        self.add_job(
            func=self._follow_users_job,
            kwargs={
                "handles": handles,
                "fetch_timeline_duration": fetch_timeline_duration,
            },
        )

    def add_fetch_timeline_job(self, fetch_timeline_duration: int = 30):
        # allow_duplicates=False to avoid multiple timeline fetches in queue
        self.add_job(
            func=self._fetch_timeline_job,
            kwargs={"fetch_timeline_duration": fetch_timeline_duration},
            allow_duplicates=False,
            timeline_save_fn=self.timeline_save_fn,
        )

    def _fetch_timeline_job(self, fetch_timeline_duration: int = 30):
        asyncio.run(
            run_x_fetcher(
                fetch_timeline_duration=fetch_timeline_duration,
                handles_to_follow=None,
                headless=self.headless,
                timeline_save_fn=self.timeline_save_fn,
            )
        )

    def _follow_users_job(self, handles: list[str], fetch_timeline_duration: int = 0):
        asyncio.run(
            run_x_fetcher(
                fetch_timeline_duration=fetch_timeline_duration,
                handles_to_follow=handles,
                headless=self.headless,
                timeline_save_fn=self.timeline_save_fn,
            )
        )


if __name__ == "__main__":
    scraper = XDataFetcher(
        headless=False,
    )
    scraper.start()

    # Example: follow specific users once
    handles_to_follow = [
        "openai",
    ]
    # scraper.add_scrape_timeline_job(scrape_timeline_duration=30)
    scraper.add_follow_users_job(handles=handles_to_follow, fetch_timeline_duration=10)

    time.sleep(300)
    scraper.stop()
