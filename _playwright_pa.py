from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        headless=False
    )
    page = browser.new_page()
    page.goto("https://www.pythonanywhere.com/login/?next=/")
    time.sleep(3)
    page.fill("input[name=auth-username]", "liudapao")
    page.fill("input[name=auth-password]", "asdke0735")
    page.click("button[type=submit]")
    time.sleep(3)

    # Go to Bash console
    page.goto("https://www.pythonanywhere.com/user/liudapao/consoles/")
    time.sleep(3)

    # Click "Bash" button
    page.click("text=Bash")
    time.sleep(5)

    # Type command
    page.keyboard.type("pip install flask gunicorn")
    page.keyboard.press("Enter")
    time.sleep(15)

    page.screenshot(path="C:\\Users\\Administrator\\Desktop\\pa_deploy.png")
    browser.close()
    print("Done!")