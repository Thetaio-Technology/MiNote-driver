from pathlib import Path
import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


PROJECT_ROOT = Path(__file__).resolve().parent
CHROMEDRIVER_EXE = PROJECT_ROOT / "bin" / "chromedriver.exe"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROME_USER_DATA_DIR = PROJECT_ROOT / "chrome_profile"
TARGET_URL = "https://i.mi.com/note/#/"


def build_driver() -> webdriver.Chrome:
    service = Service(str(CHROMEDRIVER_EXE))
    options = Options()
    options.binary_location = str(CHROME_EXE)
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--headless=new")
    return webdriver.Chrome(service=service, options=options)


def click_sidebar_item(driver: webdriver.Chrome, label: str) -> None:
    script = """
    const label = arguments[0];
    const items = Array.from(document.querySelectorAll('#folderList [role="button"]'));
    const item = items.find((el) => (el.innerText || '').trim() === label);
    if (!item) return false;
    item.click();
    return true;
    """
    if not driver.execute_script(script, label):
        raise RuntimeError(f"Sidebar item not found: {label}")


def inspect(driver: webdriver.Chrome) -> dict:
    return driver.execute_script(
        r"""
        const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
        const container = document.querySelector('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn');
        const items = container
          ? Array.from(container.querySelectorAll('[role="button"], div'))
              .map((el) => ({
                tag: el.tagName,
                className: typeof el.className === 'string' ? el.className : '',
                role: el.getAttribute('role') || '',
                text: clean(el.innerText || '').slice(0, 300),
                html: (el.outerHTML || '').slice(0, 500),
              }))
              .filter((item) => item.text)
              .slice(0, 120)
          : [];

        return {
          title: document.title,
          url: location.href,
          containerClass: container ? container.className : '',
          containerText: container ? clean(container.innerText || '').slice(0, 2000) : '',
          items,
        };
        """
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return !!document.querySelector('#folderList')")
        )
        time.sleep(2)
        click_sidebar_item(driver, "未完成")
        time.sleep(1)
        print(json.dumps(inspect(driver), ensure_ascii=False, indent=2))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
