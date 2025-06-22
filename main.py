#!/usr/bin/env python3
import asyncio
import aiohttp
import aiofiles
from selenium import webdriver

# should be 256 but that isn't working
max_filename_length = 200

# very smart function, repurposed from https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/utils/_utils.py#L627
def sanitize_filename(s):
    """Sanitizes a string so it could be used as part of a filename."""
    if s == '':
        return ''

    def replace_insane(char):
        if char == '\n':
            return '\0 '
        elif char in '"*:<>?|/\\':
            # Replace with their full-width unicode counterparts
            return {'/': '\u29F8', '\\': '\u29f9'}.get(char, chr(ord(char) + 0xfee0))
        elif char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '\''
        elif char == ':':
            return '\0 \0-'
        elif char in '\\/|*<>':
            return '\0_'
        return char

    result = ''.join(map(replace_insane, s))
    result = result.replace('\0', '') or '_'

    return result


def get_available_driver():
    from selenium.common.exceptions import WebDriverException

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException:
        pass

    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.page_load_strategy = 'eager'
        driver = webdriver.Firefox(options=options)
        return driver
    except WebDriverException:
        pass

    try:
        options = webdriver.SafariOptions()
        options.page_load_strategy = 'eager'
        driver = webdriver.Safari(options=options)
        return driver
    except Exception: # nice "Exception" buddy...
        pass

    try:
        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        options.page_load_strategy = 'eager'
        driver = webdriver.Edge(options=options)
        return driver
    except WebDriverException:
        pass

    print("No supported browser found.\nPlease install: Chrome, Firefox, Safari or Edge.")
    exit(1)


async def download(session, url, save_path):
    try:
        async with aiofiles.open(save_path, 'xb') as f:
            async with session.get(url) as resp:
                content = await resp.read()
                await f.write(content)
    except FileExistsError:
        pass


async def main():
    import os
    import sys
    import getpass
    from selenium_recaptcha_solver import RecaptchaSolver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.wait import WebDriverWait

    if len(sys.argv) <= 1:
        print("Usage: main.py <download_dir>")
        exit(1)

    download_dir = sys.argv[1]
    username = input("Username or Email: ")
    password = getpass.getpass("Password: ")

    print("Opening browser...")
    driver = get_available_driver()
    captcha_solver = RecaptchaSolver(driver=driver)

    print("Logging in...")
    driver.get("https://nhentai.net/login/?next=/favorites/")

    # recaptcha is too slow for 'eager' page load strategy
    wait = WebDriverWait(driver, timeout=5)
    wait.until(lambda _: driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]'))

    username_field = driver.find_element(by=By.NAME, value="username_or_email")
    password_field = driver.find_element(by=By.NAME, value="password")
    submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")
    recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

    username_field.send_keys(username)
    password_field.send_keys(password)

    captcha_solver.click_recaptcha_v2(iframe=recaptcha_iframe)

    submit_button.click()

    selenium_cookies = driver.get_cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}

    ids = []
    titles = []

    while True:
        favorites = driver.find_elements(By.CLASS_NAME, "gallery-favorite")

        for favorite in favorites:
            ids.append(favorite.get_attribute("data-id"))
            titles.append(favorite.find_element(By.CLASS_NAME, "caption").text)
            sys.stdout.write(f"\rLoading favorites {len(ids)}")
            sys.stdout.flush()

        next_buttons = driver.find_elements(By.CLASS_NAME, "next")
        if next_buttons == []:
            break

        next_buttons[0].click()
    print()

    favorites_amount = len(ids)
    print(f"Downloading {favorites_amount} favorites...")

    async with aiohttp.ClientSession(cookies=cookies) as session:
        tasks = []
        for i in range(favorites_amount):
            sys.stdout.write(f"\rDownloading favorite {i}")
            sys.stdout.flush()
            save_path = os.path.join(os.path.expanduser(download_dir), sanitize_filename(titles[i][:max_filename_length:]) + ".torrent")
            task = asyncio.create_task(download(session, f"https://nhentai.net/g/{id}/download", save_path))
            tasks.append(task)
        await asyncio.gather(*tasks)
    print()

asyncio.run(main())
