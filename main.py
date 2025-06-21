#!/usr/bin/env python3
from selenium import webdriver

# should be 256 but that wasn't working
max_filename_length = 200

# very smart function, reporposed from https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/utils/_utils.py#L627
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
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException:
        pass

    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        return driver
    except WebDriverException:
        pass

    try:
        driver = webdriver.Safari()
        return driver
    except Exception: # nice "Exception" buddy...
        pass

    try:
        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Edge(options=options)
        return driver
    except WebDriverException:
        pass

    print("No supported browser found.\nPlease install: Chrome, Firefox, Safari or Edge.")
    exit(1)

def main():
    import os
    import sys
    import requests
    import getpass
    from selenium_recaptcha_solver import RecaptchaSolver
    from selenium.webdriver.common.by import By

    if len(sys.argv) <= 1:
        print("Usage: main.py <download_dir>")
        exit(1)

    download_dir = sys.argv[1]
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    driver = get_available_driver()
    captcha_solver = RecaptchaSolver(driver=driver)

    driver.get("https://nhentai.net/login/?next=/favorites/")

    username_field = driver.find_element(by=By.NAME, value="username_or_email")
    password_field = driver.find_element(by=By.NAME, value="password")
    submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")
    recaptcha_iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')

    username_field.send_keys(username)
    password_field.send_keys(password)

    captcha_solver.click_recaptcha_v2(iframe=recaptcha_iframe)

    submit_button.click()

    selenium_cookies = driver.get_cookies()
    session = requests.Session()

    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    while True:
        gallery = driver.find_element(By.ID, "favcontainer")
        favorites = gallery.find_elements(By.CLASS_NAME, "gallery-favorite")

        for favorite in favorites:
            id = favorite.get_attribute("data-id")
            title = favorite.find_element(By.CLASS_NAME, "caption").text
            save_path = os.path.join(os.path.expanduser(download_dir), sanitize_filename(title[:max_filename_length:]) + ".torrent")

            try:
                with open(save_path, "xb") as f:
                    response = session.get(f"https://nhentai.net/g/{id}/download")
                    f.write(response.content)
            except FileExistsError:
                pass

        next_buttons = driver.find_elements(By.CLASS_NAME, "next")
        if next_buttons == []:
            break

        next_buttons[0].click()

main()
