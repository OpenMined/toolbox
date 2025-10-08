from omni.data_fetchers.x_fetcher import (
    cookie_to_playwright_cookie,
    get_cookies_from_brave,
    save_cookies_to_file,
)

cookies = get_cookies_from_brave()
cookies = [cookie_to_playwright_cookie(c) for c in cookies]
save_cookies_to_file(cookies)
