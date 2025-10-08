import asyncio
import json
from http.cookiejar import Cookie
from pathlib import Path

import browser_cookie3

# Keep all cookies that might be relevant for authentication
x_cookies = []
for c in browser_cookie3.brave(domain_name="x.com"):
    if c.domain == ".x.com" and c.name in ["auth_token"]:
        x_cookies.append(c)
        print("Found x auth_token")

print(x_cookies)


def cookie_to_playwright_cookie(cookie: Cookie) -> dict:
    cookie_dict = {
        "name": cookie.name,
        "value": cookie.value,
        "domain": cookie.domain.lstrip("."),  # Playwright expects no leading dot
        "path": cookie.path,
        "secure": bool(cookie.secure),
        "httpOnly": getattr(cookie, "httponly", False)
        or c.get_nonstandard_attr("HttpOnly", False),
    }
    # Optional: expires
    if cookie.expires is not None:
        cookie_dict["expires"] = cookie.expires
    return cookie_dict


def is_home_latest_timeline_url(url):
    if "graphql" in url and ("HomeLatestTimeline" in url or "HomeTimeline" in url):
        return True
    return False


async def on_request(request):
    if is_home_latest_timeline_url(request.url):
        # INSERT_YOUR_CODE
        response = await request.response()
        if response is not None:
            try:
                json_data = await response.json()
                from datetime import datetime

                dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"home_latest_timeline_{dt_str}.json"
                output_path = Path(".").parent / "data" / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    json.dump(json_data, f)
                print(f"Saved JSON to {filename}")
            except Exception as e:
                print(f"Failed to get JSON from response: {e}")

        print("API call to HomeLatestTimeline")


async def playwright_login_with_cookies():
    from playwright.async_api import async_playwright

    # Use the first cookie found (auth_token) for x.com
    cookies = []
    for c in x_cookies:
        cookies.append(cookie_to_playwright_cookie(c))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        # Set cookies before navigating
        await context.add_cookies(cookies)
        # Print all cookies currently in the context
        cookies_in_context = await context.cookies()
        print("All cookies in context after setting:")
        for cookie in cookies_in_context:
            print(cookie)
        page = await context.new_page()
        await asyncio.sleep(3)
        page.on("request", on_request)

        await page.goto("https://x.com")

        # INSERT_YOUR_CODE
        # Print all spans content with class "r-poiln3"
        await asyncio.sleep(3)

        # INSERT_YOUR_CODE
        # Find the span (button) that says "Following" and click it
        following_span = await page.query_selector("span:has-text('Following')")
        if following_span:
            await following_span.click()
            print("Clicked the 'Following' button.")
        else:
            print("Could not find the 'Following' button.")

        # spans = await page.query_selector_all("span.r-poiln3")
        # print("Contents of all <span class='r-poiln3'> elements:")
        # for span in spans:
        #     text = await span.text_content()
        #     print(text)
        await asyncio.sleep(10000)
        await browser.close()


# Run the async function
asyncio.run(playwright_login_with_cookies())
