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
    script = r"""
    const label = arguments[0];
    const items = Array.from(document.querySelectorAll('[role="button"]'))
      .filter((el) => el.closest('#folderList') || el.querySelector('.text-10cyJ'));
    const item = items.find((el) => {
      const text = (el.innerText || '').trim();
      const title = (el.querySelector('.text-10cyJ')?.getAttribute('title') || '').trim();
      return text === label || title === label;
    });
    if (!item) return false;
    item.click();
    return true;
    """
    if not driver.execute_script(script, label):
        raise RuntimeError(f"Sidebar item not found: {label}")


def inspect_first_todo(driver: webdriver.Chrome, section: str) -> dict:
    click_sidebar_item(driver, section)
    time.sleep(1)
    return driver.execute_script(
        r"""
        const first = document.querySelector('.main-group-3qygk.todo-page-2xEZZ.item-list-2UYnn .item-3HTE8');
        if (!first) return {};
        const buttons = Array.from(first.querySelectorAll('button, [role="button"]')).map((el) => ({
          text: (el.innerText || '').trim(),
          title: (el.getAttribute('title') || '').trim(),
          aria: (el.getAttribute('aria-label') || '').trim(),
          dataName: (el.getAttribute('data-name') || '').trim(),
          className: typeof el.className === 'string' ? el.className : '',
          html: (el.outerHTML || '').slice(0, 400),
        }));
        return {
          html: (first.outerHTML || '').slice(0, 3000),
          buttons,
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
        result = {
            "pending": inspect_first_todo(driver, "未完成"),
            "completed": inspect_first_todo(driver, "已完成"),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
